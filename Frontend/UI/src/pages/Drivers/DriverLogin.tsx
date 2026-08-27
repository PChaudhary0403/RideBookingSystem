import { useState,useEffect } from 'react'
import { useNavigate } from "react-router-dom"
import type { FormEvent } from "react";
function LoginDriver(){
const[email,setEmail]=useState("")
const[password,setPassword]=useState("")
const[status,setStatus]=useState(false)
const payload={email,password}
const navigate=useNavigate()

async function Submit(e: FormEvent<HTMLFormElement>){
    e.preventDefault();
    const response=await fetch(`${import.meta.env.VITE_API_URL}/drivers/login`,{
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
        console.log(response.json)
    }
    useEffect(()=>{
        if(status===true){
            alert("Login Successful")
            navigate("/maps")
        }
    },[status])
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
    
            await fetch(
                `${import.meta.env.VITE_API_URL}/drivers/location`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    credentials: "include",
                    body: JSON.stringify({
                        latitude,
                        longitude
                    })
                }
            );
        }
    );
    return(
        <>
        <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh"}}>
            <div>
                <form onSubmit={Submit} style={{display:"flex",flexDirection:"column"}}>
                    <input placeholder="Email" value={email} onChange={(e)=>setEmail(e.target.value)}/>
                    <input placeholder="Password" value={password} onChange={(e)=>setPassword(e.target.value)}/>
                    <button type="submit">Click</button>
                </form>
            </div>
        </div>
        </>
    )
}
export default LoginDriver;