import { useState,useEffect } from 'react'
import { useNavigate } from "react-router-dom"
import type { FormEvent } from "react";
function LoginUser(){
const[emailID,setEmail]=useState("")
const[password,setPassword]=useState("")
const[status,setStatus]=useState(false)
const payload={emailID,password}
const navigate=useNavigate()
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
    if(status===true){
        alert("Login Successful")
        navigate("/user-maps")
    }
},[status])

async function Submit(){
const response=await fetch(`${import.meta.env.VITE_API_URL}/users/login`,{
    method:"POST",
    headers:{
        "Content-Type":"application/json",
    },
    credentials:"include",
    body:JSON.stringify(payload)
    })
    const data=await response.json()
    if(data.status===true){
        setStatus(true)
        localStorage.setItem("role",data.role)
    }
    else{
        alert("Login failed")
        }
    console.log(data)
}
    return(
        <>
        <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh"}}>
            <div style={{backgroundColor: "#F8FAFC"}}>
                <form onSubmit={(e: FormEvent<HTMLFormElement>)=>{e.preventDefault();Submit();}} style={{display:"flex",flexDirection:"column",gap:"5px"}}>
                    <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="Email" value={emailID} onChange={(e)=>setEmail(e.target.value)}/>
                    <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="Password" value={password} onChange={(e)=>setPassword(e.target.value)}/>
                    <button style={buttonStyle} type="submit">Click</button> 
                </form>
            </div>
        </div>
        </>
    )
}
export default LoginUser;