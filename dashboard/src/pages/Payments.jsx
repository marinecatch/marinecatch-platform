// src/pages/Payments.jsx
import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../services/api';

const BRAND = { blue:'#1D60AE', green:'#276749', navy:'#0D2137' };

const statusBadge = (status) => {
  const map = {
    paid:       { bg:'#C6F6D5', color:'#276749' },
    pending:    { bg:'#FEFCBF', color:'#744210' },
    processing: { bg:'#BEE3F8', color:'#2C5282' },
    failed:     { bg:'#FED7D7', color:'#742A2A' },
    refunded:   { bg:'#E9D8FD', color:'#553C9A' },
  };
  const s = map[status] || { bg:'#E2E8F0', color:'#4A5568' };
  return <span style={{ ...s, padding:'2px 10px', borderRadius:20, fontSize:11, fontWeight:600, textTransform:'uppercase' }}>{status}</span>;
};

export default function Payments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading]   = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/v1/payments/');
      setPayments(Array.isArray(res.data) ? res.data : res.data?.payments || []);
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const totalPaid    = payments.filter(p => p.payment_status === 'paid').reduce((s,p) => s + (p.total_amount||0), 0);
  const totalPending = payments.filter(p => p.payment_status === 'pending'||p.payment_status==='processing').length;

  return (
    <Layout title="Payments" subtitle="All M-Pesa and payment transactions">
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16, marginBottom:24 }}>
        {[
          ['Total Transactions', payments.length,  BRAND.navy],
          ['Total Received',     `KES ${Math.round(totalPaid).toLocaleString()}`, BRAND.green],
          ['Pending',            totalPending,      '#C05621'],
        ].map(([label, value, color]) => (
          <div key={label} style={{ background:'white', borderRadius:8, padding:18, border:'1px solid #e2e8f0' }}>
            <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:1 }}>{label}</div>
            <div style={{ fontSize:26, fontWeight:700, color, marginTop:4 }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
        <div style={{ padding:'14px 20px', borderBottom:'1px solid #e2e8f0', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <div style={{ fontWeight:600, color:BRAND.navy }}>Payment Transactions</div>
          <button onClick={load} style={{ display:'flex', alignItems:'center', gap:6, padding:'6px 12px', background:'white', border:'1px solid #e2e8f0', borderRadius:6, cursor:'pointer', fontSize:13, color:'#4a5568' }}>
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
        {loading ? (
          <div style={{ padding:40, textAlign:'center', color:'#718096' }}>Loading payments...</div>
        ) : payments.length === 0 ? (
          <div style={{ padding:40, textAlign:'center', color:'#718096' }}>No payment transactions yet.</div>
        ) : (
          <table style={{ width:'100%', borderCollapse:'collapse' }}>
            <thead style={{ background:'#F7FAFC' }}>
              <tr>
                {['Reference','Order','Amount','Channel','Status','Payout','Date'].map(h => (
                  <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {payments.map(p => (
                <tr key={p.id} style={{ borderBottom:'1px solid #f7fafc' }}
                  onMouseEnter={e => e.currentTarget.style.background='#FAFBFC'}
                  onMouseLeave={e => e.currentTarget.style.background='white'}>
                  <td style={{ padding:'11px 14px', fontSize:12, fontFamily:'monospace', color:'#4a5568' }}>{p.transaction_reference}</td>
                  <td style={{ padding:'11px 14px', fontSize:12, color:'#4a5568' }}>{p.order_id}</td>
                  <td style={{ padding:'11px 14px', fontWeight:600, color:BRAND.green }}>KES {(p.total_amount||0).toLocaleString()}</td>
                  <td style={{ padding:'11px 14px', fontSize:12, textTransform:'uppercase', color:'#718096' }}>{p.payment_method}</td>
                  <td style={{ padding:'11px 14px' }}>{statusBadge(p.payment_status)}</td>
                  <td style={{ padding:'11px 14px' }}>{statusBadge(p.payout_status)}</td>
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