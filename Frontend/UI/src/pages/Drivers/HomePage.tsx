import { useNavigate } from 'react-router-dom';
import './DriverHome.css';

const IconCar = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M5 17H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h1.5L7 4h10l2.5 3H21a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"/>
    <circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>
  </svg>
);
const IconMap = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>
    <line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
  </svg>
);
const IconList = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
    <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
  </svg>
);
const IconPlus = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);
const IconLogout = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
);

export default function DriverHomePage() {
  const navigate = useNavigate();
  const driverId = localStorage.getItem('driver_id') ?? '—';

  async function handleLogout() {
    try {
      await fetch(`${import.meta.env.VITE_API_URL}/drivers/logout`, {
        method: 'POST', credentials: 'include'
      });
    } finally {
      localStorage.removeItem('driver_id');
      navigate('/driver/login');
    }
  }

  const actions = [
    {
      id: 'go-online',
      icon: <IconMap />,
      title: 'Go Online',
      desc: 'Open the live map to receive and manage ride requests.',
      color: 'green',
      onClick: () => navigate('/driver/maps'),
    },
    {
      id: 'register-vehicle',
      icon: <IconPlus />,
      title: 'Register Vehicle',
      desc: 'Add a new vehicle to your profile to start accepting rides.',
      color: 'blue',
      onClick: () => navigate('/vehicle/select'),
    },
    {
      id: 'my-vehicles',
      icon: <IconCar />,
      title: 'My Vehicles',
      desc: 'View and manage all vehicles registered under your account.',
      color: 'slate',
      onClick: () => navigate('/driver/vehicles'),
    },
    {
      id: 'trip-requests',
      icon: <IconList />,
      title: 'Trip Requests',
      desc: 'View pending trip requests from nearby riders waiting for pickup.',
      color: 'purple',
      onClick: () => navigate('/driver/maps'),
    },
  ];

  return (
    <div className="driver-home">
      {/* Top bar */}
      <header className="driver-home__topbar">
        <div className="container driver-home__topbar-inner">
          <div className="driver-home__brand">
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
              <rect width="32" height="32" rx="8" fill="var(--accent-500)" />
              <path d="M8 21c0-4.418 3.582-8 8-8s8 3.582 8 8" stroke="#fff" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="11" cy="22" r="2" fill="#fff"/><circle cx="21" cy="22" r="2" fill="#fff"/>
            </svg>
            <span>RideBook <span style={{ color: 'var(--accent-500)', fontWeight: 700 }}>Driver</span></span>
          </div>
          <div className="driver-home__topbar-right">
            <div className="driver-home__id-badge">Driver #{driverId}</div>
            <button className="btn btn-ghost btn-sm" onClick={handleLogout} aria-label="Sign out">
              <IconLogout /> Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="container driver-home__main">
        {/* Welcome */}
        <div className="driver-home__welcome">
          <div>
            <h1 className="driver-home__welcome-title">Driver Dashboard</h1>
            <p className="driver-home__welcome-sub">Manage your rides, vehicles, and availability from one place.</p>
          </div>
          <div className="driver-home__status">
            <span className="driver-home__status-dot" />
            <span>Offline</span>
          </div>
        </div>

        {/* Action grid */}
        <div className="driver-home__grid" role="list">
          {actions.map(a => (
            <button
              key={a.id}
              id={a.id}
              className={`driver-action-card driver-action-card--${a.color}`}
              onClick={a.onClick}
              role="listitem"
              aria-label={a.title}
            >
              <div className="driver-action-card__icon">{a.icon}</div>
              <h2 className="driver-action-card__title">{a.title}</h2>
              <p className="driver-action-card__desc">{a.desc}</p>
              <span className="driver-action-card__arrow" aria-hidden="true">→</span>
            </button>
          ))}
        </div>
      </main>
    </div>
  );
}