import { useState,useEffect } from 'react'
import{ useNavigate } from 'react-router-dom'
function UserRegister(){
    const[name,setName]=useState("")
    const[phone,setPhone]=useState("")
    const[emailID,setEmail]=useState("")
    const[password,setPassword]=useState("")
    const[check,setCheck]=useState("")
    const[status,setStatus]=useState(false)
    const payload={name,phone,emailID,password}
    const navigate=useNavigate()
    async function Submit(e){
        e.preventDefault()
        if(check!=password){
            alert("Password do not match")
            return
        }
        const response=await fetch("http://localhost:8000/users/register",{
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
            <div>
                <form onSubmit={Submit} style={{display:"flex",flexDirection:"column",gap:"2px"}}>
                    <input placeholder="name" value={name} onChange={(e)=>setName(e.target.value)}></input>
                    <input placeholder="phone" value={phone} onChange={(e)=>setPhone(e.target.value)}></input>
                    <input placeholder="email" value={emailID} onChange={(e)=>setEmail(e.target.value)}></input>
                    <input placeholder="password" value={password} onChange={(e)=>setPassword(e.target.value)}></input>
                    <input placeholder="confirm password" value={check} onChange={(e)=>setCheck(e.target.value)}></input>
                    <button onClick={Submit}>Submit</button>
                </form>
                <button onClick={Switch}>Login</button>
            </div>
        </div>
        </>
    )
}
export default UserRegister;