import GoogleMap from "../components/GoogleMap";
import { useState,useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

function Maps() {
    const[location,setLocation]=useState<{
        latitude:number;
        longitude:number;
    }|null>(null);
    const[driver,setDriver]=useState([])
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
        console.log(data.drivers[0])
        if(data.status===true){
            setDriver(data.drivers)
        }
    }
    async function logout(){
        const url=role=="driver"?`${import.meta.env.VITE_API_URL}/drivers/logout`:`${import.meta.env.VITE_API_URL}/users/logout`
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
    return (
        <div>
            <button onClick={getLocation}>Get Location</button>
            <button onClick={logout}>Logout</button>
            <GoogleMap location={location} drivers={driver}/>
            {role==="user" &&(
            <button onClick={getdrivers}>Get Drivers</button>
            )
}
            <button onClick={Switch_to_vehicle}>Register Vehicles(if any)</button>
            {role=="driver"&&(
            <button onClick={display_vehicles}>Display your vehicles</button>
        )}
        </div>
    );
}
export default Maps