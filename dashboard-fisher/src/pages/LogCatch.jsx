// src/pages/LogCatch.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { createLot } from '../services/api';

const SPECIES = ['Octopus', 'Red Snapper', 'Kingfish', 'Tuna', 'Lobster', 'Prawns', 'Rabbitfish', 'Parrotfish', 'Grouper', 'Other'];
const CONDITIONS = ['fresh', 'iced', 'frozen'];
const FORMS = ['whole_ungutted', 'whole_gutted', 'fillet', 'live'];

export default function LogCatch() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    species: '', weight_kg: '', selling_price_per_kg: '', landing_site: '',
    condition: 'fresh', product_form: 'whole_ungutted', vessel_reg: '', gear_type: '', notes: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]   = useState('');
  const [success, setSuccess] = useState(null);

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const inputStyle = { width:'100%', padding:'10px 14px', borderRadius:8, border:'1px solid #e2e8f0', fontSize:14, boxSizing:'border-box' };
  const label = { fontSize:12, fontWeight:600, color:'#4a5568', marginBottom:6, display:'block' };

  const submit = async (e) => {
    e.preventDefault();
    setError(''); setSuccess(null);
    if (!form.species || !form.weight_kg || !form.selling_price_per_kg || !form.landing_site) {
      setError('Species, weight, price and landing site are required.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await createLot({
        species: form.species,
        weight_kg: parseFloat(form.weight_kg),
        selling_price_per_kg: parseFloat(form.selling_price_per_kg),
        landing_site: form.landing_site,
        condition: form.condition,
        product_form: form.product_form,
        vessel_reg: form.vessel_reg || undefined,
        gear_type: form.gear_type || undefined,
        notes: form.notes || undefined,
      });
      setSuccess(res.data);
      setForm({ species: '', weight_kg: '', selling_price_per_kg: '', landing_site: form.landing_site, condition: 'fresh', product_form: 'whole_ungutted', vessel_reg: form.vessel_reg, gear_type: form.gear_type, notes: '' });
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not log this catch. Please check the details and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Layout title="Log Catch" subtitle="List a new lot for buyers to see — it goes to inspection before it appears on the marketplace">
      <div style={{ display:'flex', gap:20, flexWrap:'wrap' }}>
        <form onSubmit={submit} style={{ background:'white', borderRadius:8, padding:24, border:'1px solid #e2e8f0', flex:'2 1 420px' }}>
          {error && <div style={{ background:'#fed7d7', color:'#9b2c2c', padding:'10px 14px', borderRadius:8, fontSize:13, marginBottom:16 }}>{error}</div>}

          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16 }}>
            <div>
              <label style={label}>Species *</label>
              <select value={form.species} onChange={set('species')} style={inputStyle} required>
                <option value="">Select species</option>
                {SPECIES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label style={label}>Landing site *</label>
              <input value={form.landing_site} onChange={set('landing_site')} placeholder="e.g. Kibuyuni" style={inputStyle} required />
            </div>
            <div>
              <label style={label}>Weight (kg) *</label>
              <input type="number" step="0.1" min="0" value={form.weight_kg} onChange={set('weight_kg')} style={inputStyle} required />
            </div>
            <div>
              <label style={label}>Price per kg (KES) *</label>
              <input type="number" step="1" min="0" value={form.selling_price_per_kg} onChange={set('selling_price_per_kg')} style={inputStyle} required />
            </div>
            <div>
              <label style={label}>Condition</label>
              <select value={form.condition} onChange={set('condition')} style={inputStyle}>
                {CONDITIONS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label style={label}>Product form</label>
              <select value={form.product_form} onChange={set('product_form')} style={inputStyle}>
                {FORMS.map(f => <option key={f} value={f}>{f.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div>
              <label style={label}>Vessel registration</label>
              <input value={form.vessel_reg} onChange={set('vessel_reg')} style={inputStyle} />
            </div>
            <div>
              <label style={label}>Gear type</label>
              <input value={form.gear_type} onChange={set('gear_type')} placeholder="e.g. handline, gillnet" style={inputStyle} />
            </div>
          </div>

          <label style={label}>Notes</label>
          <textarea value={form.notes} onChange={set('notes')} rows={3} style={{ ...inputStyle, marginBottom:16, resize:'vertical' }} />

          <button type="submit" disabled={submitting} style={{ padding:'12px 28px', borderRadius:8, border:'none', background:'#1D60AE', color:'white', fontWeight:600, fontSize:14, cursor:'pointer' }}>
            {submitting ? 'Submitting...' : 'Log Catch'}
          </button>
        </form>

        <div style={{ flex:'1 1 260px' }}>
          {success ? (
            <div style={{ background:'#c6f6d5', borderRadius:8, padding:20, border:'1px solid #9ae6b4' }}>
              <div style={{ fontWeight:700, color:'#276749', marginBottom:8 }}>✓ {success.message}</div>
              <div style={{ fontSize:13, color:'#276749', lineHeight:1.8 }}>
                <div>Lot #: <b>{success.lot_number}</b></div>
                <div>Traceability code: <b>{success.traceability_code}</b></div>
                <div>Total value: <b>KES {success.total_value_kes.toLocaleString()}</b></div>
              </div>
              <button onClick={() => navigate('/')} style={{ marginTop:12, border:'none', background:'#276749', color:'white', padding:'8px 16px', borderRadius:6, cursor:'pointer', fontSize:13 }}>
                View in My Catch
              </button>
            </div>
          ) : (
            <div style={{ background:'white', borderRadius:8, padding:20, border:'1px solid #e2e8f0', fontSize:13, color:'#718096', lineHeight:1.7 }}>
              New lots go through quality inspection before they're visible to buyers. You'll see the result on the Compliance & Reputation tab.
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
