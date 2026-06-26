// src/pages/Payouts.jsx
import { useEffect, useState } from 'react';
import { RefreshCw, Send } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../services/api';

const BRAND = { blue:'#1D60AE', green:'#276749', navy:'#0D2137' };

export default function Payouts() {
  const [payouts, setPayouts] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/v1/payouts/');
      setPayouts(Array.isArray(res.data) ? res.data : res.data?.payouts || []);
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const totalPaid    = payouts.filter(p => p.payout_status === 'paid').reduce((s,p) => s+(p.supplier_amount||0),0);
  const totalPending = payouts.filter(p => p.payout_status === 'pending').reduce((s,p) => s+(p.supplier_amount||0),0);

  return (
    <Layout title="Fisher Payouts" subtitle="Supplier and fisher payment management">
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16, marginBottom:24 }}>
        {[
          ['Total Payouts',   payouts.length,                                    BRAND.navy],
          ['Paid Out',        `KES ${Math.round(totalPaid).toLocaleString()}`,    BRAND.green],
          ['Pending Payout',  `KES ${Math.round(totalPending).toLocaleString()}`, '#C05621'],
        ].map(([label, value, color]) => (
          <div key={label} style={{ background:'white', borderRadius:8, padding:18, border:'1px solid #e2e8f0' }}>
            <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:1 }}>{label}</div>
            <div style={{ fontSize:26, fontWeight:700, color, marginTop:4 }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
        <div style={{ padding:'14px 20px', borderBottom:'1px solid #e2e8f0', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <div style={{ fontWeight:600, color:BRAND.navy }}>Fisher Payout Records</div>
          <button onClick={load} style={{ display:'flex', alignItems:'center', gap:6, padding:'6px 12px', background:'white', border:'1px solid #e2e8f0', borderRadius:6, cursor:'pointer', fontSize:13, color:'#4a5568' }}>
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
        {loading ? (
          <div style={{ padding:40, textAlign:'center', color:'#718096' }}>Loading payouts...</div>
        ) : payouts.length === 0 ? (
          <div style={{ padding:40, textAlign:'center', color:'#718096' }}>No payout records yet. Payouts are triggered after order delivery.</div>
        ) : (
          <table style={{ width:'100%', borderCollapse:'collapse' }}>
            <thead style={{ background:'#F7FAFC' }}>
              <tr>
                {['Reference','Order','Fisher Amount','MC Amount','Payout Status','Receipt','Date'].map(h => (
                  <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {payouts.map(p => (
                <tr key={p.id} style={{ borderBottom:'1px solid #f7fafc' }}
                  onMouseEnter={e => e.currentTarget.style.background='#FAFBFC'}
                  onMouseLeave={e => e.currentTarget.style.background='white'}>
                  <td style={{ padding:'11px 14px', fontSize:12, fontFamily:'monospace', color:'#4a5568' }}>{p.transaction_reference}</td>
                  <td style={{ padding:'11px 14px', fontSize:12 }}>{p.order_id}</td>
                  <td style={{ padding:'11px 14px', fontWeight:600, color:BRAND.green }}>KES {(p.supplier_amount||0).toLocaleString()}</td>
                  <td style={{ padding:'11px 14px', fontWeight:600, color:BRAND.blue }}>KES {(p.marinecatch_amount||0).toLocaleString()}</td>
                  <td style={{ padding:'11px 14px' }}>
                    <span style={{
                      background: p.payout_status==='paid' ? '#C6F6D5' : p.payout_status==='pending' ? '#FEFCBF' : '#FED7D7',
                      color: p.payout_status==='paid' ? '#276749' : p.payout_status==='pending' ? '#744210' : '#742A2A',
                      padding:'2px 10px', borderRadius:20, fontSize:11, fontWeight:600, textTransform:'uppercase'
                    }}>{p.payout_status}</span>
                  </td>
                  <td style={{ padding:'11px 14px', fontSize:12, fontFamily:'monospace', color:'#718096' }}>{p.mpesa_receipt_number || '—'}</td>
                  <td style={{ padding:'11px 14px', fontSize:12, color:'#718096' }}>
                    {p.created_at ? new Date(p.created_at).toLocaleDateString('en-KE') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
}