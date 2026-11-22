// src/pages/LPORequest.jsx
import { useState } from 'react';
import Layout from '../components/Layout';
import { submitLpoRequest } from '../services/api';

const emptyItem = () => ({ species: '', quantity_kg: '', notes: '' });

export default function LPORequest() {
  const [lpoReference, setLpoReference] = useState('');
  const [items, setItems]               = useState([emptyItem()]);
  const [officer, setOfficer]           = useState('');
  const [expectedDate, setExpectedDate] = useState('');
  const [terms, setTerms]               = useState(7);
  const [address, setAddress]           = useState('');
  const [notes, setNotes]               = useState('');
  const [submitting, setSubmitting]     = useState(false);
  const [error, setError]               = useState('');
  const [success, setSuccess]           = useState(null);

  const inputStyle = { width:'100%', padding:'10px 14px', borderRadius:8, border:'1px solid #e2e8f0', fontSize:14, boxSizing:'border-box' };
  const label = { fontSize:12, fontWeight:600, color:'#4a5568', marginBottom:6, display:'block' };

  const setItem = (i, field, value) => {
    const next = [...items];
    next[i] = { ...next[i], [field]: value };
    setItems(next);
  };
  const addItem = () => setItems([...items, emptyItem()]);
  const removeItem = (i) => setItems(items.filter((_, idx) => idx !== i));

  const submit = async (e) => {
    e.preventDefault();
    setError(''); setSuccess(null);
    const validItems = items.filter(it => it.species && it.quantity_kg);
    if (!lpoReference || validItems.length === 0 || !address) {
      setError('LPO reference, at least one item (species + quantity) and a delivery address are required.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await submitLpoRequest({
        lpo_reference: lpoReference,
        items: validItems.map(it => ({ species: it.species, quantity_kg: parseFloat(it.quantity_kg), notes: it.notes || undefined })),
        procurement_officer: officer || undefined,
        expected_fulfillment_date: expectedDate || undefined,
        payment_terms_days: parseInt(terms, 10) || 7,
        delivery_address: address,
        notes: notes || undefined,
      });
      setSuccess(res.data);
      setLpoReference(''); setItems([emptyItem()]); setOfficer(''); setExpectedDate(''); setNotes('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not submit this LPO request.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Layout title="LPO Request" subtitle="Institutional buyers: submit a purchase order by species & quantity — our team assigns real lots and confirms">
      {success && (
        <div style={{ background:'#c6f6d5', borderRadius:8, padding:16, border:'1px solid #9ae6b4', marginBottom:20, color:'#276749' }}>
          ✓ {success.message} — status: <b>{success.status}</b>. You'll see the resulting order(s) in "My Orders" once fulfilled.
        </div>
      )}
      <form onSubmit={submit} style={{ background:'white', borderRadius:8, padding:24, border:'1px solid #e2e8f0' }}>
        {error && <div style={{ background:'#fed7d7', color:'#9b2c2c', padding:'10px 14px', borderRadius:8, fontSize:13, marginBottom:16 }}>{error}</div>}

        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16 }}>
          <div>
            <label style={label}>LPO Reference *</label>
            <input value={lpoReference} onChange={e => setLpoReference(e.target.value)} placeholder="e.g. LPO-2026-0042" style={inputStyle} required />
          </div>
          <div>
            <label style={label}>Procurement officer</label>
            <input value={officer} onChange={e => setOfficer(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <label style={label}>Expected fulfillment date</label>
            <input type="date" value={expectedDate} onChange={e => setExpectedDate(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <label style={label}>Payment terms (days)</label>
            <input type="number" min="0" value={terms} onChange={e => setTerms(e.target.value)} style={inputStyle} />
          </div>
        </div>

        <label style={label}>Delivery address *</label>
        <textarea value={address} onChange={e => setAddress(e.target.value)} rows={2} style={{ ...inputStyle, resize:'vertical', marginBottom:16 }} required />

        <div style={{ fontWeight:600, marginBottom:10, color:'#1a365d' }}>Line Items</div>
        {items.map((it, i) => (
          <div key={i} style={{ display:'flex', gap:10, marginBottom:10, alignItems:'center' }}>
            <input placeholder="Species" value={it.species} onChange={e => setItem(i, 'species', e.target.value)} style={{ ...inputStyle, flex:2 }} />
            <input type="number" min="0" step="0.1" placeholder="Quantity (kg)" value={it.quantity_kg} onChange={e => setItem(i, 'quantity_kg', e.target.value)} style={{ ...inputStyle, flex:1 }} />
            <input placeholder="Notes" value={it.notes} onChange={e => setItem(i, 'notes', e.target.value)} style={{ ...inputStyle, flex:2 }} />
            {items.length > 1 && (
              <button type="button" onClick={() => removeItem(i)} style={{ border:'none', background:'transparent', color:'#9b2c2c', cursor:'pointer', fontSize:18, lineHeight:1 }}>×</button>
            )}
          </div>
        ))}
        <button type="button" onClick={addItem} style={{ border:'1px solid #e2e8f0', background:'white', color:'#1D60AE', padding:'6px 14px', borderRadius:6, cursor:'pointer', fontSize:12, marginBottom:16 }}>
          + Add another species
        </button>

        <label style={label}>Notes</label>
        <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} style={{ ...inputStyle, resize:'vertical', marginBottom:20 }} />

        <button type="submit" disabled={submitting} style={{ padding:'12px 28px', borderRadius:8, border:'none', background:'#1D60AE', color:'white', fontWeight:600, fontSize:14, cursor:'pointer' }}>
          {submitting ? 'Submitting...' : 'Submit LPO Request'}
        </button>
      </form>
    </Layout>
  );
}
