import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './DisplayVehicles.css';

interface Vehicle { id: string; name: string; type: string; model: string; mileage: number; color?: string; }

const IconCar = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M5 17H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h1.5L7 4h10l2.5 3H21a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"/>
    <circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>
  </svg>
);

export default function DisplayVehicles() {
  const navigate  = useNavigate();
  const driverId  = localStorage.getItem('driver_id');
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');

  useEffect(() => {
    async function fetchVehicles() {
      setLoading(true);
      try {
        const res  = await fetch(`${import.meta.env.VITE_API_URL}/vehicles/driver-vehicles`, { credentials: 'include' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to load vehicles');
        setVehicles(data.vehicles ?? []);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load vehicles');
      } finally {
        setLoading(false);
      }
    }
    fetchVehicles();
  }, [driverId]);

  return (
    <div className="dv-page">
      {/* Header */}
      <div className="dv-header">
        <div className="container dv-header__inner">
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/driver/home')} aria-label="Back to dashboard">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>
            Dashboard
          </button>
          <div>
            <h1 className="dv-title">My Vehicles</h1>
            <p className="dv-sub">All vehicles registered under your driver account.</p>
          </div>
          <button className="btn btn-accent btn-sm" onClick={() => navigate('/vehicle/select')} style={{ marginLeft: 'auto' }}>
            + Add Vehicle
          </button>
        </div>
      </div>

      <div className="container dv-main">
        {/* Loading skeletons */}
        {loading && (
          <div className="dv-grid" aria-busy="true" aria-label="Loading vehicles">
            {[1, 2, 3].map(i => (
              <div key={i} className="dv-skeleton">
                <div className="skeleton dv-skeleton__icon" />
                <div style={{ flex: 1 }}>
                  <div className="skeleton dv-skeleton__line" style={{ width: '60%' }} />
                  <div className="skeleton dv-skeleton__line" style={{ width: '40%', marginTop: '8px' }} />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="dv-empty" role="alert">
            <div className="dv-empty__icon" style={{ background: '#fef2f2', color: '#ef4444' }}><IconCar /></div>
            <h2 className="dv-empty__title">Failed to Load Vehicles</h2>
            <p className="dv-empty__sub">{error}</p>
            <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry</button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && vehicles.length === 0 && (
          <div className="dv-empty">
            <div className="dv-empty__icon"><IconCar /></div>
            <h2 className="dv-empty__title">No Vehicles Registered</h2>
            <p className="dv-empty__sub">Add your first vehicle to start accepting rides on the platform.</p>
            <button className="btn btn-accent btn-lg" onClick={() => navigate('/vehicle/select')}>Register Your Vehicle</button>
          </div>
        )}

        {/* Vehicle grid */}
        {!loading && !error && vehicles.length > 0 && (
          <div className="dv-grid" role="list">
            {vehicles.map(v => (
              <div key={v.id} className="dv-card" role="listitem">
                <div className="dv-card__icon"><IconCar /></div>
                <div className="dv-card__body">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                    <h2 className="dv-card__name">{v.name || 'Vehicle'}</h2>
                    <span className="badge badge-primary">{v.type}</span>
                  </div>
                  <p className="dv-card__detail">Model: <strong>{v.model}</strong></p>
                  <p className="dv-card__detail">Mileage: <strong>{v.mileage} km/l</strong></p>
                  {v.color && <p className="dv-card__detail">Color: <strong>{v.color}</strong></p>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}