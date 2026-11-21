// src/pages/LPO.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getLpos, getLpo } from '../services/api';

export default function LPO() {
  const [orders, setOrders]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState('');
  const [detail, setDetail]   = useState(null);
  const [detailErr, setDetailErr] = useState(null);

  useEffect(() => {
    getLpos().then(r => setOrders(Array.isArray(r.data) ? r.data : (r.data.orders || []))).catch(console.error).finally(() => setLoading(false));
  }, []);

  const lookup = async () => {
    if (!search.trim()) return;
    setDetailErr(null);
    setDetail(null);
    try {
      const r = await getLpo(search.trim());
      setDetail(r.data);
    } catch (e) {
      setDetailErr(e.response?.data?.detail || 'LPO reference not found.');
    }
  };

  return (
    <Layout title="LPO Orders" subtitle="Institutional buyer Local Purchase Orders">
      <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', marginBottom:20 }}>
        <div style={{ fontWeight:600, marginBottom:12, color:'#1a365d' }}>Find Order by LPO Reference</div>
        <div style={{ display:'flex', gap:8 }}>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && lookup()}
            placeholder="e.g. LPO-2026-0042"
            style={{ flex:1, padding:'8px 12px', borderRadius:6, border:'1px solid #e2e8f0', fontSize:13 }}
          />
          <button onClick={lookup} style={{ padding:'8px 20px', borderRadius:6, border:'none', background:'#1D60AE', color:'white', fontWeight:600, cursor:'pointer', fontSize:13 }}>
            Search
          </button>
        </div>
        {detailErr && <div style={{ marginTop:12, color:'#9b2c2c', fontSize:13 }}>{detailErr}</div>}
        {detail && (
          <div style={{ marginTop:16, padding:16, background:'#f7fafc', borderRadius:6, fontSize:13, display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:12 }}>
            <div><b>Order ID</b><div>{detail.order_id}</div></div>
            <div><b>LPO Ref</b><div>{detail.lpo_reference}</div></div>
            <div><b>Species</b><div>{detail.species}</div></div>
            <div><b>Quantity</b><div>{detail.quantity_kg}kg</div></div>
            <div><b>Total</b><div>KES {(detail.total_kes || 0).toLocaleString()}</div></div>
            <div><b>Payment Terms</b><div>{detail.payment_terms_days} days</div></div>
            <div><b>Status</b><div>{detail.status}</div></div>
            <div><b>Delivery Address</b><div>{detail.delivery_address || '—'}</div></div>
            <div><b>Created</b><div>{detail.created_at ? new Date(detail.created_at).toLocaleString() : '—'}</div></div>
          </div>
        )}
      </div>

      <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
        <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>All LPO Orders</div>
        {loading ? (
          <div style={{ textAlign:'center', padding:24, color:'#718096' }}>Loading...</div>
        ) : (
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
            <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
              {['LPO Ref', 'Buyer', 'Species', 'Quantity', 'Total', 'Terms', 'Status', 'Date'].map(h => (
                <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.order_id} style={{ borderBottom:'1px solid #f7fafc' }}>
                  <td style={{ padding:'8px 12px', fontWeight:500 }}>{o.lpo_reference}</td>
                  <td style={{ padding:'8px 12px' }}>{o.buyer_name || '—'}</td>
                  <td style={{ padding:'8px 12px' }}>{o.species}</td>
                  <td style={{ padding:'8px 12px' }}>{o.quantity_kg}kg</td>
                  <td style={{ padding:'8px 12px', fontWeight:500 }}>KES {(o.total_kes || 0).toLocaleString()}</td>
                  <td style={{ padding:'8px 12px' }}>{o.payment_terms_days}d</td>
                  <td style={{ padding:'8px 12px' }}>
                    <span style={{ background:'#bee3f8', padding:'2px 8px', borderRadius:20, fontSize:11 }}>{o.status}</span>
                  </td>
                  <td style={{ padding:'8px 12px', color:'#718096' }}>{o.created_at ? new Date(o.created_at).toLocaleDateString() : '—'}</td>
                </tr>
              ))}
              {orders.length === 0 && <tr><td colSpan={8} style={{ padding:12, color:'#a0aec0' }}>No LPO orders yet.</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
}
