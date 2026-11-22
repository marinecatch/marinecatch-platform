// src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import MyCatch from './pages/MyCatch';
import LogCatch from './pages/LogCatch';
import Payments from './pages/Payments';
import Compliance from './pages/Compliance';
import Prices from './pages/Prices';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ textAlign:'center', padding:60, color:'#718096' }}>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/"           element={<ProtectedRoute><MyCatch /></ProtectedRoute>} />
      <Route path="/log-catch"  element={<ProtectedRoute><LogCatch /></ProtectedRoute>} />
      <Route path="/payments"   element={<ProtectedRoute><Payments /></ProtectedRoute>} />
      <Route path="/compliance" element={<ProtectedRoute><Compliance /></ProtectedRoute>} />
      <Route path="/prices"     element={<ProtectedRoute><Prices /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
