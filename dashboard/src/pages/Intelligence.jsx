// src/pages/Intelligence.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import {
  getCountries, getAdminGeographyTree, getLandingSites, getIntelSpecies, getDataQuality,
} from '../services/api';

const TABS = ['Overview', 'Geography', 'Landing Sites', 'Species'];

function StatCard({ label, value }) {
  return (
    <div style={{ background:'white', borderRadius:8, padding:'16px 18px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
      <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>{label}</div>
      <div style={{ fontSize:22, fontWeight:700, color:'#0D2137' }}>{value}</div>
    </div>
  );
}

function TreeNode({ node, depth = 0 }) {
  const [open, setOpen] = useState(depth < 1);
  const hasChildren = node.children && node.children.length > 0;
  return (
    <div>
      <div
        onClick={() => hasChildren && setOpen(!open)}
        style={{ padding:'6px 8px', paddingLeft: 8 + depth * 18, cursor: hasChildren ? 'pointer' : 'default', fontSize:13, display:'flex', alignItems:'center', gap:6 }}
      >
        {hasChildren && <span style={{ color:'#718096', fontSize:11 }}>{open ? '▼' : '▶'}</span>}
        <span style={{ fontWeight: depth === 0 ? 600 : 400 }}>{node.name}</span>
        <span style={{ fontSize:11, color:'#a0aec0' }}>{node.type}</span>
      </div>
      {hasChildren && open && node.children.map(c => <TreeNode key={c.id} node={c} depth={depth + 1} />)}
    </div>
  );
}

export default function Intelligence() {
  const [tab, setTab]           = useState(TABS[0]);
  const [countries, setCountries] = useState([]);
  const [country, setCountry]   = useState('KEN');
  const [tree, setTree]         = useState([]);
  const [sites, setSites]       = useState([]);
  const [species, setSpecies]   = useState([]);
  const [quality, setQuality]   = useState(null);
  const [loading, setLoading]   = useState(true);

  const COUNTRY_NAMES = { KEN: 'Kenya', TZA: 'Tanzania', SOM: 'Somalia' };

  useEffect(() => {
    getCountries().then(r => setCountries(r.data.countries?.length ? r.data.countries : ['KEN', 'TZA']))
      .catch(() => setCountries(['KEN', 'TZA']));
    getDataQuality().then(r => setQuality(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getAdminGeographyTree({ country }).catch(() => ({ data: { tree: [] } })),
      // Note: landing-sites/species aren't filterable by country on the backend yet —
      // this shows the full catalogue regardless of the selected tab.
      getLandingSites().catch(() => ({ data: { landing_sites: [] } })),
      getIntelSpecies().catch(() => ({ data: { species: [] } })),
    ]).then(([t, s, sp]) => {
      setTree(t.data.tree || []);
      setSites(s.data.landing_sites || s.data.sites || []);
      setSpecies(sp.data.species || []);
    }).finally(() => setLoading(false));
  }, [country]);

  return (
    <Layout title="Intelligence" subtitle="Geography & species data — Western Indian Ocean coastal zones">
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20, flexWrap:'wrap', gap:12 }}>
        <div style={{ display:'flex', gap:8, borderBottom:'1px solid #e2e8f0' }}>
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding:'10px 16px', border:'none', background:'transparent', cursor:'pointer',
              fontWeight: tab === t ? 600 : 400, color: tab === t ? '#1D60AE' : '#718096',
              borderBottom: tab === t ? '2px solid #1D60AE' : '2px solid transparent', fontSize:13,
            }}>{t}</button>
          ))}
        </div>
        <select value={country} onChange={e => setCountry(e.target.value)} style={{ padding:'8px 12px', borderRadius:6, border:'1px solid #e2e8f0', fontSize:13 }}>
          {countries.map(c => <option key={c} value={c}>{COUNTRY_NAMES[c] || c}</option>)}
        </select>
      </div>

      {tab === 'Overview' && quality && (
        <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:20 }}>
          <StatCard label="Landing Sites" value={quality.total_landing_sites} />
          <StatCard label="BMUs" value={quality.total_bmus} />
          <StatCard label="Species Catalogued" value={quality.total_species} />
          <StatCard label="Sources" value={quality.total_sources} />
          <StatCard label="% Verified" value={`${quality.pct_verified}%`} />
          <StatCard label="% With Coordinates" value={`${quality.pct_with_coordinates}%`} />
          <StatCard label="Needs Verification" value={quality.needs_verification_count} />
          <StatCard label="Unreconciled Claims" value={quality.unreconciled_claims_count} />
        </div>
      )}

      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading {country} intelligence...</div>
      ) : (
        <>
          {tab === 'Geography' && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <div style={{ fontWeight:600, marginBottom:12, color:'#1a365d' }}>Administrative Geography Tree</div>
              {tree.length === 0 ? <div style={{ color:'#a0aec0' }}>No geography data for this country.</div> :
                tree.map(n => <TreeNode key={n.id} node={n} />)}
            </div>
          )}

          {tab === 'Landing Sites' && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  {['Name','Type','County/Region','Verification','Coordinates'].map(h => (
                    <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {sites.map(s => (
                    <tr key={s.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'10px 12px', fontWeight:500 }}>{s.name}</td>
                      <td style={{ padding:'10px 12px' }}>{s.site_type || '—'}</td>
                      <td style={{ padding:'10px 12px' }}>{s.admin_region || s.county || '—'}</td>
                      <td style={{ padding:'10px 12px' }}>
                        <span style={{ background: s.verification_status?.startsWith('VERIFIED') ? '#c6f6d5' : '#fefcbf', color:'#276749', padding:'2px 8px', borderRadius:20, fontSize:11 }}>
                          {s.verification_status || 'UNKNOWN'}
                        </span>
                      </td>
                      <td style={{ padding:'10px 12px', fontSize:12, color:'#718096' }}>
                        {s.latitude ? `${s.latitude.toFixed(3)}, ${s.longitude.toFixed(3)}` : '—'}
                      </td>
                    </tr>
                  ))}
                  {sites.length === 0 && <tr><td colSpan={5} style={{ padding:12, color:'#a0aec0' }}>No landing sites found.</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'Species' && (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  {['Common Name','Scientific Name','Family','Category','IUCN Status','Verification'].map(h => (
                    <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {species.map(s => (
                    <tr key={s.id} style={{ borderBottom:'1px solid #f7fafc' }}>
                      <td style={{ padding:'10px 12px', fontWeight:500 }}>{s.common_name}</td>
                      <td style={{ padding:'10px 12px', fontStyle:'italic', color:'#4a5568' }}>{s.scientific_name}</td>
                      <td style={{ padding:'10px 12px' }}>{s.family || '—'}</td>
                      <td style={{ padding:'10px 12px' }}>
                        <span style={{ background: s.category === 'pelagic' ? '#bee3f8' : s.category === 'demersal' ? '#c6f6d5' : '#fefcbf', padding:'2px 8px', borderRadius:20, fontSize:11 }}>
                          {s.category}
                        </span>
                      </td>
                      <td style={{ padding:'10px 12px' }}>{s.iucn_status || '—'}</td>
                      <td style={{ padding:'10px 12px', fontSize:12, color:'#718096' }}>{s.verification_status}</td>
                    </tr>
                  ))}
                  {species.length === 0 && <tr><td colSpan={6} style={{ padding:12, color:'#a0aec0' }}>No species catalogued.</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </Layout>
  );
}
