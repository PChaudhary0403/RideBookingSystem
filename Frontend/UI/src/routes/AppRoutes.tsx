import { Routes,Route } from "react-router-dom"
import RegisterDriver from "../pages/Drivers/DriverRegistration"
import VehicleRegistration from "../pages/Drivers/VehicleRegistration"
import LoginDriver from "../pages/Drivers/DriverLogin"
import DisplayVehicles from "../pages/Drivers/DisplayVehicles"
import UserRegister from "../pages/Users/UserRegistration"
import LoginUser from "../pages/Users/LoginPage"
import HomePage from "../pages/Drivers/HomePage"
import Maps from "../pages/Map"
import App from "../App"
function AppRoutes(){
    const driver_id=localStorage.getItem("driver_id")
    return(
    <Routes>
        <Route path="/driver/register" element={<RegisterDriver/>}/>
        <Route path="/vehicle/register" element={<VehicleRegistration/>}/>
        <Route path="/driver/login" element={<LoginDriver/>}/>
        <Route path="/driver/vehicles" element={<DisplayVehicles/>}/>

        {/* user */}
        <Route path="/users/register" element={<UserRegister/>}/>
        <Route path="/users/login" element={<LoginUser/>}/>
        <Route path="/" element={<HomePage/>}/>

        {/* map */}
        <Route path="/maps" element={<Maps/>}/>
    </Routes>
    );
}
export default AppRoutes;