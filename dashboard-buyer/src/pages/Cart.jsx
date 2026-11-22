// src/pages/Cart.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { checkoutCart } from '../services/api';

export default function Cart() {
  const { user } = useAuth();
  const { items, updateQuantity, removeItem, clearCart, total } = useCart();
  const navigate = useNavigate();

  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [phoneNumber, setPhoneNumber]         = useState(user?.phone || '');
  const [notes, setNotes]                     = useState('');
  const [submitting, setSubmitting]           = useState(false);
  const [error, setError]                     = useState('');
  const [success, setSuccess]                 = useState(null);

  const inputStyle = { width:'100%', padding:'10px 14px', borderRadius:8, border:'1px solid #e2e8f0', fontSize:14, boxSizing:'border-box', marginBottom:12 };

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (items.length === 0) { setError('Your cart is empty.'); return; }
    if (!deliveryAddress || !phoneNumber) { setError('Delivery address and phone number are required.'); return; }
    setSubmitting(true);
    try {
      const res = await checkoutCart({
        items: items.map(i => ({ lot_id: i.lot_id, quantity_kg: i.quantity_kg })),
        delivery_address: deliveryAddress,
        phone_number: phoneNumber,
        notes: notes || undefined,
      });
      setSuccess(res.data);
      clearCart();
    } catch (err) {
      setError(err.response?.data?.detail || 'Checkout failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <Layout title="Order Placed" subtitle="Complete payment on your phone to confirm">
        <div style={{ background:'white', borderRadius:8, padding:32, border:'1px solid #c6f6d5', textAlign:'center' }}>
          <div style={{ fontSize:40, marginBottom:12 }}>📲</div>
          <div style={{ fontSize:16, fontWeight:700, color:'#276749', marginBottom:8 }}>{success.message}</div>
          <div style={{ fontSize:13, color:'#718096', marginBottom:20 }}>
            Combined total: <b>KES {success.combined_total_kes.toLocaleString()}</b> across {success.order_ids.length} order(s)
          </div>
          <button onClick={() => navigate('/orders')} style={{ border:'none', background:'#1D60AE', color:'white', padding:'10px 24px', borderRadius:8, cursor:'pointer', fontWeight:600 }}>
            View My Orders
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Cart" subtitle="Review your order and pay via M-Pesa">
      <div style={{ display:'flex', gap:20, flexWrap:'wrap' }}>
        <div style={{ flex:'2 1 420px' }}>
          {items.length === 0 ? (
            <div style={{ background:'white', borderRadius:8, padding:40, textAlign:'center', color:'#a0aec0', border:'1px solid #e2e8f0' }}>
              Your cart is empty — browse the Marketplace to add lots.
            </div>
          ) : (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
              {items.map(i => (
                <div key={i.lot_id} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'12px 0', borderBottom:'1px solid #f7fafc' }}>
                  <div>
                    <div style={{ fontWeight:600 }}>{i.species}</div>
                    <div style={{ fontSize:12, color:'#718096' }}>{i.lot_number} · {i.landing_site} · KES {i.price_per_kg}/kg</div>
                  </div>
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <input
                      type="number" min="0.1" max={i.available_kg} step="0.1" value={i.quantity_kg}
                      onChange={e => updateQuantity(i.lot_id, parseFloat(e.target.value) || 0)}
                      style={{ width:80, padding:'6px 8px', borderRadius:6, border:'1px solid #e2e8f0', fontSize:13 }}
                    />
                    <span style={{ fontWeight:600, width:100, textAlign:'right' }}>KES {(i.price_per_kg * i.quantity_kg).toLocaleString()}</span>
                    <button onClick={() => removeItem(i.lot_id)} style={{ border:'none', background:'transparent', color:'#9b2c2c', cursor:'pointer', fontSize:12 }}>Remove</button>
                  </div>
                </div>
              ))}
              <div style={{ display:'flex', justifyContent:'space-between', paddingTop:16, fontSize:16, fontWeight:700 }}>
                <span>Total</span>
                <span style={{ color:'#276749' }}>KES {total.toLocaleString()}</span>
              </div>
            </div>
          )}
        </div>

        <div style={{ flex:'1 1 320px' }}>
          <form onSubmit={submit} style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0' }}>
            <div style={{ fontWeight:600, marginBottom:16, color:'#1a365d' }}>Checkout</div>
            {error && <div style={{ background:'#fed7d7', color:'#9b2c2c', padding:'10px 14px', borderRadius:8, fontSize:13, marginBottom:12 }}>{error}</div>}
            <label style={{ fontSize:12, fontWeight:600, color:'#4a5568' }}>Delivery address *</label>
            <textarea value={deliveryAddress} onChange={e => setDeliveryAddress(e.target.value)} rows={2} style={{ ...inputStyle, resize:'vertical' }} required />
            <label style={{ fontSize:12, fontWeight:600, color:'#4a5568' }}>M-Pesa phone number *</label>
            <input value={phoneNumber} onChange={e => setPhoneNumber(e.target.value)} placeholder="2547XXXXXXXX" style={inputStyle} required />
            <label style={{ fontSize:12, fontWeight:600, color:'#4a5568' }}>Notes</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} style={{ ...inputStyle, resize:'vertical' }} />
            <button type="submit" disabled={submitting || items.length === 0} style={{ width:'100%', padding:'12px', borderRadius:8, border:'none', background:'#1D60AE', color:'white', fontWeight:600, fontSize:14, cursor:'pointer' }}>
              {submitting ? 'Sending STK Push...' : `Pay KES ${total.toLocaleString()} via M-Pesa`}
            </button>
          </form>
        </div>
      </div>
    </Layout>
  );
}
