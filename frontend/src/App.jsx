import { useState, useContext, createContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import MonthEditor from './pages/MonthEditor';
import './index.css';

// ── Auth context ──────────────────────────────────────────────────
const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'));

  const signIn = (t) => { localStorage.setItem('token', t); setToken(t); };
  const signOut = () => { localStorage.removeItem('token'); setToken(null); };

  return <AuthCtx.Provider value={{ token, signIn, signOut }}>{children}</AuthCtx.Provider>;
}

function RequireAuth({ children }) {
  const { token } = useAuth();
  const location = useLocation();
  if (!token) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}

// ── Top navigation bar ────────────────────────────────────────────
function Topbar() {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  return (
    <header className="topbar">
      <div className="topbar-logo" style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
        🏢 <span>Building</span> Bills
      </div>
      <div className="flex gap-2 items-center">
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/')}>Dashboard</button>
        <button className="btn btn-ghost btn-sm" onClick={signOut}>Sign Out</button>
      </div>
    </header>
  );
}

// ── Toast context ─────────────────────────────────────────────────
const ToastCtx = createContext(null);
export const useToast = () => useContext(ToastCtx);

function ToastProvider({ children }) {
  const [msg, setMsg] = useState(null);

  const toast = (text, type = 'success') => {
    setMsg({ text, type });
    setTimeout(() => setMsg(null), 3000);
  };

  return (
    <ToastCtx.Provider value={toast}>
      {children}
      {msg && (
        <div className={`toast toast-${msg.type}`}>{msg.text}</div>
      )}
    </ToastCtx.Provider>
  );
}

// ── App shell ─────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/*"
              element={
                <RequireAuth>
                  <>
                    <Topbar />
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/month/:year/:month" element={<MonthEditor />} />
                    </Routes>
                  </>
                </RequireAuth>
              }
            />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
