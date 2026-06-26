// src/pages/Inventory.jsx
import { useEffect, useState } from 'react';
import { Search, Plus, RefreshCw, Tag } from 'lucide-react';
import Layout from '../components/Layout';
import { getInventory, updateLot } from '../services/api';

const BRAND = { blue:'#1D60AE', green:'#276749', navy:'#0D2137', cyan:'#00B3F0' };

const badge = (status) => {
  const map = {
    available:     { bg:'#C6F6D5', color:'#276749' },
    reserved:      { bg:'#FEFCBF', color:'#744210' },
    partially_sold:{ bg:'#BEE3F8', color:'#2C5282' },
    sold:          { bg:'#FED7D7', color:'#742A2A' },
    expired:       { bg:'#E2E8F0', color:'#4A5568' },
  };
  const s = map[status] || map.available;
  return <span style={{ ...s, padding:'2px 10px', borderRadius:20, fontSize:11, fontWeight:600, textTransform:'uppercase' }}>{status?.replace('_',' ')}</span>;
};

export default function Inventory() {
  const [lots, setLots]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [species, setSpecies]   = useState('');
  const [modal, setModal]       = useState(null); // { lot }
  const [price, setPrice]       = useState('');
  const [weight, setWeight]     = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const params = {};
      if (species) params.species = species;
      const res = await getInventory(params);
      setLots(res.data.lots || []);
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [species]);

  const openSetPrice = (lot) => {
    setModal(lot);
    setPrice(lot.selling_price_per_kg || '');
    setWeight(lot.weight_kg || lot.available_kg || '');
  };

  const savePrice = async () => {
    if (!modal) return;
    const payload = {};
    if (price)  payload.selling_price_per_kg = parseFloat(price);
    if (weight) payload.weight_kg = parseFloat(weight);
    try {
      await updateLot(modal.id, payload);
      setModal(null);
      load();
    } catch(e) { alert('Failed to update'); }
  };

  const totalKg  = lots.reduce((s, l) => s + (l.available_kg || 0), 0);
  const totalVal = lots.reduce((s, l) => s + ((l.available_kg || 0) * (l.selling_price_per_kg || 0)), 0);
  const unpriced = lots.filter(l => !l.selling_price_per_kg || l.selling_price_per_kg === 0).length;

  return (
    <Layout title="Inventory" subtitle="All seafood lots — available, reserved, sold">

      {/* Stats */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:16, marginBottom:24 }}>
        {[
          ['Total Lots', lots.length, BRAND.blue],
          ['Available (kg)', `${totalKg.toLocaleString()}kg`, BRAND.green],
          ['Inventory Value', `KES ${Math.round(totalVal).toLocaleString()}`, BRAND.navy],
          ['Unpriced', unpriced, '#C05621'],
        ].map(([label, value, color]) => (
          <div key={label} style={{ background:'white', borderRadius:8, padding:18, border:'1px solid #e2e8f0' }}>
            <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:1 }}>{label}</div>
            <div style={{ fontSize:26, fontWeight:700, color, marginTop:4 }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ background:'white', borderRadius:8, padding:16, border:'1px solid #e2e8f0', marginBottom:16, display:'flex', gap:12, alignItems:'center' }}>
        <Search size={16} color="#a0aec0" />
        <select value={species} onChange={e => setSpecies(e.target.value)}
          style={{ border:'1px solid #e2e8f0', borderRadius:6, padding:'7px 12px', fontSize:14, color:'#4a5568' }}>
          <option value="">All Species</option>
          {['tuna','octopus','prawns','lobster','snapper','kingfish','sardines','crab'].map(s => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>
          ))}
        </select>
        <button onClick={load} style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:6, padding:'7px 14px', background:'white', border:'1px solid #e2e8f0', borderRadius:6, cursor:'pointer', fontSize:13, color:'#4a5568' }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Table */}
      <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
        {loading ? (
          <div style={{ padding:40, textAlign:'center', color:'#718096' }}>Loading inventory...</div>
        ) : (
          <table style={{ width:'100%', borderCollapse:'collapse' }}>
            <thead style={{ background:'#F7FAFC' }}>
              <tr>
                {['Lot Number','Species','Weight','Available','Price/kg','Location','Fisher','Status','Action'].map(h => (
                  <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {lots.map(lot => (
                <tr key={lot.id} style={{ borderBottom:'1px solid #f7fafc' }}
                  onMouseEnter={e => e.currentTarget.style.background='#FAFBFC'}
                  onMouseLeave={e => e.currentTarget.style.background='white'}>
                  <td style={{ padding:'12px 14px', fontSize:12, color:'#4a5568', fontFamily:'monospace' }}>{lot.lot_number}</td>
                  <td style={{ padding:'12px 14px', fontWeight:600, color:BRAND.navy, textTransform:'capitalize' }}>{lot.species}</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{lot.weight_kg || lot.available_kg}kg</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{lot.available_kg}kg</td>
                  <td style={{ padding:'12px 14px', fontWeight:600, color: lot.selling_price_per_kg ? BRAND.green : '#C05621' }}>
                    {lot.selling_price_per_kg ? `KES ${lot.selling_price_per_kg.toLocaleString()}` : 'Unpriced'}
                  </td>
                  <td style={{ padding:'12px 14px', fontSize:13, textTransform:'capitalize' }}>{lot.landing_site}</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{lot.source_name}</td>
                  <td style={{ padding:'12px 14px' }}>{badge(lot.lot_status || 'available')}</td>
                  <td style={{ padding:'12px 14px' }}>
                    <button onClick={() => openSetPrice(lot)} style={{
                      display:'flex', alignItems:'center', gap:5, padding:'5px 10px',
                      background:'white', border:`1px solid ${BRAND.blue}`, borderRadius:6,
                      color:BRAND.blue, cursor:'pointer', fontSize:12, fontWeight:500,
                    }}>
                      <Tag size={12} /> Set Price
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Set Price Modal */}
      {modal && (
        <div style={{ position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000 }}>
          <div style={{ background:'white', borderRadius:10, padding:28, width:420, boxShadow:'0 20px 60px rgba(0,0,0,0.15)' }}>
            <div style={{ fontSize:17, fontWeight:700, color:BRAND.navy, marginBottom:4 }}>Update Lot</div>
            <div style={{ fontSize:13, color:'#718096', marginBottom:20 }}>{modal.lot_number} — {modal.species}</div>
            <div style={{ marginBottom:14 }}>
              <label style={{ fontSize:12, fontWeight:600, color:'#4a5568', display:'block', marginBottom:6, textTransform:'uppercase', letterSpacing:0.5 }}>Weight (kg)</label>
              <input type="number" value={weight} onChange={e => setWeight(e.target.value)}
                style={{ width:'100%', padding:'9px 12px', border:'1px solid #e2e8f0', borderRadius:6, fontSize:14, boxSizing:'border-box' }}
                placeholder="e.g. 50" />
            </div>
            <div style={{ marginBottom:20 }}>
              <label style={{ fontSize:12, fontWeight:600, color:'#4a5568', display:'block', marginBottom:6, textTransform:'uppercase', letterSpacing:0.5 }}>Price per kg (KES)</label>
              <input type="number" value={price} onChange={e => setPrice(e.target.value)}
                style={{ width:'100%', padding:'9px 12px', border:'1px solid #e2e8f0', borderRadius:6, fontSize:14, boxSizing:'border-box' }}
                placeholder="e.g. 780" />
            </div>
            <div style={{ display:'flex', gap:10, justifyContent:'flex-end' }}>
              <button onClick={() => setModal(null)} style={{ padding:'8px 16px', background:'white', border:'1px solid #e2e8f0', borderRadius:6, cursor:'pointer', fontSize:13 }}>Cancel</button>
              <button onClick={savePrice} style={{ padding:'8px 16px', background:BRAND.blue, color:'white', border:'none', borderRadius:6, cursor:'pointer', fontSize:13, fontWeight:600 }}>Save</button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}