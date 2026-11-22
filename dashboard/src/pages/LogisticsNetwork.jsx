// src/pages/LogisticsNetwork.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import {
  getLogisticsNetworkSummary, getLogisticsPartners, getStorageNodes, getCoolers,
  getActiveJobs, getOpenExceptions, getPendingPartnerApplications, approvePartnerApplication, resolveException,
} from '../services/api';

const TABS = ['Overview', 'Partners', 'Storage Nodes', 'Coolers', 'Active Jobs', 'Exceptions', 'Partner Applications'];

function StatCard({ label, value, color = '#0D2137' }) {
  return (
    <div style={{ background:'white', borderRadius:8, padding:'16px 18px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
      <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>{label}</div>
      <div style={{ fontSize:22, fontWeight:700, color }}>{value}</div>
    </div>
  );
}
function Th({ children }) {
  return <th style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{children}</th>;
}

const COOLER_COLOR = { available: '#c6f6d5', in_use: '#bee3f8', damaged: '#fed7d7', lost: '#fed7d7' };
const SEVERITY_COLOR = { low: '#bee3f8', medium: '#fefcbf', high: '#feb2b2', critical: '#fc8181' };

export default function LogisticsNetwork() {
  const [tab, setTab] = useState(TABS[0]);
  const [summary, setSummary]       = useState(null);
  const [partners, setPartners]     = useState([]);
  const [nodes, setNodes]           = useState([]);
  const [coolers, setCoolers]       = useState([]);
  const [jobs, setJobs]             = useState([]);
  const [exceptions, setExceptions] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading]       = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      getLogisticsNetworkSummary(), getLogisticsPartners(), getStorageNodes(), getCoolers(),
      getActiveJobs(), getOpenExceptions(), getPendingPartnerApplications(),
    ]).then(([s, p, n, c, j, e, a]) => {
      setSummary(s.data);
      setPartners(p.data.partners || []);
      setNodes(n.data.nodes || []);
      setCoolers(c.data.coolers || []);
      setJobs(j.data.jobs || []);
      setExceptions(e.data.exceptions || []);
      setApplications(a.data.applications || []);
    }).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const approve = async (id) => {
    try { await approvePartnerApplication(id); load(); } catch { alert('Could not approve partner.'); }
  };
  const resolve = async (id) => {
    const notes = window.prompt('Resolution notes:');
    if (notes === null) return;
    try { await resolveException(id, { resolution_notes: notes }); load(); } catch { alert('Could not resolve exception.'); }
  };

  return (
    <Layout title="Logistics Network" subtitle="Partners, storage nodes, coolers, transport jobs & exceptions">
      <div style={{ display:'flex', gap:8, marginBottom:20, borderBottom:'1px solid #e2e8f0', flexWrap:'wrap' }}>
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding:'10px 14px', border:'none', background:'transparent', cursor:'pointer',
            fontWeight: tab === t ? 600 : 400, color: tab === t ? '#1D60AE' : '#718096',
            borderBottom: tab === t ? '2px solid #1D60AE' : '2px solid transparent', fontSize:13,
          }}>{t}</button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading logistics network...</div>
      ) : (
        <>
          {tab === 'Overview' && summary && (
            <div style={{ display:'flex', gap:16, flexWrap:'wrap' }}>
              <StatCard label="Active Partners" value={summary.partners.total_active} />
              <StatCard label="Storage Nodes" value={summary.storage.total_nodes} />
              <StatCard label="Storage Capacity" value={`${summary.storage.total_capacity_kg.toLocaleString()}kg`} />
              <StatCard label="Storage Utilization" value={`${summary.storage.utilization_pct}%`} />
              <StatCard label="Coolers (total)" value={summary.coolers.total} />
              <StatCard label="Coolers Available" value={summary.coolers.available} color="#276749" />
              <StatCard label="Coolers Lost/Damaged" value={summary.coolers.lost_or_damaged} color="#9B2C2C" />
              <StatCard label="Active Jobs" value={summary.jobs.active} />
              <StatCard label="Delayed Jobs" value={summary.jobs.delayed} color="#9B2C2C" />
              <StatCard label="Open Exceptions" value={summary.exceptions.open ?? exceptions.length} color="#9B2C2C" />
            </div>
          )}

          {tab === 'Partners' && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  <Th>Name</Th><Th>Type</Th><Th>Phone</Th><Th>Coverage</Th><Th>Cold Chain</Th><Th>On-Time Rate</Th><Th>Jobs Done</Th>
                </tr></thead>
                <tbody>
                  {partners.map(p => (
                    <tr key={p.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'8px 12px', fontWeight:500 }}>{p.name}</td>
                      <td style={{ padding:'8px 12px' }}>{p.partner_type}</td>
                      <td style={{ padding:'8px 12px' }}>{p.contact_phone}</td>
                      <td style={{ padding:'8px 12px' }}>{p.coverage_areas || '—'}</td>
                      <td style={{ padding:'8px 12px' }}>{p.cold_chain_capable ? 'Yes' : 'No'}</td>
                      <td style={{ padding:'8px 12px' }}>{p.on_time_rate != null ? `${p.on_time_rate}%` : '—'}</td>
                      <td style={{ padding:'8px 12px' }}>{p.total_jobs_completed}</td>
                    </tr>
                  ))}
                  {partners.length === 0 && <tr><td colSpan={7} style={{ padding:12, color:'#a0aec0' }}>No partners.</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'Storage Nodes' && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  <Th>Name</Th><Th>Operator</Th><Th>Location</Th><Th>Capacity</Th><Th>Available</Th><Th>Power</Th><Th>Ice Machine</Th>
                </tr></thead>
                <tbody>
                  {nodes.map(n => (
                    <tr key={n.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'8px 12px', fontWeight:500 }}>{n.name}</td>
                      <td style={{ padding:'8px 12px' }}>{n.operator_name || '—'}</td>
                      <td style={{ padding:'8px 12px' }}>{n.location}</td>
                      <td style={{ padding:'8px 12px' }}>{n.capacity_kg}kg</td>
                      <td style={{ padding:'8px 12px' }}>{n.available_kg}kg</td>
                      <td style={{ padding:'8px 12px' }}>{n.power_source || '—'}</td>
                      <td style={{ padding:'8px 12px' }}>{n.has_ice_machine ? 'Yes' : 'No'}</td>
                    </tr>
                  ))}
                  {nodes.length === 0 && <tr><td colSpan={7} style={{ padding:12, color:'#a0aec0' }}>No storage nodes.</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'Coolers' && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  <Th>Asset Code</Th><Th>Capacity</Th><Th>Owner</Th><Th>Status</Th><Th>Holder</Th><Th>Location</Th>
                </tr></thead>
                <tbody>
                  {coolers.map(c => (
                    <tr key={c.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'8px 12px', fontWeight:500 }}>{c.asset_code}</td>
                      <td style={{ padding:'8px 12px' }}>{c.capacity_kg}kg</td>
                      <td style={{ padding:'8px 12px' }}>{c.owner}</td>
                      <td style={{ padding:'8px 12px' }}>
                        <span style={{ background: COOLER_COLOR[c.status] || '#e2e8f0', padding:'2px 8px', borderRadius:20, fontSize:11 }}>{c.status}</span>
                      </td>
                      <td style={{ padding:'8px 12px' }}>{c.current_holder || '—'}</td>
                      <td style={{ padding:'8px 12px' }}>{c.current_location || '—'}</td>
                    </tr>
                  ))}
                  {coolers.length === 0 && <tr><td colSpan={6} style={{ padding:12, color:'#a0aec0' }}>No coolers registered.</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'Active Jobs' && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  <Th>Type</Th><Th>Status</Th><Th>Pickup</Th><Th>Destination</Th><Th>Partner</Th><Th>Tracking</Th><Th>Cost</Th>
                </tr></thead>
                <tbody>
                  {jobs.map(j => (
                    <tr key={j.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'8px 12px', fontWeight:500 }}>{j.job_type}</td>
                      <td style={{ padding:'8px 12px' }}>
                        <span style={{ background: j.status === 'delayed' ? '#fed7d7' : '#bee3f8', padding:'2px 8px', borderRadius:20, fontSize:11 }}>{j.status}</span>
                      </td>
                      <td style={{ padding:'8px 12px' }}>{j.pickup_location}</td>
                      <td style={{ padding:'8px 12px' }}>{j.destination_location}</td>
                      <td style={{ padding:'8px 12px' }}>{j.partner_name || '—'}</td>
                      <td style={{ padding:'8px 12px', fontSize:12, color:'#718096' }}>{j.tracking_reference || '—'}</td>
                      <td style={{ padding:'8px 12px' }}>{j.cost_kes ? `KES ${j.cost_kes.toLocaleString()}` : '—'}</td>
                    </tr>
                  ))}
                  {jobs.length === 0 && <tr><td colSpan={7} style={{ padding:12, color:'#a0aec0' }}>No active jobs.</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'Exceptions' && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  <Th>Type</Th><Th>Severity</Th><Th>Description</Th><Th>Status</Th><Th>Reported By</Th><Th>Reported At</Th><Th></Th>
                </tr></thead>
                <tbody>
                  {exceptions.map(e => (
                    <tr key={e.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'8px 12px', fontWeight:500 }}>{e.exception_type}</td>
                      <td style={{ padding:'8px 12px' }}>
                        <span style={{ background: SEVERITY_COLOR[e.severity] || '#e2e8f0', padding:'2px 8px', borderRadius:20, fontSize:11 }}>{e.severity}</span>
                      </td>
                      <td style={{ padding:'8px 12px' }}>{e.description}</td>
                      <td style={{ padding:'8px 12px' }}>{e.resolution_status}</td>
                      <td style={{ padding:'8px 12px' }}>{e.reported_by || '—'}</td>
                      <td style={{ padding:'8px 12px', color:'#718096' }}>{e.reported_at ? new Date(e.reported_at).toLocaleString() : '—'}</td>
                      <td style={{ padding:'8px 12px' }}>
                        <button onClick={() => resolve(e.id)} style={{ border:'none', background:'transparent', color:'#1D60AE', cursor:'pointer', fontSize:12, fontWeight:600 }}>Resolve</button>
                      </td>
                    </tr>
                  ))}
                  {exceptions.length === 0 && <tr><td colSpan={7} style={{ padding:12, color:'#a0aec0' }}>No open exceptions.</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'Partner Applications' && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  <Th>Name</Th><Th>Type</Th><Th>Contact</Th><Th>Coverage</Th><Th>Cold Chain</Th><Th>Applied</Th><Th></Th>
                </tr></thead>
                <tbody>
                  {applications.map(a => (
                    <tr key={a.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'8px 12px', fontWeight:500 }}>{a.name}</td>
                      <td style={{ padding:'8px 12px' }}>{a.partner_type}</td>
                      <td style={{ padding:'8px 12px' }}>{a.contact_person} · {a.contact_phone}</td>
                      <td style={{ padding:'8px 12px' }}>{a.coverage_areas || '—'}</td>
                      <td style={{ padding:'8px 12px' }}>{a.cold_chain_capable ? 'Yes' : 'No'}</td>
                      <td style={{ padding:'8px 12px', color:'#718096' }}>{a.onboarded_at ? new Date(a.onboarded_at).toLocaleDateString() : '—'}</td>
                      <td style={{ padding:'8px 12px' }}>
                        <button onClick={() => approve(a.id)} style={{ border:'none', background:'#276749', color:'white', padding:'4px 10px', borderRadius:6, cursor:'pointer', fontSize:12 }}>Approve</button>
                      </td>
                    </tr>
                  ))}
                  {applications.length === 0 && <tr><td colSpan={7} style={{ padding:12, color:'#a0aec0' }}>No pending applications.</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </Layout>
  );
}
