// src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { register as apiRegister } from '../services/api';

export default function Login() {
  const [mode, setMode]         = useState('login');
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [name, setName]         = useState('');
  const [phone, setPhone]       = useState('');
  const [businessName, setBusinessName] = useState('');
  const [location, setLocation] = useState('');
  const [error, setError]       = useState('');
  const [info, setInfo]         = useState('');
  const [loading, setLoading]   = useState(false);
  const { login }               = useAuth();
  const navigate                = useNavigate();

  const inputStyle = { width:'100%', padding:'10px 14px', borderRadius:8, border:'1px solid #e2e8f0', fontSize:14, marginBottom:12, boxSizing:'border-box' };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(''); setInfo(''); setLoading(true);
    try {
      await apiRegister({ name, email, phone, password, role: 'buyer', business_name: businessName, location });
      setInfo('Account created — you can now log in below.');
      setMode('login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create account. Check your details and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center', background:'linear-gradient(135deg, #0D2137 0%, #1D60AE 100%)', padding:20 }}>
      <div style={{ background:'white', borderRadius:12, padding:'40px 36px', width:420, maxWidth:'100%' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:8 }}>
          <img src="/src/assets/logo.png" alt="MarineCatch Africa" style={{ height:32 }} />
        </div>
        <div style={{ fontSize:13, color:'#718096', marginBottom:24 }}>Buyer Portal — Hotels, Restaurants & Wholesalers</div>

        {error && <div style={{ background:'#fed7d7', color:'#9b2c2c', padding:'10px 14px', borderRadius:8, fontSize:13, marginBottom:16 }}>{error}</div>}
        {info && <div style={{ background:'#c6f6d5', color:'#276749', padding:'10px 14px', borderRadius:8, fontSize:13, marginBottom:16 }}>{info}</div>}

        {mode === 'login' ? (
          <form onSubmit={handleLogin}>
            <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required style={inputStyle} />
            <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required style={inputStyle} />
            <button type="submit" disabled={loading} style={{ width:'100%', padding:'12px', borderRadius:8, border:'none', background:'#1D60AE', color:'white', fontWeight:600, fontSize:14, cursor:'pointer' }}>
              {loading ? 'Logging in...' : 'Log In'}
            </button>
            <div style={{ textAlign:'center', marginTop:16, fontSize:13, color:'#718096' }}>
              New here? <button type="button" onClick={() => { setMode('register'); setError(''); }} style={{ background:'none', border:'none', color:'#1D60AE', fontWeight:600, cursor:'pointer' }}>Create an account</button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleRegister}>
            <input placeholder="Your name" value={name} onChange={e => setName(e.target.value)} required style={inputStyle} />
            <input placeholder="Business name (hotel, restaurant, etc.)" value={businessName} onChange={e => setBusinessName(e.target.value)} style={inputStyle} />
            <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required style={inputStyle} />
            <input placeholder="Phone (e.g. 2547XXXXXXXX)" value={phone} onChange={e => setPhone(e.target.value)} required style={inputStyle} />
            <input placeholder="Delivery location / city" value={location} onChange={e => setLocation(e.target.value)} style={inputStyle} />
            <input type="password" placeholder="Password (min 8 chars, letters + numbers)" value={password} onChange={e => setPassword(e.target.value)} required style={inputStyle} />
            <button type="submit" disabled={loading} style={{ width:'100%', padding:'12px', borderRadius:8, border:'none', background:'#1D60AE', color:'white', fontWeight:600, fontSize:14, cursor:'pointer' }}>
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
            <div style={{ textAlign:'center', marginTop:16, fontSize:13, color:'#718096' }}>
              Already have an account? <button type="button" onClick={() => { setMode('login'); setError(''); }} style={{ background:'none', border:'none', color:'#1D60AE', fontWeight:600, cursor:'pointer' }}>Log in</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
