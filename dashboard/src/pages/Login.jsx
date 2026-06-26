// src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Waves, Mail, Lock, ArrowRight } from 'lucide-react';

export default function Login() {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);
  const { login }               = useAuth();
  const navigate                = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch {
      setError('Invalid email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight:'100vh', display:'flex',
      background:'linear-gradient(135deg, #0D2137 0%, #1D60AE 100%)',
    }}>
      {/* Left panel — branding */}
      <div style={{ flex:1, display:'flex', flexDirection:'column', justifyContent:'center', padding:'60px 80px', color:'white' }}>
        <div style={{ display:'flex', alignItems:'center', gap:14, marginBottom:48 }}>
          <img src="/src/assets/logo.png" alt="MarineCatch Africa" style={{ height:70, objectFit:'contain', mixBlendMode:'screen' }} />
        </div>
        <div style={{ fontSize:36, fontWeight:700, fontFamily:'"Cinzel", Georgia, serif', lineHeight:1.3, marginBottom:16 }}>
          Seafood Supply Chain<br/>Infrastructure
        </div>
        <div style={{ fontSize:15, opacity:0.7, lineHeight:1.8, maxWidth:400 }}>
          Digital infrastructure for African seafood trade — connecting fishers, buyers, processors and exporters across the blue economy.
        </div>
        <div style={{ marginTop:48, display:'flex', gap:32 }}>
          {[['18+', 'Tables'], ['34', 'BMU Records'], ['7', 'Landing Sites']].map(([val, lbl]) => (
            <div key={lbl}>
              <div style={{ fontSize:28, fontWeight:700, color:'#00B3F0' }}>{val}</div>
              <div style={{ fontSize:12, opacity:0.6, marginTop:2 }}>{lbl}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — login form */}
      <div style={{ width:480, background:'white', display:'flex', alignItems:'center', justifyContent:'center', padding:48 }}>
        <div style={{ width:'100%', maxWidth:360 }}>
          <div style={{ fontSize:22, fontWeight:700, color:'#0D2137', marginBottom:6, fontFamily:'"Cinzel", Georgia, serif' }}>
            Operations Login
          </div>
          <div style={{ fontSize:13, color:'#718096', marginBottom:32 }}>
            Sign in to the MarineCatch operations dashboard
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom:16 }}>
              <label style={{ display:'block', fontSize:12, fontWeight:600, marginBottom:6, color:'#4a5568', textTransform:'uppercase', letterSpacing:0.5 }}>Email</label>
              <div style={{ position:'relative' }}>
                <Mail size={16} color="#a0aec0" style={{ position:'absolute', left:12, top:'50%', transform:'translateY(-50%)' }} />
                <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                  style={{ width:'100%', padding:'11px 12px 11px 38px', border:'1px solid #e2e8f0', borderRadius:8, fontSize:14, boxSizing:'border-box', outline:'none' }}
                  placeholder="admin@marinecatch.co.ke" required />
              </div>
            </div>

            <div style={{ marginBottom:24 }}>
              <label style={{ display:'block', fontSize:12, fontWeight:600, marginBottom:6, color:'#4a5568', textTransform:'uppercase', letterSpacing:0.5 }}>Password</label>
              <div style={{ position:'relative' }}>
                <Lock size={16} color="#a0aec0" style={{ position:'absolute', left:12, top:'50%', transform:'translateY(-50%)' }} />
                <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                  style={{ width:'100%', padding:'11px 12px 11px 38px', border:'1px solid #e2e8f0', borderRadius:8, fontSize:14, boxSizing:'border-box', outline:'none' }}
                  placeholder="Password" required />
              </div>
            </div>

            {error && (
              <div style={{ background:'#FFF5F5', border:'1px solid #FED7D7', color:'#C53030', padding:'10px 14px', borderRadius:8, fontSize:13, marginBottom:16 }}>
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} style={{
              width:'100%', padding:'12px', background: loading ? '#a0aec0' : '#1D60AE',
              color:'white', border:'none', borderRadius:8, fontSize:14, fontWeight:600,
              cursor: loading ? 'not-allowed' : 'pointer',
              display:'flex', alignItems:'center', justifyContent:'center', gap:8,
              transition:'background 0.2s',
            }}>
              {loading ? 'Signing in...' : <>Sign In <ArrowRight size={16} /></>}
            </button>
          </form>

          <div style={{ marginTop:32, paddingTop:24, borderTop:'1px solid #e2e8f0', fontSize:12, color:'#a0aec0', textAlign:'center' }}>
            MarineCatch Africa © 2026 · Kwale County, Kenya
          </div>
        </div>
      </div>
    </div>
  );
}