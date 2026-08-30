import UserGoogleMap from "../../components/userGoogleMap";
import { useState,useEffect } from 'react'
import{ useNavigate } from 'react-router-dom'

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
const buttonStyle = {
    backgroundColor: "#2563EB",
    color: "white",
    border: "none",
    borderRadius: "8px",
    padding: "10px 18px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "600",
    margin: "8px",
  };
  function UserMaps() {
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
    async function RideRequest(){
        if(!selectedDriver) return
        const response=await fetch(`${import.meta.env.VITE_API_URL}/ride-request`,{
            method:"POST",
            credentials:"include",
            body: JSON.stringify({
                driver_id: selectedDriver.driver_id
            })
        })
        const data=await response.json()
        if(response.ok && data.status!==false){
            console.log("request sent")
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
    return(
        <div style={{width: "100%",height: "100vh",backgroundColor: "#F8FAFC"}}>
            <div style={{display:"flex",alignItems:"flex-start",backgroundColor: "#F8FAFC"}}>
            <button style={buttonStyle} onClick={logout}>Logout</button>
            </div>
            <div style={{border:"5px solid #2563EB",borderRadius:"12px",overflow: "hidden",boxShadow: "0 4px 12px rgba(37, 99, 235, 0.2)"}}>
                <UserGoogleMap location={location}
                    drivers={driver}
                    onDriverSelect={getDriverProfile}
                    selectedDriver={selectedDriver}
                    onCloseDriverProfile={()=>setSelectedDriver(null)}
                    onRideRequest={RideRequest}>
                    </UserGoogleMap>
            </div>
            <button style={buttonStyle} onClick={getdrivers}>Get Drivers</button>
        </div>
    )
}
export default UserMaps;