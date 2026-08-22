import { useNavigate } from 'react-router-dom'

function HomePage() {
  const navigate=useNavigate()
  return (
  <>
  <div style={{display:"flex",justifyContent:"center",alignItems:"center",height:"100vh"}}>
  <div>
    <p>This is my App</p>
    <button onClick={()=>navigate("/driver/register")}>Click here to register as Driver</button>
    <button onClick={()=>navigate("/users/register")}>Click here to register as a user</button>
  </div>
  </div>
    </>)
}
export default HomePage