// src/pages/Orders.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getMyOrders, cancelOrder, getOrderPayment } from '../services/api';

const STATUS_COLOR = {
  pending: '#fefcbf', paid: '#c6f6d5', confirmed: '#bee3f8', delivered: '#c6f6d5',
  cancelled: '#fed7d7', expired: '#fed7d7', processing: '#bee3f8',
};

export default function Orders() {
  const [orders, setOrders]   = useState([]);
  const [filter, setFilter]   = useState('');
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [payment, setPayment] = useState(null);

  const load = () => {
    setLoading(true);
    getMyOrders(filter ? { status: filter } : {}).then(r => setOrders(r.data.orders || [])).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(load, [filter]);

  const toggleExpand = async (orderId) => {
    if (expanded === orderId) { setExpanded(null); return; }
    setExpanded(orderId);
    setPayment(null);
    try {
      const r = await getOrderPayment(orderId);
      setPayment(r.data);
    } catch { setPayment(null); }
  };

  const cancel = async (orderId) => {
    if (!window.confirm('Cancel this order?')) return;
    try { await cancelOrder(orderId); load(); } catch (e) { alert(e.response?.data?.detail || 'Could not cancel order.'); }
  };

  return (
    <Layout title="My Orders" subtitle="Your order history and payment status">
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
        <select value={filter} onChange={e => setFilter(e.target.value)} style={{ padding:'8px 12px', borderRadius:6, border:'1px solid #e2e8f0', fontSize:13 }}>
          <option value="">All statuses</option>
          {Object.keys(STATUS_COLOR).map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading orders...</div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          {orders.map(o => (
            <div key={o.order_id} style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
              <div onClick={() => toggleExpand(o.order_id)} style={{ padding:16, cursor:'pointer', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <div>
                  <div style={{ fontWeight:600 }}>{o.species} — {o.quantity_kg}kg</div>
                  <div style={{ fontSize:12, color:'#718096' }}>Order #{o.order_id} · {o.landing_site} · {new Date(o.created_at).toLocaleDateString()}</div>
                </div>
                <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                  <span style={{ fontWeight:700, color:'#276749' }}>KES {o.total_kes.toLocaleString()}</span>
                  <span style={{ background: STATUS_COLOR[o.status] || '#e2e8f0', padding:'3px 10px', borderRadius:20, fontSize:11, fontWeight:600 }}>{o.status}</span>
                </div>
              </div>
              {expanded === o.order_id && (
                <div style={{ padding:'0 16px 16px', borderTop:'1px solid #f7fafc', fontSize:13 }}>
                  {payment ? (
                    <div style={{ marginTop:12, color:'#4a5568' }}>
                      Payment: <b>{payment.payment_status}</b>{payment.payment_method && <> via {payment.payment_method}</>}
                      {payment.mpesa_receipt && <> · Receipt {payment.mpesa_receipt}</>}
                    </div>
                  ) : (
                    <div style={{ marginTop:12, color:'#a0aec0' }}>No payment record yet.</div>
                  )}
                  {o.status === 'pending' && (
                    <button onClick={() => cancel(o.order_id)} style={{ marginTop:10, border:'1px solid #fed7d7', background:'white', color:'#9b2c2c', padding:'6px 14px', borderRadius:6, cursor:'pointer', fontSize:12 }}>
                      Cancel Order
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
          {orders.length === 0 && (
            <div style={{ background:'white', borderRadius:8, padding:40, textAlign:'center', color:'#a0aec0', border:'1px solid #e2e8f0' }}>
              No orders yet — visit the Marketplace to place your first order.
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}
