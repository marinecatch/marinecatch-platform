// src/pages/Newsletter.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getNewsletterSubscribers, getNewsletterOverview, deleteNewsletterSubscriber } from '../services/api';

function StatCard({ label, value }) {
  return (
    <div style={{ background:'white', borderRadius:8, padding:'16px 18px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
      <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>{label}</div>
      <div style={{ fontSize:22, fontWeight:700, color:'#0D2137' }}>{value}</div>
    </div>
  );
}

export default function Newsletter() {
  const [overview, setOverview] = useState(null);
  const [subs, setSubs]         = useState([]);
  const [filter, setFilter]     = useState('');
  const [loading, setLoading]   = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      getNewsletterOverview(),
      getNewsletterSubscribers(filter ? { stakeholder_type: filter } : {}),
    ]).then(([o, s]) => {
      setOverview(o.data);
      setSubs(s.data.subscribers || []);
    }).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(load, [filter]);

  const remove = async (id, email) => {
    if (!window.confirm(`Remove ${email} from the newsletter?`)) return;
    try {
      await deleteNewsletterSubscriber(id);
      setSubs(subs.filter(s => s.id !== id));
    } catch (e) {
      alert('Could not remove subscriber.');
    }
  };

  return (
    <Layout title="Newsletter" subtitle="Subscriber list & engagement by stakeholder type">
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading newsletter data...</div>
      ) : (
        <>
          <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:20 }}>
            <StatCard label="Confirmed Subscribers" value={overview.total_subscribers} />
            <StatCard label="New This Week" value={overview.new_this_week} />
            {Object.entries(overview.breakdown_by_type || {}).map(([k, v]) => (
              <StatCard key={k} label={k} value={v} />
            ))}
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
              <div style={{ fontWeight:600, color:'#1a365d' }}>Subscribers</div>
              <select value={filter} onChange={e => setFilter(e.target.value)} style={{ padding:'6px 10px', borderRadius:6, border:'1px solid #e2e8f0', fontSize:12 }}>
                <option value="">All types</option>
                {Object.keys(overview.breakdown_by_type || {}).map(k => <option key={k} value={k}>{k}</option>)}
              </select>
            </div>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                {['Name', 'Email', 'Organization', 'Type', 'Country', 'Source', 'Status', 'Joined', ''].map(h => (
                  <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {subs.map(s => (
                  <tr key={s.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'8px 12px', fontWeight:500 }}>{s.name || '—'}</td>
                    <td style={{ padding:'8px 12px' }}>{s.email}</td>
                    <td style={{ padding:'8px 12px' }}>{s.organization || '—'}</td>
                    <td style={{ padding:'8px 12px' }}>{s.stakeholder_type || '—'}</td>
                    <td style={{ padding:'8px 12px' }}>{s.country || '—'}</td>
                    <td style={{ padding:'8px 12px' }}>{s.source || s.utm_source || '—'}</td>
                    <td style={{ padding:'8px 12px' }}>
                      <span style={{ background: s.status === 'confirmed' ? '#c6f6d5' : '#fefcbf', padding:'2px 8px', borderRadius:20, fontSize:11 }}>{s.status}</span>
                    </td>
                    <td style={{ padding:'8px 12px', color:'#718096' }}>{s.created_at ? new Date(s.created_at).toLocaleDateString() : '—'}</td>
                    <td style={{ padding:'8px 12px' }}>
                      <button onClick={() => remove(s.id, s.email)} style={{ border:'none', background:'transparent', color:'#9b2c2c', cursor:'pointer', fontSize:12 }}>Remove</button>
                    </td>
                  </tr>
                ))}
                {subs.length === 0 && <tr><td colSpan={9} style={{ padding:12, color:'#a0aec0' }}>No subscribers.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Layout>
  );
}
