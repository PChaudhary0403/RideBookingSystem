// import { useState } from 'react'
// import RegisterDriver from "./pages/DriverRegistration"
// import './App.css'
// import VehicleRegistration from "./pages/VehicleRegistration"
// import { useNavigate } from 'react-router-dom'
import AppRoutes from "./routes/AppRoutes";

function App() {
  console.log(import.meta.env.VITE_GOOGLE_MAPS_API_KEY)
  return (
  <AppRoutes/>
  )
}

export default App;
