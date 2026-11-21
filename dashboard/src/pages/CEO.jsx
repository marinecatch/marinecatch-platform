// src/pages/CEO.jsx
import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import { getExecutiveSummary } from '../services/api';

const COLORS = ['#1D60AE', '#00B3F0', '#276749', '#D69E2E', '#9B2C2C', '#718096'];

function StatCard({ label, value, sub, color = '#0D2137' }) {
  return (
    <div style={{ background:'white', borderRadius:8, padding:'18px 20px', border:'1px solid #e2e8f0', flex:1, minWidth:180 }}>
      <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, marginBottom:6 }}>{label}</div>
      <div style={{ fontSize:24, fontWeight:700, color }}>{value}</div>
      {sub && <div style={{ fontSize:12, color:'#718096', marginTop:4 }}>{sub}</div>}
    </div>
  );
}

export default function CEO() {
  const { user } = useAuth();
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    getExecutiveSummary()
      .then(res => setData(res.data))
      .catch(err => setError(err.response?.status === 403
        ? 'Executive summary is restricted to CEO accounts.'
        : 'Could not load executive summary.'))
      .finally(() => setLoading(false));
  }, []);

  const fmt = (n) => `KES ${Math.round(n || 0).toLocaleString()}`;

  return (
    <Layout title="Executive Summary" subtitle={`MarineCatch Africa — Platform overview${user?.name ? ` · ${user.name}` : ''}`}>
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading executive summary...</div>
      ) : error ? (
        <div style={{ background:'white', borderRadius:8, padding:24, border:'1px solid #fed7d7', color:'#9b2c2c' }}>{error}</div>
      ) : (
        <>
          <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:20 }}>
            <StatCard label="Gross Merchandise Value" value={fmt(data.gmv_kes)} />
            <StatCard label="Revenue (paid orders)" value={fmt(data.revenue_kes)} color="#276749" />
            <StatCard label="Platform Commission" value={fmt(data.platform_commission_kes)} color="#1D60AE" />
            <StatCard label="Fisher Payouts Owed" value={fmt(data.fisher_payouts_owed_kes)} color="#9B2C2C" />
          </div>

          <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:20 }}>
            <StatCard label="Total Users" value={(data.total_users || 0).toLocaleString()} />
            <StatCard label="Total Fishers" value={(data.total_fishers || 0).toLocaleString()} />
            <StatCard label="Total Buyers" value={(data.total_buyers || 0).toLocaleString()} />
          </div>

          <div style={{ display:'flex', gap:20, flexWrap:'wrap', marginBottom:20 }}>
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', flex:'1 1 420px' }}>
              <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Top Buyers by Spend</div>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead>
                  <tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                    {['Buyer', 'Orders', 'Total Spent'].map(h => (
                      <th key={h} style={{ textAlign:'left', padding:'8px 4px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(data.top_buyers || []).map(b => (
                    <tr key={b.buyer_id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'8px 4px', fontWeight:500 }}>{b.name}</td>
                      <td style={{ padding:'8px 4px' }}>{b.order_count}</td>
                      <td style={{ padding:'8px 4px', color:'#276749', fontWeight:500 }}>{fmt(b.total_spent_kes)}</td>
                    </tr>
                  ))}
                  {(!data.top_buyers || data.top_buyers.length === 0) && (
                    <tr><td colSpan={3} style={{ padding:'12px 4px', color:'#a0aec0' }}>No paid orders yet.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', flex:'1 1 420px' }}>
              <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Top Fishers by Earnings</div>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead>
                  <tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                    {['Fisher', 'Orders', 'Total Earned'].map(h => (
                      <th key={h} style={{ textAlign:'left', padding:'8px 4px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(data.top_fishers || []).map(f => (
                    <tr key={f.fisher_id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'8px 4px', fontWeight:500 }}>{f.name}</td>
                      <td style={{ padding:'8px 4px' }}>{f.order_count}</td>
                      <td style={{ padding:'8px 4px', color:'#276749', fontWeight:500 }}>{fmt(f.total_earned_kes)}</td>
                    </tr>
                  ))}
                  {(!data.top_fishers || data.top_fishers.length === 0) && (
                    <tr><td colSpan={3} style={{ padding:'12px 4px', color:'#a0aec0' }}>No paid orders yet.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div style={{ display:'flex', gap:20, flexWrap:'wrap' }}>
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', flex:'1 1 420px' }}>
              <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Revenue by Species</div>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={(data.species_mix || []).slice(0, 8)}>
                  <XAxis dataKey="species" tick={{ fontSize:11 }} />
                  <YAxis tick={{ fontSize:11 }} />
                  <Tooltip formatter={(v) => [`KES ${v.toLocaleString()}`, 'Revenue']} />
                  <Bar dataKey="revenue_kes" fill="#1D60AE" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', flex:'1 1 420px' }}>
              <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Revenue by Landing Site</div>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={(data.regional_mix || []).slice(0, 6)} dataKey="revenue_kes" nameKey="landing_site" cx="50%" cy="50%" outerRadius={90} label={(e) => e.landing_site}>
                    {(data.regional_mix || []).slice(0, 6).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(v) => [`KES ${v.toLocaleString()}`, 'Revenue']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}
