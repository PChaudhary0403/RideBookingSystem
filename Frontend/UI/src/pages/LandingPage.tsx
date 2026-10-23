import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import './LandingPage.css';

/* ── SVG icons (inline — no extra dep) ── */
const IconShield = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
);
const IconClock = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
  </svg>
);
const IconMap = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>
    <line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
  </svg>
);
const IconUsers = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
);
const IconCar = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M5 17H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h1.5L7 4h10l2.5 3H21a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"/>
    <circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>
  </svg>
);
const IconCheck = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);
const IconArrow = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
  </svg>
);

export default function LandingPage() {
  return (
    <div className="landing">
      <Navbar />

      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="hero" aria-labelledby="hero-heading">
        <div className="hero__bg" aria-hidden="true">
          <div className="hero__blob hero__blob--1" />
          <div className="hero__blob hero__blob--2" />
          <div className="hero__grid" />
        </div>
        <div className="container hero__inner">
          <div className="hero__content">
            <span className="hero__badge">
              <span className="hero__badge-dot" />
              Now available across all cities
            </span>
            <h1 id="hero-heading" className="hero__heading">
              Your next ride,<br />
              <span className="hero__heading-accent">just a tap away</span>
            </h1>
            <p className="hero__sub">
              Simple, reliable ride booking that connects you with nearby drivers
              and gets you where you need to go — safely and on time.
            </p>
            <div className="hero__ctas">
              <Link to="/register" className="btn btn-primary btn-lg hero__btn-primary">
                Book a Ride <IconArrow />
              </Link>
              <Link to="/driver/register" className="btn btn-secondary btn-lg">
                Become a Driver
              </Link>
            </div>
            <div className="hero__trust">
              {['Safe &amp; Verified Drivers', 'Real-time Tracking', 'Instant Booking'].map(t => (
                <span key={t} className="hero__trust-item">
                  <IconCheck /> <span dangerouslySetInnerHTML={{__html: t}} />
                </span>
              ))}
            </div>
          </div>
          <div className="hero__visual" aria-hidden="true">
            <div className="hero__phone">
              <div className="hero__phone-notch" />
              <div className="hero__map-preview">
                {/* Stylised map UI */}
                <div className="hero__map-bg" />
                <div className="hero__map-road hero__map-road--h" />
                <div className="hero__map-road hero__map-road--v" />
                <div className="hero__map-road hero__map-road--d" />
                <div className="hero__pin hero__pin--pickup">
                  <div className="hero__pin-dot" />
                  <div className="hero__pin-label">Pickup</div>
                </div>
                <div className="hero__pin hero__pin--dest">
                  <div className="hero__pin-dot hero__pin-dot--dest" />
                  <div className="hero__pin-label">Destination</div>
                </div>
                <div className="hero__car-icon">
                  <IconCar />
                </div>
              </div>
              <div className="hero__phone-card">
                <div className="hero__phone-card-row">
                  <div>
                    <div className="hero__phone-card-label">Driver arriving in</div>
                    <div className="hero__phone-card-value">3 min</div>
                  </div>
                  <div className="hero__phone-card-avatar">
                    <span>RB</span>
                  </div>
                </div>
                <div className="hero__phone-card-bar">
                  <div className="hero__phone-card-progress" />
                </div>
              </div>
            </div>
            {/* Floating stat cards */}
            <div className="hero__stat hero__stat--drivers">
              <span className="hero__stat-num">500+</span>
              <span className="hero__stat-label">Active Drivers</span>
            </div>
            <div className="hero__stat hero__stat--rating">
              <span className="hero__stat-num">4.9 ★</span>
              <span className="hero__stat-label">Avg Rating</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────── */}
      <section id="features" className="section features" aria-labelledby="features-heading">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Why RideBook</span>
            <h2 id="features-heading" className="section-title">
              Everything you need for a great ride
            </h2>
            <p className="section-sub">
              Built with reliability and simplicity at its core.
            </p>
          </div>
          <div className="features__grid">
            {[
              {
                icon: <IconShield />,
                color: 'blue',
                title: 'Verified Drivers',
                desc: 'Every driver on the platform is registered and verified before taking their first ride.',
              },
              {
                icon: <IconClock />,
                color: 'green',
                title: 'Real-time Matching',
                desc: 'Get matched with available nearby drivers instantly and track their arrival live.',
              },
              {
                icon: <IconMap />,
                color: 'purple',
                title: 'Live Tracking',
                desc: 'Follow your ride on a live map from pickup to destination with WebSocket-powered updates.',
              },
              {
                icon: <IconUsers />,
                color: 'orange',
                title: 'Dual Experience',
                desc: 'Separate, purpose-built flows for riders and drivers — each optimised for their role.',
              },
            ].map(f => (
              <div key={f.title} className={`feature-card feature-card--${f.color}`}>
                <div className="feature-card__icon">{f.icon}</div>
                <h3 className="feature-card__title">{f.title}</h3>
                <p className="feature-card__desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ─────────────────────────────────── */}
      <section id="how-it-works" className="section how-it-works" aria-labelledby="how-heading">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">How It Works</span>
            <h2 id="how-heading" className="section-title">Ready in four simple steps</h2>
          </div>
          <div className="steps">
            {[
              { num: '01', title: 'Create an account', desc: 'Sign up in under a minute — just your name, email and password.' },
              { num: '02', title: 'Request a ride', desc: 'Enter your pickup and destination. We\'ll show you available drivers nearby.' },
              { num: '03', title: 'Get matched', desc: 'A driver accepts your request and you can track them live on the map.' },
              { num: '04', title: 'Arrive safely', desc: 'Your driver takes you to your destination. Rate the ride when done.' },
            ].map((s, i) => (
              <div key={s.num} className="step">
                <div className="step__line" aria-hidden="true">
                  <span className="step__num">{s.num}</span>
                  {i < 3 && <div className="step__connector" />}
                </div>
                <h3 className="step__title">{s.title}</h3>
                <p className="step__desc">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Rider / Driver cards ──────────────────────────── */}
      <section className="section-sm entry-section" aria-labelledby="entry-heading">
        <div className="container">
          <h2 id="entry-heading" className="section-title" style={{textAlign:'center', marginBottom:'var(--space-10)'}}>
            Choose your role
          </h2>
          <div className="entry-grid">
            {/* Rider card */}
            <div className="entry-card entry-card--rider">
              <div className="entry-card__content">
                <div className="entry-card__icon-wrap entry-card__icon-wrap--blue">
                  <IconUsers />
                </div>
                <h3 className="entry-card__title">I'm a Rider</h3>
                <p className="entry-card__desc">
                  Create your account and start booking rides with verified drivers across the city.
                </p>
                <ul className="entry-card__list">
                  <li><IconCheck /> Instant booking</li>
                  <li><IconCheck /> Live driver tracking</li>
                  <li><IconCheck /> Ride history</li>
                </ul>
                <div className="entry-card__ctas">
                  <Link to="/register" className="btn btn-primary btn-lg" style={{width:'100%', justifyContent:'center'}}>
                    Create Rider Account
                  </Link>
                  <Link to="/login" className="btn btn-ghost btn-sm" style={{justifyContent:'center'}}>
                    Already have an account? Sign in
                  </Link>
                </div>
              </div>
            </div>

            {/* Driver card */}
            <div className="entry-card entry-card--driver">
              <div className="entry-card__content">
                <div className="entry-card__icon-wrap entry-card__icon-wrap--green">
                  <IconCar />
                </div>
                <h3 className="entry-card__title">I'm a Driver</h3>
                <p className="entry-card__desc">
                  Join the platform, register your vehicle, and start accepting ride requests today.
                </p>
                <ul className="entry-card__list">
                  <li><IconCheck /> Flexible hours</li>
                  <li><IconCheck /> Easy ride management</li>
                  <li><IconCheck /> Trip request notifications</li>
                </ul>
                <div className="entry-card__ctas">
                  <Link to="/driver/register" className="btn btn-accent btn-lg" style={{width:'100%', justifyContent:'center'}}>
                    Register as Driver
                  </Link>
                  <Link to="/driver/login" className="btn btn-ghost btn-sm" style={{justifyContent:'center'}}>
                    Already a driver? Sign in
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────── */}
      <footer className="footer" role="contentinfo">
        <div className="container footer__inner">
          <div className="footer__brand">
            <span className="footer__logo">
              <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
                <rect width="32" height="32" rx="8" fill="var(--brand-600)" />
                <path d="M8 21c0-4.418 3.582-8 8-8s8 3.582 8 8" stroke="#fff" strokeWidth="2" strokeLinecap="round"/>
                <circle cx="11" cy="22" r="2" fill="#fff"/>
                <circle cx="21" cy="22" r="2" fill="#fff"/>
              </svg>
              <span>RideBook</span>
            </span>
            <p>Simple, reliable ride booking.</p>
          </div>
          <nav className="footer__links" aria-label="Footer navigation">
            <div className="footer__col">
              <span className="footer__col-heading">Riders</span>
              <Link to="/register">Create Account</Link>
              <Link to="/login">Sign In</Link>
            </div>
            <div className="footer__col">
              <span className="footer__col-heading">Drivers</span>
              <Link to="/driver/register">Join as Driver</Link>
              <Link to="/driver/login">Driver Sign In</Link>
            </div>
          </nav>
        </div>
        <div className="footer__bottom">
          <div className="container">
            <span>© {new Date().getFullYear()} RideBook. All rights reserved.</span>
            <span className="footer__bottom-right">Built with React + FastAPI</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
