// src/pages/Orders.jsx
import { useEffect, useState } from 'react';
import { RefreshCw, Filter, ChevronDown } from 'lucide-react';
import Layout from '../components/Layout';
import { getOrders, updateOrderStatus } from '../services/api';

const BRAND = { blue:'#1D60AE', green:'#276749', navy:'#0D2137' };

const STATUS_FLOW = [
    'pending_payment',
    'confirmed',
    'processing',
    'dispatched',
    'delivered',
    'completed'
];

const STATUS_LABELS = {
    pending_payment: 'Pending Payment',
    confirmed:       'Confirmed',
    processing:      'Processing',
    dispatched:      'Dispatched',
    delivered:       'Delivered',
    completed:       'Completed',
    cancelled:       'Cancelled',
};

const STATUS_COLORS = {
    pending_payment: { bg:'#FEFCBF', color:'#744210' },
    confirmed:       { bg:'#BEE3F8', color:'#2C5282' },
    processing:      { bg:'#E9D8FD', color:'#553C9A' },
    dispatched:      { bg:'#B2F5EA', color:'#234E52' },
    delivered:       { bg:'#C6F6D5', color:'#276749' },
    completed:       { bg:'#C6F6D5', color:'#276749' },
    cancelled:       { bg:'#FED7D7', color:'#742A2A' },
};

const StatusBadge = ({ status }) => {
    const s = STATUS_COLORS[status] || { bg:'#E2E8F0', color:'#4A5568' };
    return (
        <span style={{ background:s.bg, color:s.color, padding:'3px 10px', borderRadius:20, fontSize:11, fontWeight:600, whiteSpace:'nowrap' }}>
            {STATUS_LABELS[status] || status}
        </span>
    );
};

const PayBadge = ({ status }) => {
    const map = {
        paid:            { bg:'#C6F6D5', color:'#276749' },
        unpaid:          { bg:'#FED7D7', color:'#742A2A' },
        pending_payment: { bg:'#FEFCBF', color:'#744210' },
    };
    const s = map[status] || { bg:'#E2E8F0', color:'#4A5568' };
    return (
        <span style={{ background:s.bg, color:s.color, padding:'2px 8px', borderRadius:20, fontSize:11, fontWeight:600 }}>
            {(status || '').replace(/_/g,' ')}
        </span>
    );
};

const StatusTimeline = ({ currentStatus }) => {
    const idx = STATUS_FLOW.indexOf(currentStatus);
    return (
        <div style={{ display:'flex', alignItems:'center', gap:4, flexWrap:'wrap', margin:'8px 0' }}>
            {STATUS_FLOW.map((s, i) => (
                <div key={s} style={{ display:'flex', alignItems:'center', gap:4 }}>
                    <div style={{
                        width:10, height:10, borderRadius:'50%',
                        background: i <= idx ? BRAND.blue : '#e2e8f0',
                        border: i === idx ? `2px solid ${BRAND.blue}` : 'none',
                        flexShrink:0,
                    }} title={STATUS_LABELS[s]} />
                    {i < STATUS_FLOW.length - 1 && (
                        <div style={{ width:16, height:2, background: i < idx ? BRAND.blue : '#e2e8f0' }} />
                    )}
                </div>
            ))}
            <span style={{ fontSize:11, color:'#718096', marginLeft:4 }}>{STATUS_LABELS[currentStatus] || currentStatus}</span>
        </div>
    );
};

