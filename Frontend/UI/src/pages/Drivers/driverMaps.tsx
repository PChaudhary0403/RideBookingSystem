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
    const [menuOpen, setMenuOpen] = useState(false);
    const menuItemStyle = {
        width: "100%",
        padding: "12px 16px",
        border: "none",
        backgroundColor: "transparent",
        textAlign: "left" as const,
        cursor: "pointer",
        fontSize: "15px"
    };
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

    const [driver_id, setDriverId] = useState<number | null>(null);
    const [call,setCall]=useState(false)
    useEffect(()=>{
        async function getDriverId() {
            const response = await fetch(
                `${import.meta.env.VITE_API_URL}/drivers/me`,
                {
                    credentials: "include"
                }
            );
            const data = await response.json();
            setDriverId(data.driver_id);
        }
    
        getDriverId();
    },[])
    async function send_response(){
        if(!driver_id) return
        const socket=new WebSocket(`${import.meta.env.VITE_WS_URL}/ws/driver/${driver_id}`)
        socket.onopen=()=>{
            console.log("Driver websocket Connected")
        }
        socket.onmessage=(event)=>{
            const data=JSON.parse(event.data)
            console.log("Websocket message:",data)
            if(data.type==="new request"){
                setRequests((prev)=>[
                    data.request,
                    ...prev
                ])
            }
            if(data.type==="user_called"){
                setCall(true)
            }
        };
        socket.onclose=()=>{
            console.log("Driver Socket Disconnected")
        }
        socket.onerror=(error)=>{
            console.log("socket error",error)
        }
        return ()=>{
            socket.close()
        }
    }
    useEffect(()=>{
        send_response()
    },[driver_id])
    return(
        <div
            style={{
                width: "100%",
                height: "100vh",
                backgroundColor: "#F8FAFC"
            }}
        >
            {/* Top Toolbar */}
            <div
                style={{
                    width: "100%",
                    height: "64px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0 20px",
                    boxSizing: "border-box",
                    backgroundColor: "white",
                    borderBottom: "1px solid #E5E7EB",
                    position: "relative",
                    zIndex: 100
                }}
            >

                {/* Left - Menu */}
                <div style={{ position: "relative" }}>

                    <button
                        style={{
                            width: "42px",
                            height: "42px",
                            border: "none",
                            borderRadius: "8px",
                            backgroundColor: "#F1F5F9",
                            cursor: "pointer",
                            fontSize: "22px"
                        }}
                        onClick={() => setMenuOpen(!menuOpen)}
                    >
                        ☰
                    </button>

                    {menuOpen && (
                        <div
                            style={{
                                position: "absolute",
                                top: "50px",
                                left: "0",
                                width: "220px",
                                backgroundColor: "white",
                                borderRadius: "10px",
                                boxShadow: "0 5px 20px rgba(0,0,0,0.15)",
                                padding: "8px 0",
                                border: "1px solid #E5E7EB"
                            }}
                        >
                            <button style={menuItemStyle} onClick={Switch_to_vehicle}>
                                Register Vehicles(if any)
                            </button>
                            <button style={menuItemStyle} onClick={display_vehicles}>
                                Display your vehicles
                            </button>
                            <button style={menuItemStyle}>
                                Transactions
                            </button>

                            <button style={menuItemStyle}>
                                Trip History
                            </button>

                            <button style={menuItemStyle}>
                                Request History
                            </button>
                        </div>
                    )}
                </div>


                {/* Center - Future Navigation */}
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "30px",
                        flex: 1
                    }}
                >
                    {/* Future navigation items go here */}
                </div>


                {/* Right - Logout */}
                <button
                    style={buttonStyle}
                    onClick={logout}
                >
                    Logout
                </button>

            </div>
            <div style={{height:"100vh",border:"5px solid #2563EB",borderRadius:"12px",overflow: "hidden",boxShadow: "0 4px 12px rgba(37, 99, 235, 0.2)"}}>
                <DriverGoogleMap 
                location={location} 
                requests={requests}
                setRequests={setRequests}
                selectedRequest={selectedRequest}
                setSelectedRequest={setSelectedRequest}
                Call={call}></DriverGoogleMap>
            </div>
        </div>
    )
}
export default DriverMaps;