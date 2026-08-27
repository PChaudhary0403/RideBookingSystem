import { Routes,Route } from "react-router-dom"
import RegisterDriver from "../pages/Drivers/DriverRegistration"
import VehicleRegistration from "../pages/Drivers/VehicleRegistration"
import LoginDriver from "../pages/Drivers/DriverLogin"
import DisplayVehicles from "../pages/Drivers/DisplayVehicles"
import UserRegister from "../pages/Users/UserRegistration"
import LoginUser from "../pages/Users/LoginPage"
import HomePage from "../pages/Drivers/HomePage"
import UserMaps from "../pages/Users/userMaps"
import DriverMaps from "../pages/Drivers/driverMaps"
function AppRoutes(){
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
        <Route path="/user-maps" element={<UserMaps/>}/>
        <Route path="/driver-maps" element={<DriverMaps/>}></Route>
    </Routes>
    );
}
export default AppRoutes;