import DriverGoogleMap from "../../components/driverGoogleMaps";
import { useState,useEffect } from 'react'
import{ useNavigate } from 'react-router-dom'
import type { DriverTripRequest } from "../../types/trip"
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
  function DriverMaps() {
    
    const[location,setLocation]=useState<{
        latitude:number;
        longitude:number;
    }|null>(null);
    const[logoutstatus,setLogout]=useState(false)
    const navigate=useNavigate()
    const role=localStorage.getItem("role")
    console.log(role)
    const [requests,setRequests]=useState<DriverTripRequest[]>([])
    const [selectedRequest, setSelectedRequest] =useState<DriverTripRequest | null>(null);
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
    async function get_requests(){
        const result=await fetch(`${import.meta.env.VITE_API_URL}/drivers/get-request`,{
            method:"GET",
            credentials:"include"
        })
        const data=await result.json()
        if(data.status===true && result.ok){
            setRequests(data.result)
        }
    }
    useEffect(()=>{
        get_requests()
    },[])
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
    return(
        <div style={{width: "100%",height: "100vh",backgroundColor: "#F8FAFC"}}>
            <div style={{display:"flex",alignItems:"flex-start",backgroundColor: "#F8FAFC"}}>
            <button style={buttonStyle} onClick={logout}>Logout</button>
            </div>
            <div style={{border:"5px solid #2563EB",borderRadius:"12px",overflow: "hidden",boxShadow: "0 4px 12px rgba(37, 99, 235, 0.2)"}}>
                <DriverGoogleMap location={location} requests={requests} selectedRequest={selectedRequest} setSelectedRequest={setSelectedRequest}></DriverGoogleMap>
            </div>
            <button style={buttonStyle} onClick={Switch_to_vehicle}>Register Vehicles(if any)</button>
            <button style={buttonStyle} onClick={display_vehicles}>Display your vehicles</button>
        </div>
    )
}
export default DriverMaps;