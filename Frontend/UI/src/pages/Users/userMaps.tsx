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
type Location = {
    latitude: number;
    longitude: number;
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
export async function getDrivers(
    latitude: number,
    longitude: number,
    radius_km: number = 30){
    const response=await fetch(`${import.meta.env.VITE_API_URL}/users/nearby-drivers`,{
        method:"POST",
        headers:{
            "Content-Type":"application/json",
        },
        credentials:"include",
        body:JSON.stringify({
            latitude,
            longitude,
            radius_km
        })
    })
    const data=await response.json()
    console.log(data)
    console.log(data)
    return data
}
  function UserMaps() {
    const [pickup, setPickup] = useState<Location | null>(null);
    const [destination, setDestination] = useState<Location | null>(null);
    const[location,setLocation]=useState<Location|null>(null);
    const [driver, setDriver] = useState<Driver[]>([]);
    const [selectedDriver, setSelectedDriver] =useState<DriverProfile | null>(null);
    const[logoutstatus,setLogout]=useState(false)
    const navigate=useNavigate()
    const role=localStorage.getItem("role")
    const [userId, setUserId] = useState<number | null>(null);
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
    // useEffect(()=>{
    //     alert(`The driver is selected ${selectedDriver?.driver_id}`)
    // },[selectedDriver])
        useEffect(()=>{
        async function getUserId() {
            const response = await fetch(
                `${import.meta.env.VITE_API_URL}/users/me`,
                {
                    credentials: "include"
                }
            );
            const data = await response.json();
            setUserId(data.user_id);
        }
    
        getUserId();
    },[])
    const [driverResponse, setDriverResponse] = useState<{
        status: string;
        driver_id: number;
        trip_id: number;
    } | null>(null);
    async function get_driver_response(){
        const response=await fetch(`${import.meta.env.VITE_API_URL}/driver-response`,{
            method:"PATCH",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                trip_id:driverResponse?.trip_id
            })
        })
        const data=await response.json()
        console.log(data.status)
    }
    useEffect(() => {
        if (!userId) return;
        const wsURL=`${import.meta.env.VITE_WS_URL}/ws/user/${userId}`
        console.log(wsURL)
        const socket = new WebSocket(
            wsURL
        );
    
        socket.onopen = async() => {
            console.log("User WebSocket connected");
            await get_driver_response()
        };
    
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
    
            console.log("Driver response:", data);
    
            if (data.type === "driver_response") {
                console.log("status updated",data.status);
                setDriverResponse({
                    status: data.status,
                    driver_id: data.driver_id,
                    trip_id: data.trip_id
                });
        
                // accepted or rejected
            }
        };
    
        socket.onclose = () => {
            console.log("User WebSocket disconnected");
        };
    
        return () => {
            socket.close();
        };
    }, [userId]);
    async function handleGetDrivers() {

        if (!location) return;

        const data = await getDrivers(
            location.latitude,
            location.longitude
        );
        if(data.status===true){
            setDriver(data.drivers)
        }
    }
    console.log("driverResponse=====>",driverResponse)
    function handleLocations(
        pickupLocation: Location,
        destinationLocation: Location
    ) {
        setPickup(pickupLocation);
        setDestination(destinationLocation);
    }
    async function RideRequest(){
        if(!selectedDriver || !pickup || !destination) return
        const response=await fetch(`${import.meta.env.VITE_API_URL}/ride-request/`,{
            method:"POST",
            headers:{
                'Content-Type':'application/json'
            },
            credentials:"include",
            body: JSON.stringify({
                driver_id: selectedDriver.driver_id,
                pickup_lat:pickup.latitude,
                pickup_long:pickup.longitude,
                dest_lat:destination.latitude,
                dest_long:destination.longitude
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
    async function handleFindAnotherDriver() {
        await handleGetDrivers();
    
        setDriverResponse(null);
        setSelectedDriver(null);
    }
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
                <UserGoogleMap 
                    location={location}
                    drivers={driver}
                    onDriverSelect={getDriverProfile}
                    selectedDriver={selectedDriver}
                    onCloseDriverProfile={()=>setSelectedDriver(null)}
                    onRideRequest={RideRequest}
                    onLocationsSelected={handleLocations}
                    driverResponse={driverResponse}
                    onFindAnotherDriver={handleFindAnotherDriver}
                    >
                    </UserGoogleMap>
            </div>
            <button style={buttonStyle} onClick={handleGetDrivers}>Get Drivers</button>
        </div>
    )
}
export default UserMaps;