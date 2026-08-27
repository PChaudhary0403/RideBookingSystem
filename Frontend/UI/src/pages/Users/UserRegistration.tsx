import { useState,useEffect } from 'react'
import{ useNavigate } from 'react-router-dom'
import type { FormEvent } from "react";
function UserRegister(){
    const[name,setName]=useState("")
    const[phone,setPhone]=useState("")
    const[emailID,setEmail]=useState("")
    const[password,setPassword]=useState("")
    const[check,setCheck]=useState("")
    const[status,setStatus]=useState(false)
    const payload={name,phone,emailID,password}
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
    async function Submit(e: FormEvent<HTMLFormElement>){
        e.preventDefault()
        if(check!=password){
            alert("Password do not match")
            return
        }
        const response=await fetch(`${import.meta.env.VITE_API_URL}/users/register`,{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            credentials:"include",
            body:JSON.stringify(payload)
    })
    const data=await response.json()
    console.log(data)
    if(data.status===true){
        setStatus(true)
    }
    useEffect(()=>{
        if(status===true){
            alert("Registration Successful")
        }
    })
}
function Switch(){
    navigate("/users/login")
}
    return(
        <>
        <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh"}}>
            <div style={{backgroundColor: "#F8FAFC"}}>
                <form onSubmit={Submit} style={{display:"flex",flexDirection:"column",gap:"5px"}}>
                    <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="name" value={name} onChange={(e)=>setName(e.target.value)}></input>
                    <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="phone" value={phone} onChange={(e)=>setPhone(e.target.value)}></input>
                    <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="email" value={emailID} onChange={(e)=>setEmail(e.target.value)}></input>
                    <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="password" value={password} onChange={(e)=>setPassword(e.target.value)}></input>
                    <input style={{border:"2px solid #2563EB",borderRadius:"8px",padding: "10px 18px"}} placeholder="confirm password" value={check} onChange={(e)=>setCheck(e.target.value)}></input>
                    <button style={buttonStyle} type="submit">Submit</button>
                </form>
                <button style={buttonStyle} onClick={Switch}>Login</button>
            </div>
        </div>
        </>
    )
}
export default UserRegister;