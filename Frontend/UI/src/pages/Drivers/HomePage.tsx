import { useNavigate } from 'react-router-dom'
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
function HomePage() {
  const navigate=useNavigate()
  return (
  <>
  <div style={{display:"flex",justifyContent:"center",alignItems:"center",height:"100vh"}}>
  <div style={{width: "100%",height: "100vh",backgroundColor: "#F8FAFC"}}>
    <p>This is my App</p>
    <button style={buttonStyle} onClick={()=>navigate("/driver/register")}>Click here to register as Driver</button>
    <button style={buttonStyle} onClick={()=>navigate("/users/register")}>Click here to register as a user</button>
  </div>
  </div>
    </>)
}
export default HomePage