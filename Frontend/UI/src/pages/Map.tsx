import GoogleMap from "../components/GoogleMap";
import { useState,useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
type DriverProfile = {
    driver_id: number;
    name: string;
    surname: string;
    rating: number | null;
    total_reviews: number;
    distance_km: number;
};
type Driver = {
    driver_id: number;
    latitude: number;
    longitude: number;
    distance_km: number;
};
function Maps() {
    const[location,setLocation]=useState<{
        latitude:number;
        longitude:number;
    }|null>(null);
    const [driver, setDriver] = useState<Driver[]>([]);
    const [selectedDriver, setSelectedDriver] =useState<DriverProfile | null>(null);
    const[logoutstatus,setLogout]=useState(false)
    const navigate=useNavigate()
    const role=localStorage.getItem("role")
    console.log(role)
    function getLocation(){
        
        navigator.geolocation.getCurrentPosition(
            (position)=>{
                const latitude=position.coords.latitude
                const longitude=position.coords.longitude
                console.log(latitude)
                console.log(longitude)
                setLocation({
                    latitude,longitude
                })
            },
            (error)=>{
                console.log("location error",error)
            }
        )
    }
    useEffect(()=>{
        getLocation()
    },[])
    async function getdrivers(){
        const response=await fetch(`${import.meta.env.VITE_API_URL}/users/nearby-drivers`,{
            method:"POST",
            headers:{
                "Content-Type":"application/json",
            },
            credentials:"include",
            body:JSON.stringify({
                latitude:location?.latitude,
                longitude:location?.longitude,
                radius_km:30
            })
        })
        const data=await response.json()
        console.log(data)
        console.log(data)
        if(data.status===true){
            setDriver(data.drivers)
        }
    }
    async function logout(){
        const url=role=="driver"?`${import.meta.env.VITE_API_URL}/drivers/logout`:`${import.meta.env.VITE_API_URL}/users/logout`
        console.log(url)
        const response=await fetch(url,{
            method:"POST",
            credentials:"include"
        })
        const data=await response.json()
        if(data.status===true){
            setLogout(true)
        }
    }
    function Switch_to_vehicle(){
        navigate("/vehicle/register")
      }
    function display_vehicles(){
        navigate("/driver/vehicles")
    }
    useEffect(()=>{
        if(logoutstatus===true){
            navigate('/')
        }
    },[logoutstatus,navigate])
    async function getDriverProfile(driverId: number) {
        console.log("Clicked driver:", driverId);
        const clickedDriver = driver.find(
            (d) => d.driver_id === driverId
        );
        const response = await fetch(
            `${import.meta.env.VITE_API_URL}/drivers/${driverId}/profile`,
            {
                credentials: "include"
            }
        )
        console.log("Response:", response.status);
        const data=await response.json()
        console.log("Driver profile data:", data);
        if(response.ok){
            setSelectedDriver({
                ...data,distance_km: clickedDriver?.distance_km
            })  
        }
    }
    return (
        <div>
            <button onClick={logout}>Logout</button>
            <div style={{border:"2px solid #2563EB",borderRadius:"5px"}}>
            <GoogleMap 
            location={location}
            drivers={driver}
            onDriverSelect={getDriverProfile}
            selectedDriver={selectedDriver}
            onCloseDriverProfile={()=>setSelectedDriver(null)} />
            </div>
            {role==="user" &&(
            <button onClick={getdrivers}>Get Drivers</button>
            )
}
            {role==="driver" &&(
                <>
            <button onClick={Switch_to_vehicle}>Register Vehicles(if any)</button>
            <button onClick={display_vehicles}>Display your vehicles</button>
            </>
        )}
        </div>
    );
}
export default Maps