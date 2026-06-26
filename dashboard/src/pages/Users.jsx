// src/pages/Users.jsx
import { useEffect, useState } from 'react';
import { RefreshCw, Search } from 'lucide-react';
import Layout from '../components/Layout';
import { getUsers } from '../services/api';

const BRAND = { blue:'#1D60AE', green:'#276749', navy:'#0D2137' };

const roleBadge = (role) => {
  const r = role?.toLowerCase().replace('userrole.','');
  const map = {
    admin:    { bg:'#E9D8FD', color:'#553C9A' },
    fisher:   { bg:'#C6F6D5', color:'#276749' },
    buyer:    { bg:'#BEE3F8', color:'#2C5282' },
    supplier: { bg:'#FEFCBF', color:'#744210' },
  };
  const s = map[r] || { bg:'#E2E8F0', color:'#4A5568' };
  return <span style={{ ...s, padding:'2px 10px', borderRadius:20, fontSize:11, fontWeight:600, textTransform:'uppercase' }}>{r}</span>;
};

export default function Users() {
  const [users, setUsers]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState('');
  const [role, setRole]       = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const res = await getUsers();
      setUsers(Array.isArray(res.data) ? res.data : res.data?.users || []);
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const filtered = users.filter(u => {
    const matchSearch = !search ||
      u.name?.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase()) ||
      u.phone?.includes(search);
    const matchRole = !role || u.role?.toLowerCase().includes(role);
    return matchSearch && matchRole;
  });

  const counts = {
    total:    users.length,
    fishers:  users.filter(u => u.role?.toLowerCase().includes('fisher')).length,
    buyers:   users.filter(u => u.role?.toLowerCase().includes('buyer')).length,
    suppliers:users.filter(u => u.role?.toLowerCase().includes('supplier')).length,
  };

  return (
    <Layout title="Users" subtitle="Fishers, buyers, suppliers and partners">
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16, marginBottom:24 }}>
        {[
          ['Total Users', counts.total,    BRAND.navy],
          ['Fishers',     counts.fishers,  BRAND.green],
          ['Buyers',      counts.buyers,   BRAND.blue],
          ['Suppliers',   counts.suppliers,'#744210'],
        ].map(([label, value, color]) => (
          <div key={label} style={{ background:'white', borderRadius:8, padding:18, border:'1px solid #e2e8f0' }}>
            <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:1 }}>{label}</div>
            <div style={{ fontSize:26, fontWeight:700, color, marginTop:4 }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ background:'white', borderRadius:8, padding:14, border:'1px solid #e2e8f0', marginBottom:16, display:'flex', gap:12, alignItems:'center', flexWrap:'wrap' }}>
        <Search size={15} color="#a0aec0" />
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search by name, email or phone..."
          style={{ border:'1px solid #e2e8f0', borderRadius:6, padding:'7px 12px', fontSize:14, flex:1, minWidth:200 }} />
        <select value={role} onChange={e => setRole(e.target.value)}
          style={{ border:'1px solid #e2e8f0', borderRadius:6, padding:'7px 12px', fontSize:14 }}>
          <option value="">All Roles</option>
          <option value="fisher">Fishers</option>
          <option value="buyer">Buyers</option>
          <option value="supplier">Suppliers</option>
          <option value="admin">Admin</option>
        </select>
        <button onClick={load} style={{ display:'flex', alignItems:'center', gap:6, padding:'7px 14px', background:'white', border:'1px solid #e2e8f0', borderRadius:6, cursor:'pointer', fontSize:13, color:'#4a5568' }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
        {loading ? (
          <div style={{ padding:40, textAlign:'center', color:'#718096' }}>Loading users...</div>
        ) : (
          <table style={{ width:'100%', borderCollapse:'collapse' }}>
            <thead style={{ background:'#F7FAFC' }}>
              <tr>
                {['Name','Email','Phone','Role','Location','Status','Joined'].map(h => (
                  <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(u => (
                <tr key={u.id} style={{ borderBottom:'1px solid #f7fafc' }}
                  onMouseEnter={e => e.currentTarget.style.background='#FAFBFC'}
                  onMouseLeave={e => e.currentTarget.style.background='white'}>
                  <td style={{ padding:'11px 14px', fontWeight:600, color:BRAND.navy }}>{u.name}</td>
                  <td style={{ padding:'11px 14px', fontSize:13, color:'#4a5568' }}>{u.email}</td>
                  <td style={{ padding:'11px 14px', fontSize:13, color:'#4a5568' }}>{u.phone}</td>
                  <td style={{ padding:'11px 14px' }}>{roleBadge(u.role)}</td>
                  <td style={{ padding:'11px 14px', fontSize:13, textTransform:'capitalize' }}>{u.location || '—'}</td>
                  <td style={{ padding:'11px 14px' }}>
                    <span style={{ background: u.is_active ? '#C6F6D5' : '#FED7D7', color: u.is_active ? '#276749' : '#742A2A', padding:'2px 8px', borderRadius:20, fontSize:11, fontWeight:600 }}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={{ padding:'11px 14px', fontSize:12, color:'#718096' }}>
                    {u.created_at ? new Date(u.created_at).toLocaleDateString('en-KE') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
}