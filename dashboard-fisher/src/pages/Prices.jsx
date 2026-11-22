// src/pages/Prices.jsx
import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import Layout from '../components/Layout';
import { getPriceIntelligence } from '../services/api';

export default function Prices() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPriceIntelligence().then(r => setData(r.data)).catch(console.error).finally(() => setLoading(false));
  }, []);

  const platform = data?.platform_prices || [];
  const bmu      = data?.bmu_intelligence || [];

  return (
    <Layout title="Market Prices" subtitle="Live platform prices and historical BMU reference prices, by species">
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading price intelligence...</div>
      ) : (
        <>
          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', marginBottom:20 }}>
            <div style={{ fontWeight:600, marginBottom:4, color:'#1a365d' }}>Live Platform Prices — Avg KES/kg</div>
            <div style={{ fontSize:12, color:'#718096', marginBottom:16 }}>Across currently available lots on the marketplace right now</div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={platform}>
                <XAxis dataKey="species" tick={{ fontSize:11 }} angle={-20} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize:11 }} />
                <Tooltip formatter={(v) => [`KES ${v}`, 'Avg price/kg']} />
                <Bar dataKey="platform_avg_kes" fill="#1D60AE" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', marginBottom:20 }}>
            <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Live Platform Prices — Detail</div>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                {['Species', 'Avg Price/kg', 'Min', 'Max', 'Available (kg)', 'Active Lots'].map(h => (
                  <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {platform.map((s, i) => (
                  <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'8px 12px', fontWeight:500 }}>{s.species}</td>
                    <td style={{ padding:'8px 12px', fontWeight:600, color:'#276749' }}>KES {s.platform_avg_kes}</td>
                    <td style={{ padding:'8px 12px' }}>KES {s.platform_min_kes}</td>
                    <td style={{ padding:'8px 12px' }}>KES {s.platform_max_kes}</td>
                    <td style={{ padding:'8px 12px' }}>{s.available_kg}kg</td>
                    <td style={{ padding:'8px 12px' }}>{s.active_lots}</td>
                  </tr>
                ))}
                {platform.length === 0 && <tr><td colSpan={6} style={{ padding:12, color:'#a0aec0' }}>No lots currently available.</td></tr>}
              </tbody>
            </table>
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
            <div style={{ fontWeight:600, marginBottom:4, color:'#1a365d' }}>Historical Reference Prices (BMU Records)</div>
            <div style={{ fontSize:12, color:'#718096', marginBottom:16 }}>Kwale County BMU records 2024–2025 — useful for negotiating a fair price</div>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead><tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                {['Species', 'Local Name', 'Avg KES/kg', 'Min', 'Max'].map(h => (
                  <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {bmu.map((s, i) => (
                  <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'8px 12px', fontWeight:500 }}>{s.species}</td>
                    <td style={{ padding:'8px 12px', color:'#718096' }}>{s.local_name || '—'}</td>
                    <td style={{ padding:'8px 12px' }}>KES {s.avg_kes}</td>
                    <td style={{ padding:'8px 12px' }}>KES {s.min_kes}</td>
                    <td style={{ padding:'8px 12px' }}>KES {s.max_kes}</td>
                  </tr>
                ))}
                {bmu.length === 0 && <tr><td colSpan={5} style={{ padding:12, color:'#a0aec0' }}>No historical records.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Layout>
  );
}
