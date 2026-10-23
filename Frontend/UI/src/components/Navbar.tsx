import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const { pathname } = useLocation();
  const isHome = pathname === '/';

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 16);
    window.addEventListener('scroll', handler, { passive: true });
    return () => window.removeEventListener('scroll', handler);
  }, []);

  // Close menu on route change
  useEffect(() => setMenuOpen(false), [pathname]);

  const scrollTo = (id: string) => {
    setMenuOpen(false);
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <header className={`navbar ${scrolled || !isHome ? 'navbar--solid' : 'navbar--transparent'}`}>
      <nav className="container navbar__inner" aria-label="Main navigation">
        {/* Logo */}
        <Link to="/" className="navbar__logo" aria-label="RideBook home">
          <span className="navbar__logo-icon" aria-hidden="true">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="var(--brand-600)" />
              <path d="M8 21c0-4.418 3.582-8 8-8s8 3.582 8 8" stroke="#fff" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="11" cy="22" r="2" fill="#fff"/>
              <circle cx="21" cy="22" r="2" fill="#fff"/>
              <path d="M16 13V9M13 10.5l3-3 3 3" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </span>
          <span className="navbar__logo-text">RideBook</span>
        </Link>

        {/* Desktop links */}
        <div className="navbar__links" role="list">
          {isHome && (
            <>
              <button className="navbar__link" onClick={() => scrollTo('how-it-works')} role="listitem">
                How It Works
              </button>
              <button className="navbar__link" onClick={() => scrollTo('features')} role="listitem">
                Features
              </button>
            </>
          )}
          <Link to="/driver/register" className="navbar__link" role="listitem">
            Drive with Us
          </Link>
        </div>

        {/* Desktop CTAs */}
        <div className="navbar__ctas">
          <Link to="/login" className="btn btn-ghost btn-sm">Sign In</Link>
          <Link to="/register" className="btn btn-primary btn-sm">Book a Ride</Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className={`navbar__hamburger ${menuOpen ? 'open' : ''}`}
          onClick={() => setMenuOpen(o => !o)}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
        >
          <span /><span /><span />
        </button>
      </nav>

      {/* Mobile drawer */}
      {menuOpen && (
        <div className="navbar__drawer" role="dialog" aria-label="Mobile navigation">
          {isHome && (
            <>
              <button className="navbar__drawer-link" onClick={() => scrollTo('how-it-works')}>
                How It Works
              </button>
              <button className="navbar__drawer-link" onClick={() => scrollTo('features')}>
                Features
              </button>
            </>
          )}
          <Link to="/driver/register" className="navbar__drawer-link">Drive with Us</Link>
          <hr className="navbar__drawer-divider" />
          <Link to="/login" className="btn btn-secondary" style={{width:'100%', justifyContent:'center'}}>
            Sign In
          </Link>
          <Link to="/register" className="btn btn-primary" style={{width:'100%', justifyContent:'center'}}>
            Book a Ride
          </Link>
        </div>
      )}
    </header>
  );
}
