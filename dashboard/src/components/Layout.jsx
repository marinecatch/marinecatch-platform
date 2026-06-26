// src/components/Layout.jsx
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, Package, Fish, CreditCard,
  Wallet, Users, Truck, BarChart2, LogOut, Waves, ArrowLeftRight
} from 'lucide-react';

// Brand colors from MarineCatch Africa brand book
const BRAND = {
  navBg:      '#0D2137',  // Deep navy — sidebar
  navActive:  '#1D60AE',  // Safety Blue — active item
  navHover:   'rgba(29,96,174,0.15)',
  accent:     '#00B3F0',  // Cyan accent
  text:       '#F7FAFC',
  textMuted:  'rgba(247,250,252,0.55)',
  mainBg:     '#F4F7FB',
  white:      '#FFFFFF',
  border:     '#E2E8F0',
  heading:    '#0D2137',
};

const navSections = [
  {
    label: 'Operations',
    items: [
      { path: '/',          label: 'Dashboard',     icon: LayoutDashboard },
      { path: '/inventory', label: 'Inventory',     icon: Fish },
      { path: '/orders',    label: 'Orders',        icon: Package },
    ]
  },
  {
    label: 'Finance',
    items: [
      { path: '/payments',  label: 'Payments',      icon: CreditCard },
      { path: '/payouts',   label: 'Fisher Payouts',icon: Wallet },
      { path: '/settlement', label: 'Settlement',      icon: ArrowLeftRight },
    ]
  },
  {
    label: 'Intelligence',
    items: [
      { path: '/analytics', label: 'Analytics',     icon: BarChart2 },
    ]
  },
  {
    label: 'Network',
    items: [
      { path: '/users',     label: 'Users',         icon: Users },
      { path: '/logistics', label: 'Logistics',     icon: Truck },
    ]
  },
];

export default function Layout({ children, title, subtitle }) {
  const { user, logout } = useAuth();
  const location         = useLocation();
  const navigate         = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div style={{ display:'flex', minHeight:'100vh', fontFamily:'"Renault", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif', background:BRAND.mainBg }}>

      {/* Sidebar */}
      <aside style={{ width:230, background:BRAND.navBg, color:BRAND.text, display:'flex', flexDirection:'column', flexShrink:0, boxShadow:'2px 0 8px rgba(0,0,0,0.15)' }}>

        {/* Logo */}
        <div style={{ padding:'24px 20px 20px', borderBottom:`1px solid rgba(255,255,255,0.08)` }}>
          <div style={{ display:'flex', alignItems:'center', gap:10 }}>
            <img src="/src/assets/logo.png" alt="MarineCatch Africa" style={{ height:36, objectFit:'contain', filter:'brightness(0) invert(1)' }} />
          </div>
        </div>

        {/* Nav */}
        <nav style={{ flex:1, padding:'16px 12px', overflowY:'auto' }}>
          {navSections.map(section => (
            <div key={section.label} style={{ marginBottom:20 }}>
              <div style={{ fontSize:10, color:BRAND.textMuted, textTransform:'uppercase', letterSpacing:1.5, padding:'0 8px', marginBottom:6, fontWeight:600 }}>
                {section.label}
              </div>
              {section.items.map(({ path, label, icon: Icon }) => {
                const active = location.pathname === path;
                return (
                  <Link key={path} to={path} style={{
                    display:'flex', alignItems:'center', gap:10,
                    padding:'9px 10px', borderRadius:7, marginBottom:2,
                    color: active ? BRAND.text : BRAND.textMuted,
                    background: active ? BRAND.navActive : 'transparent',
                    textDecoration:'none', fontSize:13.5, fontWeight: active ? 600 : 400,
                    transition:'all 0.15s ease',
                  }}
                  onMouseEnter={e => !active && (e.currentTarget.style.background = BRAND.navHover)}
                  onMouseLeave={e => !active && (e.currentTarget.style.background = 'transparent')}
                  >
                    <Icon size={16} strokeWidth={active ? 2.5 : 2} />
                    {label}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        {/* User + logout */}
        <div style={{ padding:'16px 12px', borderTop:`1px solid rgba(255,255,255,0.08)` }}>
          <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:12 }}>
            <img src="/src/assets/logo.png" alt="MarineCatch Africa" style={{ height:36, objectFit:'contain', mixBlendMode:'screen' }} />
            <div>
              <div style={{ fontSize:13, fontWeight:600, color:BRAND.text }}>{user?.name || 'Admin'}</div>
              <div style={{ fontSize:11, color:BRAND.textMuted }}>{user?.role || 'admin'}</div>
            </div>
          </div>
          <button onClick={handleLogout} style={{
            width:'100%', padding:'8px 12px', background:'transparent',
            border:`1px solid rgba(255,255,255,0.15)`, borderRadius:7,
            color:BRAND.textMuted, cursor:'pointer', fontSize:13,
            display:'flex', alignItems:'center', justifyContent:'center', gap:8,
            transition:'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.35)'; e.currentTarget.style.color = BRAND.text; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)'; e.currentTarget.style.color = BRAND.textMuted; }}
          >
            <LogOut size={14} strokeWidth={2} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex:1, overflow:'auto', display:'flex', flexDirection:'column' }}>

        {/* Top bar */}
        <div style={{ padding:'20px 28px', borderBottom:`1px solid ${BRAND.border}`, background:BRAND.white, display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <div>
            <div style={{ fontSize:20, fontWeight:700, color:BRAND.heading, fontFamily:'"Cinzel", Georgia, serif', letterSpacing:0.3 }}>{title}</div>
            {subtitle && <div style={{ fontSize:13, color:'#718096', marginTop:2 }}>{subtitle}</div>}
          </div>
          <div style={{ fontSize:12, color:'#a0aec0' }}>
            {new Date().toLocaleDateString('en-KE', { weekday:'long', year:'numeric', month:'long', day:'numeric' })}
          </div>
        </div>

        {/* Content */}
        <div style={{ padding:28, flex:1 }}>{children}</div>
      </main>
    </div>
  );
}