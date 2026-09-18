import { APIProvider,Map,AdvancedMarker,useMap,useMapsLibrary,Polyline } from "@vis.gl/react-google-maps"
import { useEffect,useState } from 'react'
import userImage from "../assets/user.png";
import driverImage from "../assets/driver.jpg"
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
type Location={
    latitude:number,
    longitude:number
}

type Driver = {
    driver_id: number;
    latitude: number;
    longitude: number;
    distance_km: number;
}
type DriverProfile = {
    driver_id: number;
    name: string;
    surname: string;
    rating: number | null;
    total_reviews: number;
    distance_km: number;
};
type RoutePoint = {
    lat: number;
    lng: number;
};
type GoogleMapsProps={
    location:Location|null;
    drivers:Driver[];
    onDriverSelect:(driverId:number)=>void;
    selectedDriver:DriverProfile|null;
    onCloseDriverProfile:()=>void;
    onRideRequest:()=>void;
    onLocationsSelected: (
        pickup: Location,
        destination: Location
    ) => void;
    driverResponse: {
        status: string;
        driver_id: number;
        trip_req_id: number;
    } | null;
    onFindAnotherDriver: () => void;
}

type MapControllerProps = {
    location: Location | null;
};
type FitDriversProps = {
    location: Location | null;
    drivers: Driver[];
};

function MapController({ location }: MapControllerProps) {
    const map = useMap();
    useEffect(() => {
        if (!map || !location) return;

        const position = {
            lat: location.latitude,
            lng: location.longitude
        };

        map.panTo(position);
        map.setZoom(18);

    }, [map, location]);

    return null;
}
function FitDrivers({ drivers,location}:FitDriversProps) {
    const map = useMap();
    const mapsLibrary = useMapsLibrary("core");

    useEffect(() => {
      if(!map|| !mapsLibrary) return
      if (drivers.length === 0) return
      const bounds = new mapsLibrary.LatLngBounds()

      if(location){
        bounds.extend({
            lat:location.latitude,
            lng:location.longitude
        })
      }

      drivers.forEach((driver)=>{
        bounds.extend({
            lat:driver.latitude,
            lng:driver.longitude
        })
      })
      map.fitBounds(bounds,60);
    }, [drivers, map ,location]);
  
    return null;
  }

