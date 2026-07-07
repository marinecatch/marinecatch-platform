import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login      from './pages/Login';
import Dashboard  from './pages/Dashboard';
import Inventory  from './pages/Inventory';
import Orders     from './pages/Orders';
import Analytics  from './pages/Analytics';
import Users      from './pages/Users';
import Payments   from './pages/Payments';
import Payouts    from './pages/Payouts';
import Logistics  from './pages/Logistics';
import Settlement from './pages/Settlement';
import CEO from './pages/CEO';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'100vh',color:'#718096'}}>Loading...</div>;
  if (!user)   return <Navigate to="/login" replace />;
  return children;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/"          element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/inventory" element={<ProtectedRoute><Inventory /></ProtectedRoute>} />
          <Route path="/orders"    element={<ProtectedRoute><Orders /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
          <Route path="/users"     element={<ProtectedRoute><Users /></ProtectedRoute>} />
          <Route path="/payments"  element={<ProtectedRoute><Payments /></ProtectedRoute>} />
          <Route path="/payouts"   element={<ProtectedRoute><Payouts /></ProtectedRoute>} />
          <Route path="/logistics" element={<ProtectedRoute><Logistics /></ProtectedRoute>} />
          <Route path="/settlement"element={<ProtectedRoute><Settlement /></ProtectedRoute>} />
          <Route path="/ceo"       element={<ProtectedRoute><CEO /></ProtectedRoute>} />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;