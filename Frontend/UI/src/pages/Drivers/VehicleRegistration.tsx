import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './VehicleRegistration.css';

interface FormState {
  name: string;
  registration_number: string;
  associated_licence: string;
  city: string;
  state: string;
  mileage: string;
  color: string;
}
type Errors = Partial<Record<keyof FormState | 'api', string>>;

export default function VehicleRegistration() {
  const navigate  = useNavigate();
  const location  = useLocation();
  const selected  = location.state?.vehicle;

  const [form, setForm] = useState<FormState>({
    name: '', registration_number: '', associated_licence: '',
    city: '', state: '', mileage: '', color: '',
  });
  const [errors, setErrors]   = useState<Errors>({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!selected) navigate('/vehicle/select');
  }, [selected, navigate]);

  const set = (k: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(f => ({ ...f, [k]: e.target.value }));
    setErrors(er => ({ ...er, [k]: undefined, api: undefined }));
  };

  function validate(): boolean {
    const err: Errors = {};
    if (!form.name.trim())                err.name                 = 'Vehicle name is required.';
    if (!form.registration_number.trim()) err.registration_number  = 'Registration number is required.';
    if (!form.associated_licence.trim())  err.associated_licence   = 'Licence number is required.';
    if (!form.city.trim())                err.city                 = 'City is required.';
    if (!form.state.trim())               err.state                = 'State is required.';
    if (!form.mileage || isNaN(Number(form.mileage)) || Number(form.mileage) <= 0)
                                          err.mileage              = 'Enter a valid mileage.';
    if (!form.color.trim())               err.color                = 'Color is required.';
    setErrors(err);
    return Object.keys(err).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/vehicles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name: form.name,
          vehicle_type: selected.type,
          registration_number: form.registration_number,
          associated_licence: form.associated_licence,
          city: form.city,
          state: form.state,
          mileage: Number(form.mileage),
          parent_company: selected.company,
          model: selected.model,
          color: form.color,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setErrors({ api: data.detail || 'Registration failed. Please try again.' });
      } else {
        setSuccess(true);
        setTimeout(() => navigate('/driver/home'), 1800);
      }
    } catch {
      setErrors({ api: 'Network error. Please check your connection.' });
    } finally {
      setLoading(false);
    }
  }

  const fields: { key: keyof FormState; label: string; placeholder: string; type?: string }[] = [
    { key: 'name',                label: 'Vehicle Name',         placeholder: 'e.g. My Honda Activa' },
    { key: 'registration_number', label: 'Registration Number',  placeholder: 'MH01AB1234' },
    { key: 'associated_licence',  label: 'Driving Licence No.',  placeholder: 'DL1420110012345' },
    { key: 'city',                label: 'City',                 placeholder: 'Mumbai' },
    { key: 'state',               label: 'State',                placeholder: 'Maharashtra' },
    { key: 'mileage',             label: 'Mileage (km/l)',       placeholder: '45', type: 'number' },
    { key: 'color',               label: 'Vehicle Color',        placeholder: 'Pearl White' },
  ];

  return (
    <div className="vr-page">
      {/* Header */}
      <div className="vr-header">
        <button className="btn btn-ghost btn-sm vr-back" onClick={() => navigate('/vehicle/select')} aria-label="Back to vehicle selection">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>
          Choose Different Vehicle
        </button>
      </div>

      <div className="vr-layout container">
        {/* Selected vehicle preview */}
        {selected && (
          <div className="vr-preview">
            <div className="vr-preview__card">
              <span className="badge badge-primary" style={{ marginBottom: 'var(--space-3)' }}>Selected Vehicle</span>
              <div className="vr-preview__img-wrap">
                <img src={selected.image} alt={`${selected.company} ${selected.model}`} className="vr-preview__img" />
              </div>
              <h2 className="vr-preview__name">{selected.company}</h2>
              <p className="vr-preview__model">{selected.model}</p>
              <p className="vr-preview__type">{selected.type}</p>
            </div>
          </div>
        )}

        {/* Form */}
        <div className="vr-form-wrap">
          {success ? (
            <div className="vr-success">
              <div className="vr-success__icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-600)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
              <h2>Vehicle Registered!</h2>
              <p>Redirecting to your dashboard…</p>
            </div>
          ) : (
            <div className="card">
              <div className="card-body">
                <h1 className="vr-form__title">Register Your Vehicle</h1>
                <p className="vr-form__sub">Fill in your vehicle details to start accepting rides.</p>

                {errors.api && (
                  <div role="alert" className="vr-error-banner">{errors.api}</div>
                )}

                <form onSubmit={handleSubmit} noValidate className="vr-form">
                  {fields.map(f => (
                    <div className="form-group" key={f.key}>
                      <label htmlFor={`vr-${f.key}`} className="form-label">{f.label}</label>
                      <input
                        id={`vr-${f.key}`}
                        className={`form-input${errors[f.key] ? ' error' : ''}`}
                        type={f.type ?? 'text'}
                        placeholder={f.placeholder}
                        value={form[f.key]}
                        onChange={set(f.key)}
                        inputMode={f.type === 'number' ? 'numeric' : undefined}
                        aria-describedby={errors[f.key] ? `vr-${f.key}-err` : undefined}
                      />
                      {errors[f.key] && (
                        <span id={`vr-${f.key}-err`} className="form-error" role="alert">{errors[f.key]}</span>
                      )}
                    </div>
                  ))}

                  <div className="vr-form__actions">
                    <button
                      type="submit"
                      className={`btn btn-accent btn-lg${loading ? ' btn-loading' : ''}`}
                      disabled={loading}
                    >
                      {loading ? 'Registering…' : 'Register Vehicle'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => navigate('/driver/vehicles')}
                    >
                      View my vehicles
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}