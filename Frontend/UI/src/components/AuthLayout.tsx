import { Link } from 'react-router-dom';

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  backTo?: { href: string; label: string };
  footerText?: string;
  footerLink?: { href: string; label: string };
  variant?: 'rider' | 'driver';
}

export default function AuthLayout({
  title, subtitle, children, backTo, footerText, footerLink, variant = 'rider'
}: AuthLayoutProps) {
  return (
    <div className="auth-page" style={{ background: variant === 'driver' ? 'linear-gradient(135deg, #064e3b 0%, #065f46 100%)' : 'var(--gray-50)' }}>
      {backTo && (
        <Link
          to={backTo.href}
          className="auth-back"
          style={{
            position: 'fixed', top: '1rem', left: '1.25rem',
            display: 'flex', alignItems: 'center', gap: '6px',
            fontSize: 'var(--font-size-sm)', fontWeight: 600,
            color: variant === 'driver' ? 'rgba(255,255,255,.8)' : 'var(--gray-600)',
            zIndex: 10, textDecoration: 'none',
          }}
          aria-label={backTo.label}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          {backTo.label}
        </Link>
      )}

      <div className="auth-card">
        {/* Header */}
        <div style={{ marginBottom: 'var(--space-8)' }}>
          <Link
            to="/"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-6)', textDecoration: 'none' }}
            aria-label="RideBook home"
          >
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <rect width="32" height="32" rx="8" fill={variant === 'driver' ? 'var(--accent-500)' : 'var(--brand-600)'} />
              <path d="M8 21c0-4.418 3.582-8 8-8s8 3.582 8 8" stroke="#fff" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="11" cy="22" r="2" fill="#fff"/>
              <circle cx="21" cy="22" r="2" fill="#fff"/>
            </svg>
            <span style={{ fontWeight: 800, fontSize: 'var(--font-size-xl)', color: 'var(--gray-900)', letterSpacing: '-0.3px' }}>RideBook</span>
          </Link>
          <h1 style={{
            fontSize: 'var(--font-size-2xl)',
            fontWeight: 800,
            color: 'var(--gray-900)',
            letterSpacing: '-0.3px',
            marginBottom: 'var(--space-2)'
          }}>
            {title}
          </h1>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--gray-500)' }}>{subtitle}</p>
        </div>

        {/* Form content */}
        {children}

        {/* Footer link */}
        {footerText && footerLink && (
          <p style={{
            marginTop: 'var(--space-6)',
            textAlign: 'center',
            fontSize: 'var(--font-size-sm)',
            color: 'var(--gray-500)'
          }}>
            {footerText}{' '}
            <Link
              to={footerLink.href}
              style={{ color: variant === 'driver' ? 'var(--accent-600)' : 'var(--brand-600)', fontWeight: 600 }}
            >
              {footerLink.label}
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}
