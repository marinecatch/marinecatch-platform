// src/pages/Compliance.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import {
  getComplianceProfiles, getPendingInspections, getDrafts, getClusterLeaderboard,
} from '../services/api';

const TABS = ['Profiles', 'Pending Inspections', 'Catch Drafts', 'Cluster Leaderboard'];

function Badge({ ok, yes = 'Verified', no = 'Unverified' }) {
  return (
    <span style={{
      background: ok ? '#c6f6d5' : '#fed7d7',
      color: ok ? '#276749' : '#9b2c2c',
      padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600,
    }}>
      {ok ? yes : no}
    </span>
  );
}

function Th({ children }) {
  return <th style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{children}</th>;
}
function Td({ children, ...rest }) {
  return <td style={{ padding:'10px 12px' }} {...rest}>{children}</td>;
}

export default function Compliance() {
  const [tab, setTab]         = useState(TABS[0]);
  const [profiles, setProfiles] = useState([]);
  const [pending, setPending]   = useState([]);
  const [drafts, setDrafts]     = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [leaderboardErr, setLeaderboardErr] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getComplianceProfiles().catch(() => ({ data: { profiles: [] } })),
      getPendingInspections().catch(() => ({ data: { pending: [] } })),
      getDrafts().catch(() => ({ data: { drafts: [] } })),
      getClusterLeaderboard().catch(err => { setLeaderboardErr(err.response?.status === 403 ? 'CEO access only' : 'Unavailable'); return { data: { clusters: [] } }; }),
    ]).then(([p, i, d, l]) => {
      setProfiles(p.data.profiles || []);
      setPending(i.data.pending || []);
      setDrafts(d.data.drafts || []);
      setLeaderboard(l.data.clusters || []);
    }).finally(() => setLoading(false));
  }, []);

  return (
    <Layout title="Compliance" subtitle="Member verification, quality inspections & catch drafts">
      <div style={{ display:'flex', gap:8, marginBottom:20, borderBottom:'1px solid #e2e8f0' }}>
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding:'10px 16px', border:'none', background:'transparent', cursor:'pointer',
            fontWeight: tab === t ? 600 : 400, color: tab === t ? '#1D60AE' : '#718096',
            borderBottom: tab === t ? '2px solid #1D60AE' : '2px solid transparent', fontSize:13,
          }}>{t}</button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading compliance data...</div>
      ) : (
        <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>

          {tab === 'Profiles' && (
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                <Th>Member ID</Th><Th>Name</Th><Th>Role</Th><Th>Level</Th><Th>National ID</Th><Th>BMU</Th><Th>KRA</Th><Th>Trust Score</Th><Th>Transactions</Th>
              </tr></thead>
              <tbody>
                {profiles.map(p => (
                  <tr key={p.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <Td>{p.member_id || '—'}</Td>
                    <Td style={{ fontWeight:500 }}>{p.user_name}</Td>
                    <Td>{p.user_role}</Td>
                    <Td>L{p.compliance_level}</Td>
                    <Td><Badge ok={p.national_id_verified} /></Td>
                    <Td>{p.bmu_verified ? <Badge ok yes={p.bmu_name || 'Verified'} /> : <Badge ok={false} />}</Td>
                    <Td><Badge ok={p.kra_verified} /></Td>
                    <Td style={{ fontWeight:600 }}>{p.trust_score ?? '—'}</Td>
                    <Td>{p.total_transactions ?? 0} · KES {(p.total_value_kes || 0).toLocaleString()}</Td>
                  </tr>
                ))}
                {profiles.length === 0 && <tr><Td colSpan={9} style={{ color:'#a0aec0' }}>No compliance profiles found.</Td></tr>}
              </tbody>
            </table>
          )}

          {tab === 'Pending Inspections' && (
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                <Th>Lot #</Th><Th>Species</Th><Th>Weight</Th><Th>Landing Site</Th><Th>Source</Th><Th>Catch Date</Th>
              </tr></thead>
              <tbody>
                {pending.map(p => (
                  <tr key={p.lot_id} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <Td style={{ fontWeight:500 }}>{p.lot_number}</Td>
                    <Td>{p.species}</Td>
                    <Td>{p.weight_kg}kg</Td>
                    <Td>{p.landing_site || '—'}</Td>
                    <Td>{p.source_name || '—'}</Td>
                    <Td>{p.catch_date ? new Date(p.catch_date).toLocaleDateString() : '—'}</Td>
                  </tr>
                ))}
                {pending.length === 0 && <tr><Td colSpan={6} style={{ color:'#a0aec0' }}>Nothing awaiting inspection.</Td></tr>}
              </tbody>
            </table>
          )}

          {tab === 'Catch Drafts' && (
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                <Th>Reference</Th><Th>Fisher</Th><Th>Species</Th><Th>Weight</Th><Th>Asking Price</Th><Th>Status</Th><Th>Channel</Th><Th>Inspection</Th>
              </tr></thead>
              <tbody>
                {drafts.map(d => (
                  <tr key={d.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <Td style={{ fontWeight:500 }}>{d.reference}</Td>
                    <Td>{d.fisher_name}<div style={{ fontSize:11, color:'#718096' }}>{d.fisher_phone}</div></Td>
                    <Td>{d.species}</Td>
                    <Td>{d.weight_kg}kg</Td>
                    <Td>KES {d.asking_price_per_kg}/kg</Td>
                    <Td><span style={{ background:'#bee3f8', padding:'2px 8px', borderRadius:20, fontSize:11 }}>{d.status}</span></Td>
                    <Td>{d.channel}</Td>
                    <Td>{d.inspection_grade ? `Grade ${d.inspection_grade}` : '—'}</Td>
                  </tr>
                ))}
                {drafts.length === 0 && <tr><Td colSpan={8} style={{ color:'#a0aec0' }}>No catch drafts.</Td></tr>}
              </tbody>
            </table>
          )}

          {tab === 'Cluster Leaderboard' && (
            leaderboardErr ? (
              <div style={{ color:'#9b2c2c' }}>{leaderboardErr}</div>
            ) : (
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  <Th>Cluster</Th><Th>BMU</Th><Th>Members</Th><Th>Total Earnings</Th><Th>Credit Score</Th><Th>Monthly Capacity</Th>
                </tr></thead>
                <tbody>
                  {leaderboard.map((c, i) => (
                    <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <Td style={{ fontWeight:500 }}>{c.name}</Td>
                      <Td>{c.bmu_name}</Td>
                      <Td>{c.members_count}</Td>
                      <Td style={{ color:'#276749', fontWeight:500 }}>KES {(c.total_earnings_kes || 0).toLocaleString()}</Td>
                      <Td>{c.credit_score ?? '—'}</Td>
                      <Td>{c.monthly_capacity_kg ? `${c.monthly_capacity_kg}kg` : '—'}</Td>
                    </tr>
                  ))}
                  {leaderboard.length === 0 && <tr><Td colSpan={6} style={{ color:'#a0aec0' }}>No active clusters.</Td></tr>}
                </tbody>
              </table>
            )
          )}
        </div>
      )}
    </Layout>
  );
}
