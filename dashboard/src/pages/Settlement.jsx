// src/pages/Settlement.jsx
import { useEffect, useState } from 'react';
import { RefreshCw, TrendingUp, TrendingDown, DollarSign, Clock } from 'lucide-react';
import Layout from '../components/Layout';
import api from '../services/api';

const BRAND = { blue:'#1D60AE', green:'#276749', navy:'#0D2137', cyan:'#00B3F0' };

const StatCard = ({ label, value, icon: Icon, color, sub }) => (
  <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', display:'flex', gap:14, alignItems:'center' }}>
    <div style={{ width:44, height:44, background:`${color}18`, borderRadius:10, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
      <Icon size={20} color={color} />
    </div>
    <div>
      <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, marginBottom:2 }}>{label}</div>
      <div style={{ fontSize:22, fontWeight:700, color }}>{value}</div>
      {sub && <div style={{ fontSize:11, color:'#a0aec0', marginTop:2 }}>{sub}</div>}
    </div>
  </div>
);

export default function Settlement() {
  const [data, setData]           = useState(null);
  const [receivables, setReceivables] = useState([]);
  const [pending, setPending]     = useState([]);
  const [loading, setLoading]     = useState(true);
  const [tab, setTab]             = useState('overview');

  const load = async () => {
    setLoading(true);
    try {
      const [c, r, p] = await Promise.allSettled([
        api.get('/api/v1/settlement/working-capital'),
        api.get('/api/v1/settlement/receivables'),
        api.get('/api/v1/settlement/supplier-payments/pending'),
      ]);
      if (c.status === 'fulfilled') setData(c.value.data);
      if (r.status === 'fulfilled') setReceivables(r.value.data?.receivables || r.value.data || []);
      if (p.status === 'fulfilled') setPending(p.value.data?.payments || p.value.data || []);
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const fmt = (n) => `KES ${(n || 0).toLocaleString()}`;
  const rec = data?.receivables || {};
  const pay = data?.payables || {};
  const wc  = data?.working_capital;

  const Tab = ({ id, label }) => (
    <button onClick={() => setTab(id)} style={{
      padding:'8px 18px', borderRadius:6, border:'none', cursor:'pointer',
      fontSize:13, fontWeight: tab===id ? 600 : 400,
      background: tab===id ? BRAND.blue : 'transparent',
      color: tab===id ? 'white' : '#718096',
    }}>{label}</button>
  );

  return (
    <Layout title="Settlement" subtitle="Receivables, payables and working capital">
      {loading ? (
        <div style={{ padding:40, textAlign:'center', color:'#718096' }}>Loading settlement data...</div>
      ) : (
        <>
          {/* KPI Cards */}
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16, marginBottom:24 }}>
            <StatCard label="Outstanding Receivables" value={fmt(rec.outstanding_kes)} icon={TrendingUp}   color={BRAND.blue}  sub={`Invoiced: ${fmt(rec.total_invoiced_kes)}`} />
            <StatCard label="Collected"               value={fmt(rec.total_collected_kes)} icon={DollarSign} color={BRAND.green} />
            <StatCard label="Overdue"                 value={fmt(rec.overdue_kes)}      icon={Clock}        color="#C05621"     />
            <StatCard label="Pending Payables"        value={fmt(pay.outstanding_kes)}  icon={TrendingDown} color={BRAND.navy}  sub={`Paid: ${fmt(pay.total_paid_suppliers)}`} />
          </div>

          {/* Working Capital */}
          {wc && (
            <div style={{ background: BRAND.navy, borderRadius:8, padding:20, marginBottom:24, color:'white', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <div>
                <div style={{ fontSize:12, opacity:0.6, textTransform:'uppercase', letterSpacing:1 }}>Net Working Capital Position</div>
                <div style={{ fontSize:32, fontWeight:700, marginTop:4, color: wc >= 0 ? '#68D391' : '#FC8181' }}>
                  KES {(wc || 0).toLocaleString()}
                </div>
              </div>
              <button onClick={load} style={{ display:'flex', alignItems:'center', gap:6, padding:'8px 14px', background:'rgba(255,255,255,0.1)', border:'1px solid rgba(255,255,255,0.2)', borderRadius:6, color:'white', cursor:'pointer', fontSize:13 }}>
                <RefreshCw size={14} /> Refresh
              </button>
            </div>
          )}

          {/* Tabs */}
          <div style={{ background:'white', borderRadius:8, padding:6, border:'1px solid #e2e8f0', marginBottom:16, display:'inline-flex', gap:4 }}>
            <Tab id="overview"    label="Receivables" />
            <Tab id="payables"    label="Supplier Payments" />
          </div>

          {/* Receivables Table */}
          {tab === 'overview' && (
            <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
              <div style={{ padding:'14px 20px', borderBottom:'1px solid #e2e8f0', fontWeight:600, color:BRAND.navy }}>
                Outstanding Receivables
              </div>
              {receivables.length === 0 ? (
                <div style={{ padding:40, textAlign:'center', color:'#718096', fontSize:13 }}>
                  No outstanding receivables.<br/>
                  <span style={{ fontSize:12, color:'#a0aec0' }}>Receivables are created when orders are delivered on credit terms.</span>
                </div>
              ) : (
                <table style={{ width:'100%', borderCollapse:'collapse' }}>
                  <thead style={{ background:'#F7FAFC' }}>
                    <tr>
                      {['Invoice','Buyer','Species','Amount','Outstanding','Due Date','Status'].map(h => (
                        <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {receivables.map((r, i) => (
                      <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}
                        onMouseEnter={e => e.currentTarget.style.background='#FAFBFC'}
                        onMouseLeave={e => e.currentTarget.style.background='white'}>
                        <td style={{ padding:'11px 14px', fontSize:12, fontFamily:'monospace', color:'#4a5568' }}>{r.invoice_number}</td>
                        <td style={{ padding:'11px 14px', fontWeight:600, color:BRAND.navy }}>{r.buyer_name || r.buyer_id}</td>
                        <td style={{ padding:'11px 14px', fontSize:13, textTransform:'capitalize' }}>{r.species || '—'}</td>
                        <td style={{ padding:'11px 14px', fontWeight:600, color:BRAND.blue }}>{fmt(r.total_amount_kes)}</td>
                        <td style={{ padding:'11px 14px', fontWeight:600, color:'#C05621' }}>{fmt(r.outstanding_kes)}</td>
                        <td style={{ padding:'11px 14px', fontSize:12, color: r.status === 'overdue' ? '#C53030' : '#718096' }}>
                          {r.due_date ? new Date(r.due_date).toLocaleDateString('en-KE') : '—'}
                        </td>
                        <td style={{ padding:'11px 14px' }}>
                          <span style={{
                            background: r.status==='paid' ? '#C6F6D5' : r.status==='overdue' ? '#FED7D7' : '#FEFCBF',
                            color: r.status==='paid' ? '#276749' : r.status==='overdue' ? '#742A2A' : '#744210',
                            padding:'2px 10px', borderRadius:20, fontSize:11, fontWeight:600, textTransform:'uppercase'
                          }}>{r.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* Supplier Payments */}
          {tab === 'payables' && (
            <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
              <div style={{ padding:'14px 20px', borderBottom:'1px solid #e2e8f0', fontWeight:600, color:BRAND.navy }}>
                Pending Supplier Payments
              </div>
              {pending.length === 0 ? (
                <div style={{ padding:40, textAlign:'center', color:'#718096', fontSize:13 }}>
                  No pending supplier payments.
                </div>
              ) : (
                <table style={{ width:'100%', borderCollapse:'collapse' }}>
                  <thead style={{ background:'#F7FAFC' }}>
                    <tr>
                      {['Supplier','Species','Amount','Order','Status','Action'].map(h => (
                        <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {pending.map((p, i) => (
                      <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}>
                        <td style={{ padding:'11px 14px', fontWeight:600, color:BRAND.navy }}>{p.supplier_name || p.fisher_name || p.supplier_id}</td>
                        <td style={{ padding:'11px 14px', fontSize:13, textTransform:'capitalize' }}>{p.species || '—'}</td>
                        <td style={{ padding:'11px 14px', fontWeight:600, color:BRAND.green }}>{fmt(p.amount_kes || p.total_amount_kes)}</td>
                        <td style={{ padding:'11px 14px', fontSize:12, color:'#4a5568' }}>{p.order_id || '—'}</td>
                        <td style={{ padding:'11px 14px' }}>
                          <span style={{ background:'#FEFCBF', color:'#744210', padding:'2px 8px', borderRadius:20, fontSize:11, fontWeight:600 }}>PENDING</span>
                        </td>
                        <td style={{ padding:'11px 14px' }}>
                          <button style={{ padding:'5px 12px', background:BRAND.green, color:'white', border:'none', borderRadius:6, cursor:'pointer', fontSize:12, fontWeight:500 }}>
                            Pay Now
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </>
      )}
    </Layout>
  );
}