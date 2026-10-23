import { Routes, Route } from 'react-router-dom';
import LandingPage        from '../pages/LandingPage';
import RegisterDriver     from '../pages/Drivers/DriverRegistration';
import VehicleRegistration from '../pages/Drivers/VehicleRegistration';
import LoginDriver        from '../pages/Drivers/DriverLogin';
import DisplayVehicles    from '../pages/Drivers/DisplayVehicles';
import DriverHomePage     from '../pages/Drivers/HomePage';
import UserRegister       from '../pages/Users/UserRegistration';
import LoginUser          from '../pages/Users/LoginPage';
import UserMaps           from '../pages/Users/userMaps';
import DriverMaps         from '../pages/Drivers/driverMaps';
import VehicleSelection   from '../pages/Drivers/VehicleSelection';

function AppRoutes() {
  return (
    <Routes>
      {/* Landing */}
      <Route path="/"    element={<LandingPage />} />

      {/* User auth */}
      <Route path="/register"    element={<UserRegister />} />
      <Route path="/login"       element={<LoginUser />} />

      {/* Legacy route aliases (preserve existing deep-links) */}
      <Route path="/users/register" element={<UserRegister />} />
      <Route path="/users/login"    element={<LoginUser />} />

      {/* Driver auth */}
      <Route path="/driver/register" element={<RegisterDriver />} />
      <Route path="/driver/login"    element={<LoginDriver />} />
      <Route path="/driver/home"     element={<DriverHomePage />} />

      {/* Vehicles */}
      <Route path="/vehicle/select"   element={<VehicleSelection />} />
      <Route path="/vehicle/register" element={<VehicleRegistration />} />
      <Route path="/driver/vehicles"  element={<DisplayVehicles />} />

      {/* Maps (preserved exactly — complex WebSocket components) */}
      <Route path="/user/maps"   element={<UserMaps />} />
      <Route path="/driver/maps" element={<DriverMaps />} />

      {/* Legacy map aliases */}
      <Route path="/user-maps"   element={<UserMaps />} />
      <Route path="/driver-maps" element={<DriverMaps />} />
    </Routes>
  );
}

export default AppRoutes;