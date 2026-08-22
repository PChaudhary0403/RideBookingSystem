import { useState,useEffect } from 'react'
import { useNavigate } from "react-router-dom"
import type { FormEvent } from "react";
function LoginUser(){
const[emailID,setEmail]=useState("")
const[password,setPassword]=useState("")
const[status,setStatus]=useState(false)
const payload={emailID,password}
const navigate=useNavigate()
useEffect(()=>{
    if(status===true){
        alert("Login Successful")
        navigate("/maps")
    }
},[status])

async function Submit(){
const response=await fetch("http://localhost:8000/users/login",{
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
    }
    else{
        alert("Login failed")
        }
    localStorage.setItem("role",data.role)
    console.log(data)
}
    return(
        <>
        <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh"}}>
            <div>
                <form onSubmit={(e)=>{e.preventDefault();Submit();}} style={{display:"flex",flexDirection:"column"}}>
                    <input placeholder="Email" value={emailID} onChange={(e)=>setEmail(e.target.value)}/>
                    <input placeholder="Password" value={password} onChange={(e)=>setPassword(e.target.value)}/>
                    <button type="submit">Click</button> 
                </form>
            </div>
        </div>
        </>
    )
}
export default LoginUser;