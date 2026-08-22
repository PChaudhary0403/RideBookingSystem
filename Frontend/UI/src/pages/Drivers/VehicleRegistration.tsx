import { useState,useEffect } from 'react'
import { useNavigate } from "react-router-dom"
function VehicleRegistration(){
    const[name,setName]=useState("")
    const[vehicle_type,setType]=useState("")
    const[registration_number,setNumber]=useState("")
    const[associated_licence,setLicence]=useState("")
    const[city,setCity]=useState("")
    const[state,setState]=useState("")
    const[mileage,setMileage]=useState("")
    const[parent_company,setCompany]=useState("")
    const[model,setModel]=useState("")
    const[color,setColor]=useState("")
    const[status,setStatus]=useState(false)
    // const driver_id=Number(localStorage.getItem("driver_id"))
    const navigate=useNavigate()
    useEffect(()=>{
        if(status===true){
            alert("Vehicle Registered")
        }
    },[status])

    function showVehicles(){
        navigate("/driver/vehicles")
    }
    // name:str
    // vehicle_type:VehicleType
    // registration_number:str
    // city:str
    // state:str
    // mileage:int
    // parent_company:str
    // model:str
    // color:str
    async function Submit(){
        const payload={name,
            vehicle_type,
            registration_number,
            associated_licence,
            city,
            state,
            mileage:Number(mileage),
            parent_company
            ,model,
            color,
        }
        const response=await fetch("http://localhost:8000/vehicles/",{
            method:"POST",
            headers:{
                "Content-Type":"application/json",
            },
            credentials:"include",
            body:JSON.stringify(payload)
        })
        const data=await response.json()
        console.log(data)
        if(response.ok){
            setStatus(true)
        }
    }

return(<>
<div>
    <div>
        <form onSubmit={Submit} style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",height:"100vh"}}>
            <input placeholder="Name" value={name} onChange={(e)=>setName(e.target.value)}></input>
            <select value={vehicle_type} onChange={(e) => setType(e.target.value)}>
                        <option value="">Select vehicle type</option>
                        <option value="Bike">Bike</option>
                        <option value="Auto">Auto</option>
                        <option value="Car">Car</option>
                        <option value="SUV">SUV</option>
                        <option value="Van">Van</option>
                        <option value="Mini Bus">Mini Bus</option>
                        <option value="Bus">Bus</option>
            </select>
            <input placeholder="Vehicle Number" value={registration_number} onChange={(e)=>setNumber(e.target.value)}></input>
            <input placeholder="Licence No" value={associated_licence} onChange={(e)=>setLicence(e.target.value)}/>
            <input placeholder="City" value={city} onChange={(e)=>setCity(e.target.value)}></input>
            <input placeholder="State" value={state} onChange={(e)=>setState(e.target.value)}></input>
            <input type="number" placeholder="Mileage" value={mileage} onChange={(e)=>setMileage(e.target.value)}></input>
            <input placeholder="Company" value={parent_company} onChange={(e)=>setCompany(e.target.value)}></input>
            <input placeholder="Model" value={model} onChange={(e)=>setModel(e.target.value)}></input>
            <input placeholder="Color" value={color} onChange={(e)=>setColor(e.target.value)}></input>
            <button type="button" onClick={Submit}>Submit</button>
        </form>
        <button onClick={showVehicles}>Show registered vehicles</button>
    </div>
</div>
</>)
}
export default VehicleRegistration;