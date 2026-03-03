import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import { login } from '../api';

export default function LoginPage() {
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { signIn } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const from = location.state?.from?.pathname || '/';

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const res = await login(password);
            signIn(res.data.access_token);
            navigate(from, { replace: true });
        } catch {
            setError('Wrong password. Try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-bg">
            <div className="login-box card">
                <h1>🏢 Building Bills</h1>
                <p className="sub">Sign in to manage monthly utility bills</p>
                <form onSubmit={handleSubmit}>
                    <div className="field">
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password..."
                            autoFocus
                        />
                    </div>
                    {error && <p className="error-msg">{error}</p>}
                    <button className="btn btn-primary w-full mt-3" type="submit" disabled={loading}>
                        {loading ? 'Signing in…' : 'Sign In'}
                    </button>
                </form>
            </div>
        </div>
    );
}
