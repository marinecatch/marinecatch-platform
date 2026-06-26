// src/pages/Settlement.jsx
import { useEffect, useState } from 'react';
import { RefreshCw, TrendingUp, Clock, CheckCircle } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../services/api';

const BRAND = { blue:'#1D60AE', green:'#276749', navy:'#0D2137', cyan:'#00B3F0' };

export default function Settlement() {
  const [capital, setCapital]     = useState(null);
  const [receivables, setReceivables] = useState([]);
  const [pending, setPending]     = useState([]);
  const [loading, setLoading]     = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [c, r, p] = await Promise.allSettled([
        api.get('/api/v1/settlement/working-capital'),
        api.get('/api/v1/settlement/receivables'),
        api.get('/api/v1/settlement/supplier-payments/pending'),
      ]);
      if (c.status === 'fulfilled') setCapital(c.value.data);
      if (r.status === 'fulfilled') setReceivables(r.value.data?.receivables || r.value.data || []);
      if (p.status === 'fulfilled') setPending(p.value.data?.payments || p.value.data || []);
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  return (
    <Layout title="Settlement" subtitle="Receivables and supplier payment management">
      {loading ? (
        <div style={{ padding:40, textAlign:'center', color:'#718096' }}>Loading settlement data...</div>
      ) : (
        <>
          {/* Working Capital Summary */}
          {capital && (
            <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16, marginBottom:24 }}>
              {[
                ['Total Receivables', `KES ${(capital.total_receivables || 0).toLocaleString()}`, TrendingUp, BRAND.blue],
                ['Pending Payouts',   `KES ${(capital.pending_payouts || 0).toLocaleString()}`,   Clock,       '#C05621'],
                ['Net Position',      `KES ${(capital.net_position || 0).toLocaleString()}`,      CheckCircle, BRAND.green],
              ].map(([label, value, Icon, color]) => (
                <div key={label} style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', display:'flex', gap:14, alignItems:'center' }}>
                  <div style={{ width:44, height:44, background:`${color}15`, borderRadius:10, display:'flex', alignItems:'center', justifyContent:'center' }}>
                    <Icon size={20} color={color} />
                  </div>
                  <div>
                    <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5 }}>{label}</div>
                    <div style={{ fontSize:22, fontWeight:700, color, marginTop:2 }}>{value}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
            {/* Receivables */}
            <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
              <div style={{ padding:'16px 20px', borderBottom:'1px solid #e2e8f0', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <div style={{ fontWeight:600, color:BRAND.navy }}>Outstanding Receivables</div>
                <button onClick={load} style={{ border:'none', background:'none', cursor:'pointer', color:'#718096' }}>
                  <RefreshCw size={14} />
                </button>
              </div>
              {receivables.length === 0 ? (
                <div style={{ padding:24, textAlign:'center', color:'#718096', fontSize:13 }}>No outstanding receivables</div>
              ) : (
                <table style={{ width:'100%', borderCollapse:'collapse' }}>
                  <thead>
                    <tr style={{ background:'#F7FAFC' }}>
                      {['Order','Buyer','Amount','Due'].map(h => (
                        <th key={h} style={{ padding:'8px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {receivables.map((r, i) => (
                      <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}>
                        <td style={{ padding:'10px 14px', fontSize:12, fontFamily:'monospace', color:'#4a5568' }}>{r.order_number || r.order_id}</td>
                        <td style={{ padding:'10px 14px', fontSize:13 }}>{r.buyer_name || r.buyer_id}</td>
                        <td style={{ padding:'10px 14px', fontWeight:600, color:BRAND.blue }}>KES {(r.amount_kes || 0).toLocaleString()}</td>
                        <td style={{ padding:'10px 14px', fontSize:12, color: r.overdue ? '#C53030' : '#718096' }}>
                          {r.due_date ? new Date(r.due_date).toLocaleDateString('en-KE') : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Pending Supplier Payments */}
            <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
              <div style={{ padding:'16px 20px', borderBottom:'1px solid #e2e8f0' }}>
                <div style={{ fontWeight:600, color:BRAND.navy }}>Pending Supplier Payments</div>
              </div>
              {pending.length === 0 ? (
                <div style={{ padding:24, textAlign:'center', color:'#718096', fontSize:13 }}>No pending supplier payments</div>
              ) : (
                <table style={{ width:'100%', borderCollapse:'collapse' }}>
                  <thead>
                    <tr style={{ background:'#F7FAFC' }}>
                      {['Supplier','Species','Amount','Action'].map(h => (
                        <th key={h} style={{ padding:'8px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {pending.map((p, i) => (
                      <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}>
                        <td style={{ padding:'10px 14px', fontSize:13 }}>{p.supplier_name || p.fisher_name}</td>
                        <td style={{ padding:'10px 14px', fontSize:13, textTransform:'capitalize' }}>{p.species}</td>
                        <td style={{ padding:'10px 14px', fontWeight:600, color:BRAND.green }}>KES {(p.amount_kes || 0).toLocaleString()}</td>
                        <td style={{ padding:'10px 14px' }}>
                          <button style={{ padding:'4px 10px', background:BRAND.green, color:'white', border:'none', borderRadius:6, cursor:'pointer', fontSize:12, fontWeight:500 }}>
                            Pay Now
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}