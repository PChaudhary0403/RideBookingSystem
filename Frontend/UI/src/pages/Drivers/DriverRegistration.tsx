import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../../components/AuthLayout';

interface FormState { name: string; email: string; phone: string; password: string; confirm: string; }
interface Errors { name?: string; email?: string; phone?: string; password?: string; confirm?: string; api?: string; }

export default function DriverRegistration() {
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>({ name: '', email: '', phone: '', password: '', confirm: '' });
  const [errors, setErrors] = useState<Errors>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const set = (k: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(f => ({ ...f, [k]: e.target.value }));
    setErrors(er => ({ ...er, [k]: undefined, api: undefined }));
  };

  function validate(): boolean {
    const err: Errors = {};
    if (!form.name.trim())   err.name     = 'Full name is required.';
    if (!form.email.trim() || !/^\S+@\S+\.\S+$/.test(form.email)) err.email = 'A valid email is required.';
    if (!form.phone.trim() || !/^\d{10}$/.test(form.phone.replace(/\D/g, ''))) err.phone = 'Enter a valid 10-digit phone number.';
    if (form.password.length < 6) err.password = 'Password must be at least 6 characters.';
    if (form.password !== form.confirm) err.confirm = 'Passwords do not match.';
    setErrors(err);
    return Object.keys(err).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/drivers/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: form.name, email: form.email, phone: form.phone, password: form.password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setErrors({ api: data.detail || 'Registration failed. Please try again.' });
      } else {
        setSuccess(true);
        setTimeout(() => navigate('/driver/login'), 1800);
      }
    } catch {
      setErrors({ api: 'Network error. Please check your connection.' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Join as a Driver"
      subtitle="Register your account and start accepting rides."
      backTo={{ href: '/', label: 'Back to home' }}
      footerText="Already a driver?"
      footerLink={{ href: '/driver/login', label: 'Sign in' }}
      variant="driver"
    >
      {success ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-8) 0' }}>
          <div style={{
            width: 56, height: 56, background: '#d1fae5', borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto var(--space-4)'
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent-600)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
          </div>
          <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--gray-900)', marginBottom: 'var(--space-2)' }}>Welcome aboard!</h2>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)' }}>Account created. Redirecting to sign in…</p>
        </div>
      ) : (
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
            <label htmlFor="drv-name" className="form-label">Full Name</label>
            <input id="drv-name" className={`form-input${errors.name ? ' error' : ''}`} type="text"
              placeholder="Your full name" value={form.name} onChange={set('name')}
              autoComplete="name" aria-describedby={errors.name ? 'drv-name-err' : undefined}/>
            {errors.name && <span id="drv-name-err" className="form-error" role="alert">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="drv-email" className="form-label">Email Address</label>
            <input id="drv-email" className={`form-input${errors.email ? ' error' : ''}`} type="email"
              placeholder="driver@example.com" value={form.email} onChange={set('email')}
              autoComplete="email" aria-describedby={errors.email ? 'drv-email-err' : undefined}/>
            {errors.email && <span id="drv-email-err" className="form-error" role="alert">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="drv-phone" className="form-label">Phone Number</label>
            <input id="drv-phone" className={`form-input${errors.phone ? ' error' : ''}`} type="tel"
              placeholder="9876543210" value={form.phone} onChange={set('phone')}
              autoComplete="tel" inputMode="numeric" aria-describedby={errors.phone ? 'drv-phone-err' : undefined}/>
            {errors.phone && <span id="drv-phone-err" className="form-error" role="alert">{errors.phone}</span>}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div className="form-group">
              <label htmlFor="drv-pwd" className="form-label">Password</label>
              <input id="drv-pwd" className={`form-input${errors.password ? ' error' : ''}`} type="password"
                placeholder="Min 6 characters" value={form.password} onChange={set('password')}
                autoComplete="new-password" aria-describedby={errors.password ? 'drv-pwd-err' : undefined}/>
              {errors.password && <span id="drv-pwd-err" className="form-error" role="alert">{errors.password}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="drv-confirm" className="form-label">Confirm</label>
              <input id="drv-confirm" className={`form-input${errors.confirm ? ' error' : ''}`} type="password"
                placeholder="Repeat password" value={form.confirm} onChange={set('confirm')}
                autoComplete="new-password" aria-describedby={errors.confirm ? 'drv-confirm-err' : undefined}/>
              {errors.confirm && <span id="drv-confirm-err" className="form-error" role="alert">{errors.confirm}</span>}
            </div>
          </div>

          <button
            type="submit"
            className={`btn btn-accent btn-lg${loading ? ' btn-loading' : ''}`}
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: 'var(--space-2)' }}
          >
            {loading ? 'Creating account…' : 'Create Driver Account'}
          </button>
        </form>
      )}
    </AuthLayout>
  );
}