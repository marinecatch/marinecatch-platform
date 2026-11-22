// src/pages/Compliance.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import { getMyComplianceProfile, getMyInspections, getMyCluster } from '../services/api';

function Badge({ ok, yes = 'Verified', no = 'Unverified' }) {
  return (
    <span style={{ background: ok ? '#c6f6d5' : '#fed7d7', color: ok ? '#276749' : '#9b2c2c', padding:'2px 10px', borderRadius:20, fontSize:12, fontWeight:600 }}>
      {ok ? yes : no}
    </span>
  );
}

export default function Compliance() {
  const { user } = useAuth();
  const [profile, setProfile]   = useState(null);
  const [inspections, setInspections] = useState([]);
  const [cluster, setCluster]   = useState(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      getMyComplianceProfile(user.id).catch(() => ({ data: null })),
      getMyInspections().catch(() => ({ data: { inspections: [] } })),
      getMyCluster().catch(() => ({ data: null })),
    ]).then(([p, i, c]) => {
      setProfile(p.data);
      setInspections(i.data.inspections || []);
      setCluster(c.data);
    }).finally(() => setLoading(false));
  }, [user]);

  return (
    <Layout title="Compliance & Reputation" subtitle="Your verification status, trust score & catch quality history">
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading your profile...</div>
      ) : (
        <>
          {profile && (
            <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:20 }}>
              <div style={{ background:'white', borderRadius:8, padding:'18px 20px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
                <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>Trust Score</div>
                <div style={{ fontSize:26, fontWeight:700, color:'#1D60AE' }}>{profile.trust_score ?? '—'}</div>
              </div>
              <div style={{ background:'white', borderRadius:8, padding:'18px 20px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
                <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>Compliance Level</div>
                <div style={{ fontSize:26, fontWeight:700, color:'#0D2137' }}>L{profile.compliance_level}</div>
              </div>
              <div style={{ background:'white', borderRadius:8, padding:'18px 20px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
                <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>Transactions</div>
                <div style={{ fontSize:26, fontWeight:700, color:'#0D2137' }}>{profile.total_transactions ?? 0}</div>
              </div>
            </div>
          )}

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', marginBottom:20 }}>
            <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Verification Status</div>
            <div style={{ display:'flex', gap:24, flexWrap:'wrap' }}>
              <div>National ID: {profile ? <Badge ok={profile.national_id_verified} /> : '—'}</div>
              <div>BMU Membership: {profile ? <Badge ok={profile.bmu_verified} yes={profile.bmu_name || 'Verified'} /> : '—'}</div>
              <div>KRA PIN: {profile ? <Badge ok={profile.kra_verified} /> : '—'}</div>
            </div>
          </div>

          {cluster && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', marginBottom:20, fontSize:13 }}>
              <div style={{ fontWeight:600, marginBottom:10, color:'#1a365d' }}>Your Cluster</div>
              <div style={{ color:'#4a5568' }}>{cluster.name} · {cluster.members_count} members · credit score {cluster.credit_score ?? '—'}</div>
            </div>
          )}

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
            <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Catch Inspection History</div>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                {['Lot #', 'Species', 'Grade', 'Inspector', 'Date', 'Notes'].map(h => (
                  <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {inspections.map((ins, i) => (
                  <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'8px 12px', fontWeight:500 }}>{ins.lot_number}</td>
                    <td style={{ padding:'8px 12px' }}>{ins.species}</td>
                    <td style={{ padding:'8px 12px' }}>
                      <span style={{ background: ['A','A+'].includes(ins.grade) ? '#c6f6d5' : '#fefcbf', padding:'2px 8px', borderRadius:20, fontSize:11 }}>{ins.grade}</span>
                    </td>
                    <td style={{ padding:'8px 12px' }}>{ins.inspector_name || '—'}</td>
                    <td style={{ padding:'8px 12px', color:'#718096' }}>{ins.inspected_at ? new Date(ins.inspected_at).toLocaleDateString() : '—'}</td>
                    <td style={{ padding:'8px 12px', color:'#718096' }}>{ins.notes || '—'}</td>
                  </tr>
                ))}
                {inspections.length === 0 && <tr><td colSpan={6} style={{ padding:12, color:'#a0aec0' }}>No inspections yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Layout>
  );
}
