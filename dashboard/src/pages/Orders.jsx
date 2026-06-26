// src/pages/Orders.jsx
import { useEffect, useState } from 'react';
import { RefreshCw, Filter } from 'lucide-react';
import Layout from '../components/Layout';
import { getOrders } from '../services/api';

const BRAND = { blue:'#1D60AE', green:'#276749', navy:'#0D2137' };

const statusBadge = (status) => {
  const map = {
    pending_payment: { bg:'#FEFCBF', color:'#744210', label:'Pending Payment' },
    confirmed:       { bg:'#BEE3F8', color:'#2C5282', label:'Confirmed' },
    processing:      { bg:'#E9D8FD', color:'#553C9A', label:'Processing' },
    dispatched:      { bg:'#B2F5EA', color:'#234E52', label:'Dispatched' },
    delivered:       { bg:'#C6F6D5', color:'#276749', label:'Delivered' },
    completed:       { bg:'#C6F6D5', color:'#276749', label:'Completed' },
    cancelled:       { bg:'#FED7D7', color:'#742A2A', label:'Cancelled' },
  };
  const s = map[status] || { bg:'#E2E8F0', color:'#4A5568', label: status };
  return <span style={{ background:s.bg, color:s.color, padding:'3px 10px', borderRadius:20, fontSize:11, fontWeight:600 }}>{s.label}</span>;
};

const payBadge = (status) => {
  const map = {
    paid:    { bg:'#C6F6D5', color:'#276749' },
    unpaid:  { bg:'#FED7D7', color:'#742A2A' },
    pending_payment: { bg:'#FEFCBF', color:'#744210' },
  };
  const s = map[status] || { bg:'#E2E8F0', color:'#4A5568' };
  return <span style={{ background:s.bg, color:s.color, padding:'2px 8px', borderRadius:20, fontSize:11, fontWeight:600 }}>{status?.replace('_',' ')}</span>;
};

export default function Orders() {
  const [orders, setOrders]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter]   = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const res = await getOrders();
      setOrders(res.data?.orders || res.data || []);
    } catch(e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const filtered = filter
    ? orders.filter(o => o.status === filter)
    : orders;

  const totalRevenue = orders
    .filter(o => o.payment_status === 'paid')
    .reduce((s, o) => s + (o.total_buyer_pays_kes || 0), 0);

  return (
    <Layout title="Orders" subtitle="All seafood orders across all channels">
      {/* Stats */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16, marginBottom:24 }}>
        {[
          ['Total Orders',    orders.length,                                   BRAND.blue],
          ['Pending Payment', orders.filter(o=>o.payment_status==='pending_payment'||o.payment_status==='unpaid').length, '#C05621'],
          ['Confirmed',       orders.filter(o=>o.status==='confirmed').length, BRAND.green],
          ['Revenue (KES)',   `KES ${Math.round(totalRevenue).toLocaleString()}`, BRAND.navy],
        ].map(([label, value, color]) => (
          <div key={label} style={{ background:'white', borderRadius:8, padding:18, border:'1px solid #e2e8f0' }}>
            <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:1 }}>{label}</div>
            <div style={{ fontSize:26, fontWeight:700, color, marginTop:4 }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div style={{ background:'white', borderRadius:8, padding:16, border:'1px solid #e2e8f0', marginBottom:16, display:'flex', gap:12, alignItems:'center' }}>
        <Filter size={15} color="#a0aec0" />
        <select value={filter} onChange={e => setFilter(e.target.value)}
          style={{ border:'1px solid #e2e8f0', borderRadius:6, padding:'7px 12px', fontSize:14, color:'#4a5568' }}>
          <option value="">All Orders</option>
          <option value="pending_payment">Pending Payment</option>
          <option value="confirmed">Confirmed</option>
          <option value="processing">Processing</option>
          <option value="dispatched">Dispatched</option>
          <option value="delivered">Delivered</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <button onClick={load} style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:6, padding:'7px 14px', background:'white', border:'1px solid #e2e8f0', borderRadius:6, cursor:'pointer', fontSize:13, color:'#4a5568' }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Table */}
      <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
        {loading ? (
          <div style={{ padding:40, textAlign:'center', color:'#718096' }}>Loading orders...</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding:40, textAlign:'center', color:'#718096' }}>No orders found.</div>
        ) : (
          <table style={{ width:'100%', borderCollapse:'collapse' }}>
            <thead style={{ background:'#F7FAFC' }}>
              <tr>
                {['Order','Species','Qty','Total (KES)','Buyer','Payment','Status','Date'].map(h => (
                  <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(order => (
                <tr key={order.id} style={{ borderBottom:'1px solid #f7fafc' }}
                  onMouseEnter={e => e.currentTarget.style.background='#FAFBFC'}
                  onMouseLeave={e => e.currentTarget.style.background='white'}>
                  <td style={{ padding:'12px 14px', fontSize:12, color:'#4a5568', fontFamily:'monospace' }}>{order.order_number}</td>
                  <td style={{ padding:'12px 14px', fontWeight:600, color:BRAND.navy, textTransform:'capitalize' }}>{order.species}</td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{order.quantity_kg}kg</td>
                  <td style={{ padding:'12px 14px', fontWeight:600, color:BRAND.green }}>
                    {(order.total_buyer_pays_kes || 0).toLocaleString()}
                  </td>
                  <td style={{ padding:'12px 14px', fontSize:13 }}>{order.buyer_name || order.buyer_id}</td>
                  <td style={{ padding:'12px 14px' }}>{payBadge(order.payment_status)}</td>
                  <td style={{ padding:'12px 14px' }}>{statusBadge(order.status)}</td>
                  <td style={{ padding:'12px 14px', fontSize:12, color:'#718096' }}>
                    {order.created_at ? new Date(order.created_at).toLocaleDateString('en-KE') : '—'}
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