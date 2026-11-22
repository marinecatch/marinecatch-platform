// src/components/Layout.jsx
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { Store, ShoppingCart, Package, FileText, TrendingUp, LogOut } from 'lucide-react';

const BRAND = {
  navBg: '#0D2137', accent: '#00B3F0',
  text: '#F7FAFC', textMuted: 'rgba(247,250,252,0.6)',
  mainBg: '#F4F7FB', heading: '#0D2137',
};

const NAV = [
  { path: '/',          label: 'Marketplace', icon: Store },
  { path: '/cart',      label: 'Cart',        icon: ShoppingCart, cart: true },
  { path: '/orders',    label: 'My Orders',   icon: Package },
  { path: '/lpo',       label: 'LPO Request', icon: FileText },
  { path: '/prices',    label: 'Market Prices', icon: TrendingUp },
];

export default function Layout({ children, title, subtitle }) {
  const { user, logout } = useAuth();
  const { items }        = useCart();
  const location = useLocation();
  const navigate  = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div style={{ minHeight:'100vh', background:BRAND.mainBg, fontFamily:'-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>
      <header style={{ background:BRAND.navBg, color:BRAND.text, padding:'0 24px' }}>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', height:64, maxWidth:1100, margin:'0 auto' }}>
          <div style={{ display:'flex', alignItems:'center', gap:10, fontWeight:700, fontSize:16 }}>
            <img src="/src/assets/logo.png" alt="MarineCatch Africa" style={{ height:28, filter:'brightness(0) invert(1)' }} />
            Buyer Portal
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:16 }}>
            <span style={{ fontSize:13, color:BRAND.textMuted }}>{user?.business_name || user?.name}</span>
            <button onClick={handleLogout} style={{ background:'transparent', border:'none', color:BRAND.textMuted, cursor:'pointer', display:'flex', alignItems:'center', gap:6, fontSize:13 }}>
              <LogOut size={15} /> Log out
            </button>
          </div>
        </div>
        <nav style={{ display:'flex', gap:4, maxWidth:1100, margin:'0 auto', overflowX:'auto' }}>
          {NAV.map(item => {
            const active = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link key={item.path} to={item.path} style={{
                display:'flex', alignItems:'center', gap:6, padding:'10px 16px', fontSize:13, position:'relative',
                color: active ? BRAND.accent : BRAND.textMuted, textDecoration:'none', whiteSpace:'nowrap',
                borderBottom: active ? `2px solid ${BRAND.accent}` : '2px solid transparent', fontWeight: active ? 600 : 400,
              }}>
                <Icon size={15} /> {item.label}
                {item.cart && items.length > 0 && (
                  <span style={{ background:'#9B2C2C', color:'white', borderRadius:10, fontSize:10, padding:'1px 6px', fontWeight:700 }}>
                    {items.length}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </header>

      <main style={{ maxWidth:1100, margin:'0 auto', padding:'28px 24px' }}>
        <div style={{ marginBottom:20 }}>
          <h1 style={{ fontSize:22, fontWeight:700, color:BRAND.heading, margin:0 }}>{title}</h1>
          {subtitle && <div style={{ fontSize:13, color:'#718096', marginTop:4 }}>{subtitle}</div>}
        </div>
        {children}
      </main>
    </div>
  );
}
