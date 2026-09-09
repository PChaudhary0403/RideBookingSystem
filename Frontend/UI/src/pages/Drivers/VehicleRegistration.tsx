import { useState,useEffect } from 'react'
import { useNavigate,useLocation } from "react-router-dom"
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
    // const driver_id=Number(localStorage.getItem("driver_id"))
    const navigate=useNavigate()
    const location=useLocation()
    const selectedVehicle=location.state?.vehicle
    useEffect(()=>{
        if(status===true){
            alert("Vehicle Registered")
        }
    },[status])

    function showVehicles(){
        navigate("/driver/vehicles")
    }
    function addVehicle() {
        navigate("/vehicle/select");
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
        if (!selectedVehicle) {
            alert("Please select a vehicle first");
            navigate("/vehicle/select");
            return;
        }
        const payload={name,
            vehicle_type:selectedVehicle.type,
            registration_number,
            associated_licence,
            city,
            state,
            mileage:Number(mileage),
            parent_company:selectedVehicle.company,
            model:selectedVehicle.model,
            color,
        }
        const response=await fetch(`${import.meta.env.VITE_API_URL}/vehicles`,{
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
<div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh"}}>
    <div style={{width: "100%",height: "100vh",backgroundColor: "#F8FAFC"}}>
        <form onSubmit={Submit} style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",height:"100vh",gap:"5px"}}>
            <input style={{border:"2px solid #2563EB",borderRadius:"8px" ,padding: "10px 18px"}} placeholder="Name" value={name} onChange={(e)=>setName(e.target.value)}></input>
            <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="Vehicle Number" value={registration_number} onChange={(e)=>setNumber(e.target.value)}></input>
            <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="Licence No" value={associated_licence} onChange={(e)=>setLicence(e.target.value)}/>
            <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="City" value={city} onChange={(e)=>setCity(e.target.value)}></input>
            <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="State" value={state} onChange={(e)=>setState(e.target.value)}></input>
            <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} type="number" placeholder="Mileage" value={mileage} onChange={(e)=>setMileage(e.target.value)}></input>
            <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="Color" value={color} onChange={(e)=>setColor(e.target.value)}></input>
            <button style={buttonStyle} onClick={addVehicle}>Select vehicles</button>
            <button style={buttonStyle} type="button" onClick={Submit}>Submit</button>
        </form>
        <button style={buttonStyle} onClick={showVehicles}>Show registered vehicles</button>
    </div>
</div>
</>)
}
export default VehicleRegistration;