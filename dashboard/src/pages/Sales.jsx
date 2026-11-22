// src/pages/Sales.jsx
import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts';
import Layout from '../components/Layout';
import {
  getSalesOverview, getPipelineSummary, getLeadsByRole, getLeadSources, getLeadsTimeline, getRecentLeads,
} from '../services/api';

function StatCard({ label, value, color = '#0D2137' }) {
  return (
    <div style={{ background:'white', borderRadius:8, padding:'16px 18px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
      <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>{label}</div>
      <div style={{ fontSize:22, fontWeight:700, color }}>{value}</div>
    </div>
  );
}

const FUNNEL_LABELS = { new: 'New', contacted: 'Contacted', qualified: 'Qualified', converted: 'Converted', not_interested: 'Not Interested' };
const STATUS_COLORS = { new: '#bee3f8', contacted: '#fefcbf', qualified: '#e9d8fd', converted: '#c6f6d5', not_interested: '#fed7d7' };

export default function Sales() {
  const [overview, setOverview]   = useState(null);
  const [pipeline, setPipeline]   = useState(null);
  const [byRole, setByRole]       = useState({});
  const [sources, setSources]     = useState({ sources_total: {}, sources_converted: {} });
  const [timeline, setTimeline]   = useState({});
  const [leads, setLeads]         = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    Promise.all([
      getSalesOverview(), getPipelineSummary(), getLeadsByRole(), getLeadSources(), getLeadsTimeline({ days: 30 }),
    ]).then(([o, p, r, s, t]) => {
      setOverview(o.data);
      setPipeline(p.data);
      setByRole(r.data.breakdown || {});
      setSources(s.data);
      setTimeline(t.data.daily_counts || {});
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    getRecentLeads(statusFilter ? { status: statusFilter, limit: 30 } : { limit: 30 })
      .then(r => setLeads(r.data.leads || []))
      .catch(console.error);
  }, [statusFilter]);

  const funnelData = pipeline ? Object.entries(pipeline.funnel).map(([k, v]) => ({ name: FUNNEL_LABELS[k] || k, count: v })) : [];
  const timelineData = Object.entries(timeline).sort().map(([day, count]) => ({ day: day.slice(5), count }));
  const roleData = Object.entries(byRole).map(([k, v]) => ({ name: k, count: v }));

  return (
    <Layout title="Sales & CRM" subtitle="Lead pipeline, source attribution & conversion">
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading sales data...</div>
      ) : (
        <>
          <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:20 }}>
            <StatCard label="Total Leads" value={overview.total_leads} />
            <StatCard label="Converted" value={overview.total_converted} color="#276749" />
            <StatCard label="Active Buyers" value={overview.total_active_buyers} color="#1D60AE" />
            <StatCard label="Total Orders" value={overview.total_orders} />
            <StatCard label="New This Week" value={overview.leads_this_week} />
            <StatCard label="Unassigned" value={overview.unassigned_leads} color="#9B2C2C" />
          </div>

          {pipeline && (
            <div style={{ marginBottom:20, background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <div style={{ fontWeight:600, marginBottom:4, color:'#1a365d' }}>Conversion Funnel</div>
              <div style={{ fontSize:12, color:'#718096', marginBottom:16 }}>{pipeline.total_leads} total leads · {pipeline.conversion_rate}% conversion rate</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={funnelData}>
                  <XAxis dataKey="name" tick={{ fontSize:12 }} />
                  <YAxis tick={{ fontSize:12 }} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#1D60AE" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <div style={{ display:'flex', gap:20, flexWrap:'wrap', marginBottom:20 }}>
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', flex:'1 1 420px' }}>
              <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Leads by Role</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={roleData} layout="vertical">
                  <XAxis type="number" tick={{ fontSize:12 }} allowDecimals={false} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize:12 }} width={90} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#00B3F0" radius={[0,4,4,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', flex:'1 1 420px' }}>
              <div style={{ fontWeight:600, marginBottom:4, color:'#1a365d' }}>New Leads — Last 30 Days</div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={timelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="day" tick={{ fontSize:11 }} />
                  <YAxis tick={{ fontSize:11 }} allowDecimals={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="#2b6cb0" strokeWidth={2} dot={{ r:3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', marginBottom:20 }}>
            <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Lead Sources (Total / Converted)</div>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                {['Source', 'Total', 'Converted'].map(h => (
                  <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {Object.keys(sources.sources_total || {}).map(src => (
                  <tr key={src} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'8px 12px', fontWeight:500 }}>{src}</td>
                    <td style={{ padding:'8px 12px' }}>{sources.sources_total[src]}</td>
                    <td style={{ padding:'8px 12px', color:'#276749' }}>{sources.sources_converted[src] || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
              <div style={{ fontWeight:600, color:'#1a365d' }}>Recent Leads</div>
              <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ padding:'6px 10px', borderRadius:6, border:'1px solid #e2e8f0', fontSize:12 }}>
                <option value="">All statuses</option>
                {Object.keys(FUNNEL_LABELS).map(k => <option key={k} value={k}>{FUNNEL_LABELS[k]}</option>)}
              </select>
            </div>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                {['Name', 'Phone', 'Location', 'Interest', 'Source', 'Status', 'Assigned'].map(h => (
                  <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {leads.map(l => (
                  <tr key={l.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'8px 12px', fontWeight:500 }}>{l.name}</td>
                    <td style={{ padding:'8px 12px' }}>{l.phone}</td>
                    <td style={{ padding:'8px 12px' }}>{l.location || '—'}</td>
                    <td style={{ padding:'8px 12px' }}>{l.interest || '—'}</td>
                    <td style={{ padding:'8px 12px' }}>{l.utm_source || 'direct'}</td>
                    <td style={{ padding:'8px 12px' }}>
                      <span style={{ background: STATUS_COLORS[l.lead_status] || '#e2e8f0', padding:'2px 8px', borderRadius:20, fontSize:11 }}>
                        {FUNNEL_LABELS[l.lead_status] || l.lead_status}
                      </span>
                    </td>
                    <td style={{ padding:'8px 12px' }}>{l.assigned_to || '—'}</td>
                  </tr>
                ))}
                {leads.length === 0 && <tr><td colSpan={7} style={{ padding:12, color:'#a0aec0' }}>No leads found.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Layout>
  );
}
