// src/pages/MyCatch.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getMyLots } from '../services/api';

function StatCard({ label, value, color = '#0D2137' }) {
  return (
    <div style={{ background:'white', borderRadius:8, padding:'16px 18px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
      <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>{label}</div>
      <div style={{ fontSize:22, fontWeight:700, color }}>{value}</div>
    </div>
  );
}

const STATUS_COLOR = {
  available: '#c6f6d5', reserved: '#fefcbf', sold: '#e2e8f0', expired: '#fed7d7', pending: '#bee3f8',
};

export default function MyCatch() {
  const [data, setData]       = useState(null);
  const [includeSold, setIncludeSold] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getMyLots(includeSold).then(r => setData(r.data)).catch(console.error).finally(() => setLoading(false));
  }, [includeSold]);

  return (
    <Layout title="My Catch" subtitle="Lots you've listed on the marketplace">
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading your lots...</div>
      ) : (
        <>
          <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:20 }}>
            <StatCard label="Total Lots" value={data.total_lots} />
            <StatCard label="Available (kg)" value={`${data.total_available_kg}kg`} />
            <StatCard label="Value Available" value={`KES ${data.total_value_kes.toLocaleString()}`} color="#276749" />
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
              <div style={{ fontWeight:600, color:'#1a365d' }}>Your Lots</div>
              <label style={{ fontSize:13, color:'#718096', display:'flex', alignItems:'center', gap:6 }}>
                <input type="checkbox" checked={includeSold} onChange={e => setIncludeSold(e.target.checked)} />
                Include sold lots
              </label>
            </div>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                {['Lot #', 'Species', 'Weight', 'Available', 'Price/kg', 'Status', 'Catch Date', 'Est. Expiry'].map(h => (
                  <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {data.lots.map(l => (
                  <tr key={l.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'8px 12px', fontWeight:500 }}>{l.lot_number}</td>
                    <td style={{ padding:'8px 12px' }}>{l.species}</td>
                    <td style={{ padding:'8px 12px' }}>{l.weight_kg}kg</td>
                    <td style={{ padding:'8px 12px' }}>{l.available_kg}kg</td>
                    <td style={{ padding:'8px 12px' }}>KES {l.selling_price_per_kg}</td>
                    <td style={{ padding:'8px 12px' }}>
                      <span style={{ background: STATUS_COLOR[l.lot_status] || '#e2e8f0', padding:'2px 8px', borderRadius:20, fontSize:11 }}>{l.lot_status}</span>
                    </td>
                    <td style={{ padding:'8px 12px', color:'#718096' }}>{l.catch_date ? new Date(l.catch_date).toLocaleDateString() : '—'}</td>
                    <td style={{ padding:'8px 12px', color:'#718096' }}>{l.estimated_expiry ? new Date(l.estimated_expiry).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
                {data.lots.length === 0 && <tr><td colSpan={8} style={{ padding:12, color:'#a0aec0' }}>No lots listed yet — use "Log Catch" to add your first one.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Layout>
  );
}
