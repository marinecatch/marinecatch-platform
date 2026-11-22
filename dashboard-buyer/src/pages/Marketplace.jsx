// src/pages/Marketplace.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { useCart } from '../context/CartContext';
import { browseInventory } from '../services/api';

export default function Marketplace() {
  const { addItem, items } = useCart();
  const [lots, setLots]       = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ species: '', landing_site: '', condition: '', max_price_per_kg: '' });
  const [qty, setQty]         = useState({});
  const [added, setAdded]     = useState(null);

  const load = () => {
    setLoading(true);
    const params = {};
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
    browseInventory(params).then(r => setLots(r.data.lots || [])).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const inCart = (lotId) => items.some(i => i.lot_id === lotId);

  const addToCart = (lot) => {
    const q = parseFloat(qty[lot.id]) || lot.available_kg;
    if (q <= 0 || q > lot.available_kg) {
      alert(`Enter a quantity between 0 and ${lot.available_kg}kg.`);
      return;
    }
    addItem(lot, q);
    setAdded(lot.id);
    setTimeout(() => setAdded(null), 1500);
  };

  const inputStyle = { padding:'8px 12px', borderRadius:6, border:'1px solid #e2e8f0', fontSize:13 };

  return (
    <Layout title="Marketplace" subtitle="Fresh catch available right now, direct from fishers and suppliers">
      <div style={{ background:'white', borderRadius:8, padding:16, border:'1px solid #e2e8f0', marginBottom:20, display:'flex', gap:10, flexWrap:'wrap', alignItems:'center' }}>
        <input placeholder="Species" value={filters.species} onChange={e => setFilters({ ...filters, species: e.target.value })} style={inputStyle} />
        <input placeholder="Landing site" value={filters.landing_site} onChange={e => setFilters({ ...filters, landing_site: e.target.value })} style={inputStyle} />
        <select value={filters.condition} onChange={e => setFilters({ ...filters, condition: e.target.value })} style={inputStyle}>
          <option value="">Any condition</option>
          <option value="fresh">Fresh</option>
          <option value="iced">Iced</option>
          <option value="frozen">Frozen</option>
        </select>
        <input type="number" placeholder="Max price/kg" value={filters.max_price_per_kg} onChange={e => setFilters({ ...filters, max_price_per_kg: e.target.value })} style={{ ...inputStyle, width:130 }} />
        <button onClick={load} style={{ padding:'8px 20px', borderRadius:6, border:'none', background:'#1D60AE', color:'white', fontWeight:600, cursor:'pointer', fontSize:13 }}>
          Search
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading marketplace...</div>
      ) : (
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(280px, 1fr))', gap:16 }}>
          {lots.map(lot => (
            <div key={lot.id} style={{ background:'white', borderRadius:8, padding:18, border:'1px solid #e2e8f0' }}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'start', marginBottom:8 }}>
                <div style={{ fontWeight:700, fontSize:15, color:'#0D2137' }}>{lot.species}</div>
                <span style={{ background: lot.grade === 'A' ? '#c6f6d5' : '#fefcbf', padding:'2px 8px', borderRadius:20, fontSize:11, fontWeight:600 }}>
                  Grade {lot.grade || '—'}
                </span>
              </div>
              <div style={{ fontSize:12, color:'#718096', marginBottom:10 }}>
                {lot.landing_site} · {lot.condition} · {lot.product_form?.replace(/_/g, ' ')}
              </div>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:4, fontSize:13 }}>
                <span style={{ color:'#718096' }}>Available</span>
                <span style={{ fontWeight:600 }}>{lot.available_kg}kg</span>
              </div>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:14, fontSize:13 }}>
                <span style={{ color:'#718096' }}>Price/kg</span>
                <span style={{ fontWeight:700, color:'#276749' }}>KES {lot.selling_price_per_kg}</span>
              </div>
              <div style={{ display:'flex', gap:8 }}>
                <input
                  type="number" placeholder={`up to ${lot.available_kg}`} min="0.1" max={lot.available_kg} step="0.1"
                  value={qty[lot.id] ?? ''} onChange={e => setQty({ ...qty, [lot.id]: e.target.value })}
                  style={{ ...inputStyle, flex:1 }}
                />
                <button onClick={() => addToCart(lot)} style={{
                  padding:'8px 14px', borderRadius:6, border:'none', cursor:'pointer', fontSize:12, fontWeight:600, whiteSpace:'nowrap',
                  background: added === lot.id ? '#276749' : inCart(lot.id) ? '#00B3F0' : '#1D60AE', color:'white',
                }}>
                  {added === lot.id ? 'Added ✓' : inCart(lot.id) ? 'Update' : 'Add to Cart'}
                </button>
              </div>
              {lot.estimated_expiry && (
                <div style={{ fontSize:11, color:'#9B2C2C', marginTop:8 }}>
                  Best before {new Date(lot.estimated_expiry).toLocaleDateString()}
                </div>
              )}
            </div>
          ))}
          {lots.length === 0 && (
            <div style={{ gridColumn:'1 / -1', background:'white', borderRadius:8, padding:40, textAlign:'center', color:'#a0aec0', border:'1px solid #e2e8f0' }}>
              No lots match your filters right now.
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}
