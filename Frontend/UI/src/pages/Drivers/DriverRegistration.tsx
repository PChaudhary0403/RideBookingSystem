import { useState,useEffect } from 'react'
import { useNavigate } from "react-router-dom";
function RegisterDriver(){
const[name,setName]=useState("");
const[surname,setSurname]=useState("")
const[address,setAddress]=useState("")
const[licenceno,setLicenseNo]=useState("")
const[phone,setPhone]=useState("")
const[email,setEmail]=useState("")
const[password,setPassword]=useState("")
const[checkpassword,setCheck]=useState("")
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
useEffect(()=>{
    if(status==true){
        alert("Registered Sucessfully!!")
    }
},[status]);
async function Submit(){
    if (password !== checkpassword) {
        alert("Passwords don't match");
        return;
    }
const response=await fetch(`${import.meta.env.VITE_API_URL}/drivers/register`,{
    method:"POST",
    headers:{
        "Content-Type":"application/json"
    },
    body:JSON.stringify({
        name:name,
        surname:surname,
        email:email,
        phone:phone,
        password:password,
        address:address,
        licenceno:licenceno
    })
}
)
console.log("STATUS:", response.status);
console.log("OK:", response.ok);
console.log("CONTENT TYPE:", response.headers.get("content-type"));

const data = await response.json();
localStorage.setItem("driver_id",data.driverID)
if(response.ok){
    setStatus(true);
}
}
const navigate=useNavigate()
function Switch_to_login(){
    navigate("/driver/login")
}
return(
    <>
    <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh"}}>
        <div style={{backgroundColor: "#F8FAFC"}}>
            <form onSubmit={Submit} style={{display:"flex",flexDirection:"column",gap:"5px"}}>
            <input style={{border:"2px solid #2563EB",borderRadius:"12px"}} placeholder="name" value={name} onChange={(e)=>setName(e.target.value)}/>
            <input style={{border:"2px solid #2563EB",borderRadius:"12px"}} placeholder="surname" value={surname} onChange={(e)=>setSurname(e.target.value)}/>
            <input style={{border:"2px solid #2563EB",borderRadius:"12px"}} placeholder="address" value={address} onChange={(e)=>setAddress(e.target.value)}/>
            <input style={{border:"2px solid #2563EB",borderRadius:"12px"}} placeholder="licenceno" value={licenceno} onChange={(e)=>setLicenseNo(e.target.value)}/>
            <input style={{border:"2px solid #2563EB",borderRadius:"12px"}} placeholder="phone" value={phone} onChange={(e)=>setPhone(e.target.value)}/>
            <input style={{border:"2px solid #2563EB",borderRadius:"12px"}} placeholder="email" value={email} onChange={(e)=>setEmail(e.target.value)}/>
            <input style={{border:"2px solid #2563EB",borderRadius:"12px"}} placeholder="password" value={password} onChange={(e)=>setPassword(e.target.value)}/>
            <input style={{border:"2px solid #2563EB",borderRadius:"12px"}} placeholder="check password" value={checkpassword} onChange={(e)=>setCheck(e.target.value)}/>
            <button type="button" style={buttonStyle} onClick={Submit}>Register yourself as a driver</button>
            </form>
            <div>
            <button style={buttonStyle} onClick={Switch_to_login}>Login as a Driver</button>
            </div>
        </div>
    </div>
    </>
)
}
export default RegisterDriver;