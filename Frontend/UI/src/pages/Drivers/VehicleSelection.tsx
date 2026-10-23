import { useNavigate } from 'react-router-dom';
import hondaShine    from '../../assets/vehicles/HondaShine.png';
import bajajRE       from '../../assets/vehicles/Bajaj_re.png';
import swift         from '../../assets/vehicles/Swift.png';
import creta         from '../../assets/vehicles/Creta.png';
import eeco          from '../../assets/vehicles/Eco.png';
import forceTraveller from '../../assets/vehicles/ForceTraveller.png';
import tataStarbus   from '../../assets/vehicles/Tata_Starbus.png';
import './VehicleSelection.css';

type Vehicle = { id: string; type: string; company: string; model: string; image: string };

const vehicles: Vehicle[] = [
  { id: 'bike',     type: 'Bike',     company: 'Honda',          model: 'Activa',    image: hondaShine },
  { id: 'auto',     type: 'Auto',     company: 'Bajaj',          model: 'RE',        image: bajajRE },
  { id: 'car',      type: 'Car',      company: 'Maruti Suzuki',  model: 'Swift',     image: swift },
  { id: 'suv',      type: 'SUV',      company: 'Hyundai',        model: 'Creta',     image: creta },
  { id: 'van',      type: 'Van',      company: 'Maruti Suzuki',  model: 'Eeco',      image: eeco },
  { id: 'mini-bus', type: 'Mini Bus', company: 'Force',          model: 'Traveller', image: forceTraveller },
  { id: 'bus',      type: 'Bus',      company: 'Tata',           model: 'Starbus',   image: tataStarbus },
];

export default function VehicleSelection() {
  const navigate = useNavigate();

  function selectVehicle(v: Vehicle) {
    navigate('/vehicle/register', { state: { vehicle: v } });
  }

  return (
    <div className="vs-page">
      {/* Header */}
      <div className="vs-header">
        <button
          className="vs-back btn btn-ghost btn-sm"
          onClick={() => navigate('/driver/home')}
          aria-label="Back to dashboard"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>
          Dashboard
        </button>
        <div>
          <h1 className="vs-title">Select Your Vehicle</h1>
          <p className="vs-sub">Choose the vehicle type you'll use to accept rides.</p>
        </div>
      </div>

      {/* Grid */}
      <div className="container vs-grid" role="list" aria-label="Vehicle types">
        {vehicles.map(v => (
          <button
            key={v.id}
            id={`vehicle-${v.id}`}
            className="vs-card"
            onClick={() => selectVehicle(v)}
            role="listitem"
            aria-label={`Select ${v.company} ${v.model} (${v.type})`}
          >
            <div className="vs-card__img-wrap">
              <img src={v.image} alt={`${v.company} ${v.model}`} className="vs-card__img" loading="lazy" />
            </div>
            <div className="vs-card__body">
              <span className="badge badge-primary vs-card__type">{v.type}</span>
              <h2 className="vs-card__company">{v.company}</h2>
              <p className="vs-card__model">{v.model}</p>
            </div>
            <div className="vs-card__overlay" aria-hidden="true">Select</div>
          </button>
        ))}
      </div>
    </div>
  );
}