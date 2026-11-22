// src/pages/Payments.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import { getFisherPayouts } from '../services/api';

function StatCard({ label, value, color = '#0D2137' }) {
  return (
    <div style={{ background:'white', borderRadius:8, padding:'16px 18px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
      <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>{label}</div>
      <div style={{ fontSize:22, fontWeight:700, color }}>{value}</div>
    </div>
  );
}

const STATUS_COLOR = { paid: '#c6f6d5', pending: '#fefcbf', processing: '#bee3f8', failed: '#fed7d7' };

export default function Payments() {
  const { user } = useAuth();
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    if (!user) return;
    getFisherPayouts(user.id).then(r => setData(r.data)).catch(() => setError('Could not load payout summary.')).finally(() => setLoading(false));
  }, [user]);

  return (
    <Layout title="Payments" subtitle="Your earnings, pending payouts & settlement history">
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading payments...</div>
      ) : error ? (
        <div style={{ background:'white', borderRadius:8, padding:24, border:'1px solid #fed7d7', color:'#9b2c2c' }}>{error}</div>
      ) : (
        <>
          <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:20 }}>
            <StatCard label="Total Earned" value={`KES ${data.summary.total_earned_kes.toLocaleString()}`} color="#276749" />
            <StatCard label="Pending" value={`KES ${data.summary.total_pending_kes.toLocaleString()}`} color="#9B2C2C" />
            <StatCard label="Orders" value={data.summary.total_orders} />
            <StatCard label="Consistency Score" value={data.summary.consistency_score != null ? `${data.summary.consistency_score}%` : '—'} />
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', marginBottom:20, fontSize:13 }}>
            <div style={{ fontWeight:600, marginBottom:10, color:'#1a365d' }}>Settlement Account</div>
            <div style={{ color:'#4a5568' }}>
              {data.settlement_account ? (
                <>
                  {data.settlement_type || 'Account'}: <b>{data.settlement_account}</b>{' '}
                  {data.account_verified ? <span style={{ color:'#276749' }}>· Verified</span> : <span style={{ color:'#9b2c2c' }}>· Not verified</span>}
                </>
              ) : (
                <span style={{ color:'#a0aec0' }}>No settlement account on file yet — contact an admin to set one up.</span>
              )}
            </div>
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
            <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Payout History</div>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                {['Reference', 'Species', 'Qty', 'Lot #', 'Amount', 'Status', 'Payout Date'].map(h => (
                  <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {data.payout_history.map((p, i) => (
                  <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'8px 12px', fontWeight:500 }}>{p.transaction_reference}</td>
                    <td style={{ padding:'8px 12px' }}>{p.species || '—'}</td>
                    <td style={{ padding:'8px 12px' }}>{p.quantity_kg ? `${p.quantity_kg}kg` : '—'}</td>
                    <td style={{ padding:'8px 12px' }}>{p.lot_number || '—'}</td>
                    <td style={{ padding:'8px 12px', fontWeight:500, color:'#276749' }}>KES {(p.payout_amount_kes || 0).toLocaleString()}</td>
                    <td style={{ padding:'8px 12px' }}>
                      <span style={{ background: STATUS_COLOR[p.payout_status] || '#e2e8f0', padding:'2px 8px', borderRadius:20, fontSize:11 }}>{p.payout_status}</span>
                    </td>
                    <td style={{ padding:'8px 12px', color:'#718096' }}>{p.payout_date ? new Date(p.payout_date).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
                {data.payout_history.length === 0 && <tr><td colSpan={7} style={{ padding:12, color:'#a0aec0' }}>No payouts yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Layout>
  );
}
