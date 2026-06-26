// src/pages/Dashboard.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getPlatformSummary } from '../services/api';

const StatCard = ({ label, value, sub, color='#1a365d' }) => (
  <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
    <div style={{ fontSize:12, color:'#718096', textTransform:'uppercase', letterSpacing:1 }}>{label}</div>
    <div style={{ fontSize:32, fontWeight:700, color, marginTop:4 }}>{value}</div>
    {sub && <div style={{ fontSize:12, color:'#a0aec0', marginTop:4 }}>{sub}</div>}
  </div>
);

export default function Dashboard() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPlatformSummary()
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const p = data?.platform || {};
  const m = data?.market_intelligence || {};

  return (
    <Layout title="Dashboard" subtitle="MarineCatch Africa — Live Operations">
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading...</div>
      ) : (
        <>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(180px, 1fr))', gap:16, marginBottom:24 }}>
            <StatCard label="Active Lots"       value={p.active_lots || 0}    color="#2b6cb0" />
            <StatCard label="Available (kg)"    value={`${(p.available_kg || 0).toLocaleString()}kg`} color="#276749" />
            <StatCard label="Inventory Value"   value={`KES ${(p.inventory_value_kes || 0).toLocaleString()}`} color="#744210" />
            <StatCard label="Total Orders"      value={p.total_orders || 0}   color="#553c9a" />
            <StatCard label="Active Users"      value={p.active_users || 0}   color="#2c7a7b" />
            <StatCard label="Species Traded"    value={p.species_traded || 0} color="#c05621" />
          </div>

          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>📊 Market Intelligence</div>
              <div style={{ fontSize:13, color:'#4a5568', lineHeight:1.8 }}>
                <div>BMU Records: <strong>{m.bmu_records || 0}</strong></div>
                <div>Historical Volume: <strong>{(m.historical_kg || 0).toLocaleString()}kg</strong></div>
                <div>Historical Value: <strong>KES {(m.historical_value_kes || 0).toLocaleString()}</strong></div>
                <div style={{ marginTop:8, fontSize:11, color:'#a0aec0' }}>{m.data_source}</div>
              </div>
            </div>
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>🎯 Prove 3 Things</div>
              <div style={{ fontSize:13, color:'#4a5568', lineHeight:2 }}>
                <div>✅ Fish can be listed</div>
                <div>✅ Fish can be ordered</div>
                <div>{p.total_orders > 0 ? '✅' : '⏳'} Fish can be paid for</div>
              </div>
              <div style={{ marginTop:12, fontSize:11, color:'#718096' }}>
                Launch target: 24th July 2026
              </div>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}