// src/pages/Logistics.jsx
import { useEffect, useState } from 'react';
import { RefreshCw, MapPin, Truck } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../services/api';

const BRAND = { blue:'#1D60AE', green:'#276749', navy:'#0D2137' };

export default function Logistics() {
  const [zones, setZones]       = useState([]);
  const [hubs, setHubs]         = useState([]);
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [tab, setTab]           = useState('zones');

  const load = async () => {
    setLoading(true);
    try {
      const [z, h, s] = await Promise.allSettled([
        api.get('/api/v1/logistics/zones'),
        api.get('/api/v1/logistics/hubs'),
        api.get('/api/v1/logistics/shipments'),
      ]);
      if (z.status==='fulfilled') setZones(z.value.data?.zones || z.value.data || []);
      if (h.status==='fulfilled') setHubs(h.value.data?.hubs || h.value.data || []);
      if (s.status==='fulfilled') setShipments(s.value.data?.shipments || s.value.data || []);
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const Tab = ({ id, label }) => (
    <button onClick={() => setTab(id)} style={{
      padding:'8px 18px', borderRadius:6, border:'none', cursor:'pointer', fontSize:13, fontWeight: tab===id ? 600 : 400,
      background: tab===id ? BRAND.blue : 'transparent', color: tab===id ? 'white' : '#718096',
    }}>{label}</button>
  );

  const statusColor = (s) => ({ active:'#276749', coming_soon:'#744210', not_served:'#742A2A' })[s] || '#718096';

  return (
    <Layout title="Logistics" subtitle="Delivery zones, fulfillment hubs and shipments">
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16, marginBottom:24 }}>
        {[
          ['Delivery Zones', zones.length,    BRAND.blue],
          ['Fulfillment Hubs', hubs.length,   BRAND.green],
          ['Active Shipments', shipments.filter(s=>s.status==='in_transit').length, BRAND.navy],
        ].map(([label, value, color]) => (
          <div key={label} style={{ background:'white', borderRadius:8, padding:18, border:'1px solid #e2e8f0' }}>
            <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:1 }}>{label}</div>
            <div style={{ fontSize:26, fontWeight:700, color, marginTop:4 }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ background:'white', borderRadius:8, padding:6, border:'1px solid #e2e8f0', marginBottom:16, display:'inline-flex', gap:4 }}>
        <Tab id="zones" label="Delivery Zones" />
        <Tab id="hubs"  label="Fulfillment Hubs" />
        <Tab id="shipments" label="Shipments" />
      </div>

      <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
        {loading ? (
          <div style={{ padding:40, textAlign:'center', color:'#718096' }}>Loading logistics...</div>
        ) : tab === 'zones' ? (
          <table style={{ width:'100%', borderCollapse:'collapse' }}>
            <thead style={{ background:'#F7FAFC' }}>
              <tr>
                {['Zone','Coverage','Min Order','Delivery Days','Same Day','Status'].map(h => (
                  <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {zones.map(z => (
                <tr key={z.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                  <td style={{ padding:'12px 14px', fontWeight:600, color:BRAND.navy }}>{z.zone_name}</td>
                  <td style={{ padding:'12px 14px', fontSize:12, color:'#4a5568' }}>{z.counties}</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{z.min_order_kg}kg</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{z.estimated_delivery_days} day(s)</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{z.same_day_available ? '✓' : '—'}</td>
                  <td style={{ padding:'12px 14px' }}>
                    <span style={{ color: statusColor(z.status), fontWeight:600, fontSize:12, textTransform:'uppercase' }}>{z.status?.replace('_',' ')}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : tab === 'hubs' ? (
          <table style={{ width:'100%', borderCollapse:'collapse' }}>
            <thead style={{ background:'#F7FAFC' }}>
              <tr>
                {['Hub','Code','Type','Location','Cold Storage','Capacity','Zones'].map(h => (
                  <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {hubs.map(h => (
                <tr key={h.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                  <td style={{ padding:'12px 14px', fontWeight:600, color:BRAND.navy }}>{h.hub_name}</td>
                  <td style={{ padding:'12px 14px', fontSize:12, fontFamily:'monospace' }}>{h.hub_code}</td>
                  <td style={{ padding:'12px 14px', fontSize:12, textTransform:'capitalize' }}>{h.hub_type?.replace('_',' ')}</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{h.town}, {h.county}</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{h.has_cold_storage ? '✓' : '—'}</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{h.cold_storage_capacity_kg ? `${h.cold_storage_capacity_kg.toLocaleString()}kg` : '—'}</td>
                  <td style={{ padding:'12px 14px', fontSize:12, color:'#4a5568' }}>{h.serves_zones}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          shipments.length === 0 ? (
            <div style={{ padding:40, textAlign:'center', color:'#718096' }}>No shipments yet.</div>
          ) : (
            <table style={{ width:'100%', borderCollapse:'collapse' }}>
              <thead style={{ background:'#F7FAFC' }}>
                <tr>
                  {['Reference','Order','Driver','Vehicle','Status','Estimated Delivery'].map(h => (
                    <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {shipments.map(s => (
                  <tr key={s.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'12px 14px', fontSize:12, fontFamily:'monospace', color:'#4a5568' }}>{s.shipment_reference}</td>
                    <td style={{ padding:'12px 14px', fontSize:12 }}>{s.order_id}</td>
                    <td style={{ padding:'12px 14px', fontSize:13 }}>{s.driver_name || '—'}</td>
                    <td style={{ padding:'12px 14px', fontSize:13 }}>{s.vehicle_reg || '—'}</td>
                    <td style={{ padding:'12px 14px' }}>
                      <span style={{ background:'#BEE3F8', color:'#2C5282', padding:'2px 8px', borderRadius:20, fontSize:11, fontWeight:600, textTransform:'uppercase' }}>{s.status}</span>
                    </td>
                    <td style={{ padding:'12px 14px', fontSize:12, color:'#718096' }}>
                      {s.estimated_delivery_at ? new Date(s.estimated_delivery_at).toLocaleDateString('en-KE') : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}
      </div>
    </Layout>
  );
}