export default function Orders() {
    const [orders, setOrders]     = useState([]);
    const [loading, setLoading]   = useState(true);
    const [filter, setFilter]     = useState('');
    const [updating, setUpdating] = useState(null);
    const [selected, setSelected] = useState(null);

    const load = async () => {
        setLoading(true);
        try {
            const res = await getOrders();
            setOrders(res.data?.orders || res.data || []);
        } catch(e) { console.error(e); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    const filtered = filter ? orders.filter(o => o.status === filter) : orders;

    const handleStatusUpdate = async (orderId, newStatus) => {
        setUpdating(orderId);
        try {
            await updateOrderStatus(orderId, newStatus);
            await load();
        } catch(e) {
            alert('Failed to update order status. Please try again.');
        } finally {
            setUpdating(null);
        }
    };

    const getNextStatus = (current) => {
        const idx = STATUS_FLOW.indexOf(current);
        if (idx === -1 || idx >= STATUS_FLOW.length - 1) return null;
        return STATUS_FLOW[idx + 1];
    };

    const totalRevenue = orders
        .filter(o => o.payment_status === 'paid')
        .reduce((s, o) => s + (o.total_buyer_pays_kes || 0), 0);

    return (
        <Layout title="Orders" subtitle="All seafood orders across all channels">
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16, marginBottom:24 }}>
                {[
                    ['Total Orders',    orders.length,                                    BRAND.navy],
                    ['Pending Payment', orders.filter(o => o.payment_status === 'unpaid' || o.payment_status === 'pending_payment').length, '#C05621'],
                    ['In Progress',     orders.filter(o => ['confirmed','processing','dispatched'].includes(o.status)).length, BRAND.blue],
                    ['Revenue (KES)',   `KES ${Math.round(totalRevenue).toLocaleString()}`, BRAND.green],
                ].map(([label, value, color]) => (
                    <div key={label} style={{ background:'white', borderRadius:8, padding:18, border:'1px solid #e2e8f0' }}>
                        <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:1 }}>{label}</div>
                        <div style={{ fontSize:26, fontWeight:700, color, marginTop:4 }}>{value}</div>
                    </div>
                ))}
            </div>

            <div style={{ background:'white', borderRadius:8, padding:14, border:'1px solid #e2e8f0', marginBottom:16, display:'flex', gap:12, alignItems:'center' }}>
                <Filter size={15} color="#a0aec0" />
                <select value={filter} onChange={e => setFilter(e.target.value)}
                    style={{ border:'1px solid #e2e8f0', borderRadius:6, padding:'7px 12px', fontSize:14, color:'#4a5568' }}>
                    <option value="">All Orders</option>
                    {Object.entries(STATUS_LABELS).map(([val, label]) => (
                        <option key={val} value={val}>{label}</option>
                    ))}
                </select>
                <button onClick={load} style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:6, padding:'7px 14px', background:'white', border:'1px solid #e2e8f0', borderRadius:6, cursor:'pointer', fontSize:13, color:'#4a5568' }}>
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            <div style={{ background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden' }}>
                {loading ? (
                    <div style={{ padding:40, textAlign:'center', color:'#718096' }}>Loading orders...</div>
                ) : filtered.length === 0 ? (
                    <div style={{ padding:40, textAlign:'center', color:'#718096' }}>No orders found.</div>
                ) : (
                    <table style={{ width:'100%', borderCollapse:'collapse' }}>
                        <thead style={{ background:'#F7FAFC' }}>
                            <tr>
                                {['Order','Species','Qty','Total','Buyer','Payment','Progress','Action'].map(h => (
                                    <th key={h} style={{ padding:'10px 14px', textAlign:'left', fontSize:11, color:'#718096', textTransform:'uppercase', letterSpacing:0.5, fontWeight:600, borderBottom:'1px solid #e2e8f0' }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map(order => {
                                const nextStatus = getNextStatus(order.status);
                                const isUpdating = updating === order.id;
                                return (
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
                                        <td style={{ padding:'12px 14px' }}><PayBadge status={order.payment_status} /></td>
                                        <td style={{ padding:'12px 14px', minWidth:200 }}>
                                            <StatusTimeline currentStatus={order.status} />
                                        </td>
                                        <td style={{ padding:'12px 14px' }}>
                                            {nextStatus && order.status !== 'cancelled' ? (
                                                <button
                                                    onClick={() => handleStatusUpdate(order.id, nextStatus)}
                                                    disabled={isUpdating}
                                                    style={{
                                                        padding:'5px 10px',
                                                        background: isUpdating ? '#a0aec0' : BRAND.blue,
                                                        color:'white', border:'none', borderRadius:6,
                                                        cursor: isUpdating ? 'not-allowed' : 'pointer',
                                                        fontSize:12, fontWeight:500, whiteSpace:'nowrap',
                                                    }}>
                                                    {isUpdating ? '...' : `Mark ${STATUS_LABELS[nextStatus]}`}
                                                </button>
                                            ) : (
                                                <span style={{ fontSize:12, color:'#a0aec0' }}>
                                                    {order.status === 'completed' ? 'Complete' : order.status === 'cancelled' ? 'Cancelled' : '—'}
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                )}
            </div>
        </Layout>
    );
}