function Route({
    pickup,
    destination
}: {
    pickup: Location | null;
    destination: Location | null;
}) {
    const [routePath, setRoutePath] =useState<RoutePoint[]>([]);
    const map = useMap();
    const routesLibrary = useMapsLibrary("routes");

    useEffect(() => {

        if (!map || !routesLibrary || !pickup || !destination) {
            return;
        }
        const pickupLocation=pickup
        const destinationLocation=destination
        async function calculateRoute() {

            const { Route } = routesLibrary;

            const result = await Route.computeRoutes({
                origin: {
                    lat: pickupLocation.latitude,
                    lng: pickupLocation.longitude
                },

                destination: {
                    lat: destinationLocation.latitude,
                    lng: destinationLocation.longitude
                },

                travelMode: "DRIVING",

                fields: [
                    "path",
                    "distanceMeters",
                    "durationMillis"
                ]
            });
            const route = result.routes?.[0];

            if (!route) {
                setRoutePath([]);
                return;
            }

            setRoutePath(
                route.path.map((point: { lat: number; lng: number }) => ({
                    lat: point.lat,
                    lng: point.lng
                }))
            );
                    }

        calculateRoute();

    }, [map, routesLibrary, pickup, destination]);
    
    return <>
            {routePath.length > 0 && (
            <Polyline
                path={routePath}
                strokeColor="#2563EB"
                strokeOpacity={0.8}
                strokeWeight={5}
            />
            )}
    </>;
}
function UserGoogleMap({location,drivers,onDriverSelect,selectedDriver,onCloseDriverProfile,onRideRequest,onLocationsSelected,driverResponse,onFindAnotherDriver}:GoogleMapsProps){
    const [showLocationOptions, setShowLocationOptions] = useState(true);
    type SelectionMode = "pickup" | "destination" | null;
    const [selectionMode, setSelectionMode] =useState<SelectionMode>(null);
    const[pickup,setPickup]=useState<Location|null>(null);
    const[destination,setDestination]=useState<Location|null>(null);
    // const [showFindAnother, setShowFindAnother] = useState(true);
    const[showResponseCard,setOpenResponseCard]=useState(false)
    const[showLocationSelectCard,setShowCard]=useState(true)
    const defaultLocation={
        lat:19.0760,
        lng:72.8777
    }
    const mapLocation = location
        ? {
            lat: location.latitude,
            lng: location.longitude
        }
        : defaultLocation;
        useEffect(() => {
            if (driverResponse) {
                setOpenResponseCard(true);
                setShowCard(false)
            }
        }, [driverResponse]);
    useEffect(() => {
        if (pickup && destination) {
            onLocationsSelected(pickup, destination);
        }
    }, [pickup, destination]);

    const trip_req_ID=driverResponse?.trip_req_id
    async function callDriverToLocation(){
        const response=await fetch(`${import.meta.env.VITE_API_URL}/users/call_from_user/${trip_req_ID}`,{
            "method":"POST",
            "credentials":"include",
        })
        const data=await response.json()
        if(data.status==true){
            alert("Driver has been called to your location")
        }
        else{
            alert("Failed to call the driver")
        }
    }

        return (
            <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
        
                <div
                    style={{
                        position: "relative",
                        width: "100%",
                        height: "500px"
                    }}
                >
                    <Map
                        defaultCenter={mapLocation}
                        defaultZoom={14}
                        mapId={import.meta.env.VITE_GOOGLE_MAPS_MAP_ID}
                        style={{
                            width: "100%",
                            height: "100%"
                        }}
                        onClick={(event) => {
                            const lat = event.detail.latLng?.lat;
                            const lng = event.detail.latLng?.lng;
                    
                            if (lat === undefined || lng === undefined) return;
                            const selectedLocation={
                                latitude:lat,
                                longitude:lng
                            }
                            if(selectionMode==="pickup"){
                                setPickup(selectedLocation)
                                setSelectionMode(null);
                            }
                            if(selectionMode==="destination"){
                                setDestination(selectedLocation)
                                setSelectionMode(null);
                            }
                        }}
                    >
        
                        <MapController location={location} />
                        <Route
                            pickup={pickup}
                            destination={destination}
                        />
                        <FitDrivers
                            drivers={drivers}
                            location={location}
                        />
        
                        {/* User Marker */}
                        {location && (
                            <AdvancedMarker position={mapLocation}>
                                <img
                                    src={userImage}
                                    alt="user"
                                    style={{
                                        width: "45px",
                                        height: "45px",
                                        borderRadius: "50%",
                                        objectFit: "cover",
                                        border: "3px solid white",
                                        boxShadow: "0 2px 6px rgba(0,0,0,0.3)"
                                    }}
                                />
                            </AdvancedMarker>
                        )}
        
                        {/* Driver Markers */}
                        {drivers.map((driver) => (
                            <AdvancedMarker
                                key={driver.driver_id}
                                position={{
                                    lat: driver.latitude,
                                    lng: driver.longitude
                                }}
                                onClick={() =>{
                                    onDriverSelect(driver.driver_id);
                                    setShowCard(false);
                                }
                                }
                            >
                                <img
                                    src={driverImage}
                                    alt="Driver"
                                    style={{
                                        width: "45px",
                                        height: "45px",
                                        borderRadius: "50%",
                                        border: "3px solid white",
                                        boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
                                        objectFit: "cover"
                                    }}
                                />
                            </AdvancedMarker>
                        ))}
                        {pickup && (
                            <AdvancedMarker
                                position={{
                                    lat: pickup.latitude,
                                    lng: pickup.longitude
                                }}
                            >
                                <div
                                    style={{
                                        width: "18px",
                                        height: "18px",
                                        backgroundColor: "green",
                                        borderRadius: "50%",
                                        border: "3px solid white",
                                        boxShadow: "0 2px 6px rgba(0,0,0,0.3)"
                                    }}
                                />
                            </AdvancedMarker>
                        )}
                        {destination && (
                            <AdvancedMarker
                                position={{
                                    lat: destination.latitude,
                                    lng: destination.longitude
                                }}
                            >
                                <div
                                    style={{
                                        width: "18px",
                                        height: "18px",
                                        backgroundColor: "red",
                                        borderRadius: "50%",
                                        border: "3px solid white",
                                        boxShadow: "0 2px 6px rgba(0,0,0,0.3)"
                                    }}
                                />
                            </AdvancedMarker>
                        )}
                    </Map>
                    {showLocationSelectCard &&(
                    <div
                    style={{
                        position: "absolute",
                        bottom: "20px",
                        left: "50%",
                        transform:"translateX(-50%)",
                        zIndex: 20,
                        display: "flex",
                        gap: "10px"
                    }}
                    >
                    <button
                        style={buttonStyle}
                        onClick={() => setSelectionMode("pickup")}
                    >
                        Select Pickup
                    </button>

                    <button
                        style={buttonStyle}
                        onClick={() => setSelectionMode("destination")}
                    >
                        Select Destination
                    </button>
                    </div>
                    )}
                    {/* Driver Profile Card */}
                    {selectedDriver && (
                        <div
                            style={{
                                position: "absolute",
                                bottom: "20px",
                                left: "20px",
                                width: "280px",
                                background: "white",
                                borderRadius: "15px",
                                padding: "16px",
                                boxShadow: "0 4px 15px rgba(0,0,0,0.25)",
                                zIndex: 10
                            }}
                        >
                            <button
                                onClick={(e)=>{e.stopPropagation();
                                    onCloseDriverProfile()
                                    setShowCard(true)}}
                                style={{
                                    position: "absolute",
                                    right: "10px",
                                    top: "8px",
                                    border: "none",
                                    backgroundColor: "red",
                                    fontSize: "18px",
                                    cursor: "pointer"
                                }}
                            >
                                ×
                            </button>
        
                            <h2>
                                {selectedDriver.name}{" "}
                                {selectedDriver.surname}
                            </h2>
                            <h3>The driver is {selectedDriver.distance_km}km from your location</h3>
                            <p>
                                ⭐ {selectedDriver.rating ?? "New Driver"}
                            </p>
        
                            <p>
                                📝 {selectedDriver.total_reviews} reviews
                            </p>
        
                            <button style={buttonStyle} onClick={()=>{
                                if(!showLocationOptions){
                                setShowLocationOptions(true)
                                return
                                }
                                if(pickup&&destination){
                                onRideRequest();
                            }}}>
                                {pickup&&destination ? "Confirm Ride" : "Request Ride"}
                            </button>
                            {!pickup&&!destination?<p>Please choose pickup and destination point to request ride</p>:""}
                        </div>
                    )}
                    {driverResponse?.status === "accepted" && showResponseCard &&(
                        <div
                            style={{
                                position: "absolute",
                                bottom: "30px",
                                left: "50%",
                                transform: "translateX(-50%)",
                                backgroundColor: "white",
                                padding: "20px",
                                borderRadius: "12px",
                                boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
                                zIndex: 10,
                                minWidth: "300px",
                                textAlign: "center"
                            }}
                        >
                                    {/* Close button */}
                        <button
                            onClick={() => setOpenResponseCard(false)}
                            style={{
                                position: "absolute",
                                top: "8px",
                                right: "10px",
                                border: "none",
                                background: "transparent",
                                fontSize: "22px",
                                fontWeight: "bold",
                                cursor: "pointer",
                                color: "#555"
                            }}
                        >
                            ×
                        </button>
                            <h3>Ride Accepted 🎉</h3>

                            <p>
                                Driver {driverResponse.driver_id} has accepted your ride.
                            </p>

                            <p>
                                Trip ID: {driverResponse.trip_req_id}
                            </p>
                            <button style={buttonStyle} onClick={callDriverToLocation}>Call the driver to pickup point</button>
                        </div>
                    )}
                    {driverResponse?.status === "rejected" && showResponseCard && (
                        <div
                            style={{
                                position: "absolute",
                                bottom: "30px",
                                left: "50%",
                                transform: "translateX(-50%)",
                                backgroundColor: "white",
                                padding: "20px",
                                borderRadius: "12px",
                                boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
                                zIndex: 10,
                                minWidth: "300px",
                                textAlign: "center"
                            }}
                        >
                                {/* Close button */}
                        <button
                            onClick={() => setOpenResponseCard(false)}
                            style={{
                                position: "absolute",
                                top: "8px",
                                right: "10px",
                                border: "none",
                                background: "transparent",
                                fontSize: "22px",
                                fontWeight: "bold",
                                cursor: "pointer",
                                color: "#555"
                            }}
                        >
                            ×
                        </button>
                            <h3>Let's find another ride</h3>

                            <p>
                                This driver isn't available for your trip right now.
                            </p>

                            <p>
                                You can choose another nearby driver.
                            </p>

                        <button
                                style={{
                                backgroundColor: "#2563EB",
                                color: "white",
                                border: "none",
                                borderRadius: "8px",
                                padding: "10px 18px",
                                cursor: "pointer",
                                fontWeight: "600"
                                }}
                            onClick={onFindAnotherDriver}
                            >
                            Find Another Driver
                        </button>
                    </div>
                    )}
                        
                </div>
        
            </APIProvider>
        );
}
export default UserGoogleMap;