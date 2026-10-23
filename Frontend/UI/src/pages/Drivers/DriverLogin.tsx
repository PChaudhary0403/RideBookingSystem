import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../../components/AuthLayout';

export default function DriverLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string; api?: string }>({});
  const [loading, setLoading] = useState(false);

  function validate() {
    const err: typeof errors = {};
    if (!email.trim() || !/^\S+@\S+\.\S+$/.test(email)) err.email = 'Enter a valid email address.';
    if (!password) err.password = 'Password is required.';
    setErrors(err);
    return Object.keys(err).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/drivers/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setErrors({ api: data.detail || 'Invalid email or password.' });
      } else {
        if (data.id) localStorage.setItem('driver_id', String(data.id));
        navigate('/driver/home');
      }
    } catch {
      setErrors({ api: 'Network error. Please check your connection.' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Driver Sign In"
      subtitle="Sign in to start accepting rides."
      backTo={{ href: '/', label: 'Back to home' }}
      footerText="Not a driver yet?"
      footerLink={{ href: '/driver/register', label: 'Register now' }}
      variant="driver"
    >
      <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        {errors.api && (
          <div role="alert" style={{
            background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b',
            borderRadius: 'var(--radius-md)', padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-sm)'
          }}>
            {errors.api}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="drv-login-email" className="form-label">Email Address</label>
          <input id="drv-login-email" className={`form-input${errors.email ? ' error' : ''}`}
            type="email" placeholder="driver@example.com" value={email}
            onChange={e => { setEmail(e.target.value); setErrors(er => ({ ...er, email: undefined, api: undefined })); }}
            autoComplete="email" aria-describedby={errors.email ? 'drv-login-email-err' : undefined} />
          {errors.email && <span id="drv-login-email-err" className="form-error" role="alert">{errors.email}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="drv-login-pwd" className="form-label">Password</label>
          <input id="drv-login-pwd" className={`form-input${errors.password ? ' error' : ''}`}
            type="password" placeholder="Your password" value={password}
            onChange={e => { setPassword(e.target.value); setErrors(er => ({ ...er, password: undefined, api: undefined })); }}
            autoComplete="current-password" aria-describedby={errors.password ? 'drv-login-pwd-err' : undefined} />
          {errors.password && <span id="drv-login-pwd-err" className="form-error" role="alert">{errors.password}</span>}
        </div>

        <button
          type="submit"
          className={`btn btn-accent btn-lg${loading ? ' btn-loading' : ''}`}
          disabled={loading}
          style={{ width: '100%', justifyContent: 'center', marginTop: 'var(--space-2)' }}
        >
          {loading ? 'Signing in…' : 'Sign In as Driver'}
        </button>

        <p style={{ textAlign: 'center', fontSize: 'var(--font-size-sm)', color: 'var(--gray-500)', marginTop: 'var(--space-2)' }}>
          Looking to book a ride?{' '}
          <a href="/login" style={{ color: 'var(--brand-600)', fontWeight: 600 }}>Rider sign in</a>
        </p>
      </form>
    </AuthLayout>
  );
}