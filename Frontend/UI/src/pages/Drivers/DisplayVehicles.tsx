import { useState,useEffect } from 'react'
function DisplayVehicles(){
    const driver_id=localStorage.getItem("driver_id")
    const[vehicles,setVehicles]=useState([])
useEffect(()=>{
    async function fetchVehicles(){
    const response=await fetch(`http://127.0.0.1:8000/vehicles/driver/${driver_id}`)
    const data=await response.json()
    console.log(data)
    const vehicles=data.vehicles
    console.log(vehicles)
    setVehicles(vehicles)
    }
    fetchVehicles()
},[]);
    return(
        <>
        <div>
        <p>My vehicles</p>
        <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh"}}>
            <div style={{display:"flex",flexDirection:"row",gap:"22px"}}>
                {vehicles.length===0?(
                    <p> No vehicles found</p>
                ):(
                    vehicles.map((vehicle)=>(
                    <div style={{display:"flex",flexDirection:"column",textAlign:"justify",border:"2px solid black",borderRadius:"5px",padding:"4px"}}key={vehicle.id}>
                        <h2>Name:{vehicle.name}</h2>
                        <p>Type:{vehicle.type}</p>
                        <p>Color:{vehicle.model}</p>
                        <p>Mileage:{vehicle.mileage}</p>
                    </div>
                ))
            )}
                </div>
            </div>
        </div>
        </>
    )
}
export default DisplayVehicles;