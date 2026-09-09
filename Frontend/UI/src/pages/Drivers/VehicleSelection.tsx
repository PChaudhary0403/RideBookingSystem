import { useNavigate } from 'react-router-dom'
import hondaShine from "../assets/vehicles/HondaShine.png";
import bajajRE from "../assets/vehicles/Bajaj-re.png";
import swift from "../assets/vehicles/Swift.png";
import creta from "../assets/vehicles/Creta.png";
import eeco from "../assets/vehicles/Eco.png";
import forceTraveller from "../assets/vehicles/ForceTraveller.png";
import tataStarbus from "../assets/vehicles/Tata_Starbus.png";
type Vehicle={
    id:string;
    type:string;
    company:string;
    model:string;
    image:string
}
const vehicles:Vehicle[] = [
    {
        id: "bike",
        type: "Bike",
        company: "Honda",
        model: "Activa",
        image: hondaShine
    },
    {
        id: "auto",
        type: "Auto",
        company: "Bajaj",
        model: "RE",
        image: bajajRE
    },
    {
        id: "car",
        type: "Car",
        company: "Maruti Suzuki",
        model: "Swift",
        image: swift
    },
    {
        id: "suv",
        type: "SUV",
        company: "Hyundai",
        model: "Creta",
        image: creta
    },
    {
        id: "van",
        type: "Van",
        company: "Maruti Suzuki",
        model: "Eeco",
        image: eeco
    },
    {
        id: "mini-bus",
        type: "Mini Bus",
        company: "Force",
        model: "Traveller",
        image: forceTraveller
    },
    {
        id: "bus",
        type: "Bus",
        company: "Tata",
        model: "Starbus",
        image: tataStarbus
    }
];
function VehicleSelection(){
    const navigate=useNavigate()
    function selectVehicle(vehicle:Vehicle){
        navigate("/vehicle/register",{
            state:{
                vehicle:vehicle
            }
        })
    }
    return(
        <div 
            style={{
            minHeight: "100vh",
            backgroundColor: "#F8FAFC",
            padding: "30px"
        }}>
            <h1 
                style={{
                textAlign: "center",
                color: "#2563EB"
                }}>Select Your Vehicle</h1>
                            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(220px, 1fr))",
                    gap: "20px",
                    maxWidth: "1000px",
                    margin: "30px auto"
                }}
            >
                {vehicles.map((vehicle) => (

                <div
                    key={vehicle.id}
                    onClick={() => selectVehicle(vehicle)}
                    style={{
                        backgroundColor: "white",
                        border: "2px solid #2563EB",
                        borderRadius: "12px",
                        padding: "15px",
                        cursor: "pointer",
                        textAlign: "center"
                    }}
                >

                    <img
                        src={vehicle.image}
                        alt={`${vehicle.company} ${vehicle.model}`}
                        style={{
                            width: "100%",
                            height: "150px",
                            objectFit: "contain"
                        }}
                    />
                                            <h3>
                            {vehicle.company}
                        </h3>

                        <h2>
                            {vehicle.model}
                        </h2>

                        <p>
                            {vehicle.type}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    )
}
export default VehicleSelection