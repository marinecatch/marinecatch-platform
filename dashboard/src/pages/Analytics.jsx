// src/pages/Analytics.jsx
import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, Legend } from 'recharts';
import Layout from '../components/Layout';
import { getSpeciesSummary, getMonthlyTrends } from '../services/api';

export default function Analytics() {
  const [species, setSpecies]   = useState([]);
  const [trends, setTrends]     = useState([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      getSpeciesSummary({ year: 2025 }),
      getMonthlyTrends({ year: 2025 }),
    ]).then(([s, t]) => {
      setSpecies(s.data.species || []);
      setTrends(t.data.trends || []);
    }).catch(console.error)
    .finally(() => setLoading(false));
  }, []);

  const topSpecies = species.slice(0, 8).map(s => ({
    name: s.local_name || s.species,
    kg:   Math.round(s.total_kg),
    value: Math.round((s.total_value_kes || 0) / 1000),
  }));

  const monthNames = { 1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec' };
  const trendData = trends.map(t => ({
    month: monthNames[t.month] || t.month,
    kg:    Math.round(t.total_kg),
    value: Math.round((t.total_value_kes || 0) / 1000),
  }));

  return (
    <Layout title="Analytics" subtitle="Kibuyuni BMU Fisheries Intelligence 2025">
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading analytics...</div>
      ) : (
        <>
          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', marginBottom:20 }}>
            <div style={{ fontWeight:600, marginBottom:4, color:'#1a365d' }}>Top Species by Volume (kg) — Kibuyuni 2025</div>
            <div style={{ fontSize:12, color:'#718096', marginBottom:16 }}>Source: Kibuyuni BMU — Kenya Fisheries Service</div>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={topSpecies}>
                <XAxis dataKey="name" tick={{ fontSize:12 }} />
                <YAxis tick={{ fontSize:12 }} />
                <Tooltip formatter={(val) => [`${val.toLocaleString()}kg`, 'Volume']} />
                <Bar dataKey="kg" fill="#2b6cb0" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', marginBottom:20 }}>
            <div style={{ fontWeight:600, marginBottom:4, color:'#1a365d' }}>Monthly Catch Trends 2025</div>
            <div style={{ fontSize:12, color:'#718096', marginBottom:16 }}>Volume (kg) and Value (KES thousands)</div>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize:12 }} />
                <YAxis yAxisId="left" tick={{ fontSize:12 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize:12 }} />
                <Tooltip />
                <Legend />
                <Line yAxisId="left"  type="monotone" dataKey="kg"    stroke="#2b6cb0" strokeWidth={2} dot={{ r:4 }} name="Volume (kg)" />
                <Line yAxisId="right" type="monotone" dataKey="value" stroke="#276749" strokeWidth={2} dot={{ r:4 }} name="Value (KES 000)" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
            <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Species Intelligence Table</div>
            <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
              <thead>
                <tr style={{ borderBottom:'2px solid #e2e8f0' }}>
                  {['Species','Local Name','Category','Total (kg)','Value (KES)','Avg Price/kg'].map(h => (
                    <th key={h} style={{ textAlign:'left', padding:'8px 12px', color:'#718096', fontWeight:500, fontSize:11, textTransform:'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {species.map((s, i) => (
                  <tr key={i} style={{ borderBottom:'1px solid #f7fafc' }}>
                    <td style={{ padding:'10px 12px', fontWeight:500 }}>{s.species}</td>
                    <td style={{ padding:'10px 12px', color:'#4a5568' }}>{s.local_name}</td>
                    <td style={{ padding:'10px 12px' }}>
                      <span style={{ background: s.category === 'pelagic' ? '#bee3f8' : s.category === 'demersal' ? '#c6f6d5' : '#fefcbf', padding:'2px 8px', borderRadius:20, fontSize:11 }}>
                        {s.category}
                      </span>
                    </td>
                    <td style={{ padding:'10px 12px' }}>{s.total_kg.toLocaleString()}kg</td>
                    <td style={{ padding:'10px 12px' }}>KES {(s.total_value_kes || 0).toLocaleString()}</td>
                    <td style={{ padding:'10px 12px', fontWeight:500, color:'#276749' }}>KES {(s.avg_price_per_kg || 0).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Layout>
  );
}