    import { APIProvider,Map,AdvancedMarker,useMap,useMapsLibrary,Polyline } from "@vis.gl/react-google-maps"
    import { useEffect,useState } from "react";
    // import userImage from "../assets/user.png";
    import driverImage from "../assets/driver.jpg"
    import type { DriverTripRequest } from "../types/trip"
    import type { Dispatch, SetStateAction } from "react";
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
    type RoutePoint = {
        lat: number;
        lng: number;
    };
    // type Driver = {
    //     driver_id: number;
    //     latitude: number;
    //     longitude: number;
    //     distance_km: number;
    // }

    // type DriverProfile = {
    //     driver_id: number;
    //     name: string;
    //     surname: string;
    //     rating: number | null;
    //     total_reviews: number;
    //     distance_km: number;
    // };
    
    type GoogleMapsProps = {
        location: Location | null;
        requests: DriverTripRequest[];
        setRequests: React.Dispatch<
        React.SetStateAction<DriverTripRequest[]>
        >;
        selectedRequest: DriverTripRequest | null;
        setSelectedRequest: Dispatch<SetStateAction<DriverTripRequest | null>>
        Call:boolean;
    };

    type MapControllerProps = {
        location?: Location | null;
        pickup?: Location | null;
    };
    // type FitDriversProps = {
    //     location: Location | null;
    // };
    function MapController({ location,pickup }: MapControllerProps) {
        const map = useMap();

        useEffect(() => {
            if (!map) return;
            const target=pickup??location
            if(!target) return

            const position = {
                lat: target.latitude,
                lng: target.longitude
            };

            map.panTo(position);
            map.setZoom(18);

        }, [map, location,pickup]);

        return null;
    }
    // function FitDrivers({ drivers,location}:FitDriversProps) {
    //     const map = useMap();
    //     const mapsLibrary = useMapsLibrary("core");

    //     useEffect(() => {
    //       if(!map|| !mapsLibrary) return
    //       if (drivers.length === 0) return
    //       const bounds = new mapsLibrary.LatLngBounds()

    //       if(location){
    //         bounds.extend({
    //             lat:location.latitude,
    //             lng:location.longitude
    //         })
    //       }

    //       drivers.forEach((driver)=>{
    //         bounds.extend({
    //             lat:driver.latitude,
    //             lng:driver.longitude
    //         })
    //       })
    //       map.fitBounds(bounds,60);
    //     }, [drivers, map ,location]);
    
    //     return null;
    //   }

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
            setRoutePath([]);
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

    function DriverGoogleMap({location,requests,setRequests,selectedRequest,setSelectedRequest,Call}:GoogleMapsProps){
        const [showRequests, setShowRequests] = useState(true);
        const [agreement,setAgreement]=useState("")
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
            async function closeRequest(tripId: number) {
                const response = await fetch(
                    `${import.meta.env.VITE_API_URL}/drivers/dismiss-request/${tripId}`,
                    {
                        method: "PATCH",
                        credentials: "include"
                    }
                );
            
                const data = await response.json();
            
                if (response.ok && data.status === true) {
            
                    setRequests((prev) =>
                        prev.filter(
                            (request) => request.trip_req_id !== tripId
                        )
                    );
            
                    setSelectedRequest(null);
                }
            }
            type TripStatus =
                | "pending"
                | "accepted"
                | "rejected"
                | "completed"
                | "dismiss"
                | "cancelled";
            async function get_agreement(tripId:number,agreementStatus:TripStatus){
                const response=await fetch(`${import.meta.env.VITE_API_URL}/drivers/update-status/${tripId}`,{
                    method:"PATCH",
                    credentials:"include",
                    headers:{
                        "Content-Type":"application/json"
                    },
                    body:JSON.stringify({
                        status:agreementStatus
                    })
                })
                const data=await response.json()
                if(data.status===true){
                    alert(`data sent ${agreement}`)
                    console.log("Request accepted")
                }
        }
            return (
                <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
            
                    <div
                        style={{
                            position: "relative",
                            width: "100%",
                            height: "100vh"
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
                        >
            
                            <MapController location={location} pickup={selectedRequest?{
                                latitude:selectedRequest.pickup_lat,
                                longitude:selectedRequest.pickup_long
                            }:null} />

                        {selectedRequest && (
                        <Route
                            pickup={{
                                latitude: selectedRequest.pickup_lat,
                                longitude: selectedRequest.pickup_long
                            }}
                            destination={{
                                latitude: selectedRequest.dest_lat,
                                longitude: selectedRequest.dest_long
                            }}
                        />
                        )}
            
                        {/* User Marker */}
                        {location && (
                            <AdvancedMarker position={mapLocation}>
                                <img
                                    src={driverImage}
                                    alt="driver"
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
                {/* Selected Request */}
                {selectedRequest && (
                    <>
                        {/* Pickup */}
                        <AdvancedMarker
                            position={{
                                lat: selectedRequest.pickup_lat,
                                lng: selectedRequest.pickup_long
                            }}
                        >
                            <div
                                style={{
                                    fontSize: "30px"
                                }}
                            >
                                📍
                            </div>
                        </AdvancedMarker>

                        {/* Destination */}
                        <AdvancedMarker
                            position={{
                                lat: selectedRequest.dest_lat,
                                lng: selectedRequest.dest_long
                            }}
                        >
                            <div
                                style={{
                                    fontSize: "30px"
                                }}
                            >
                                🏁
                            </div>
                        </AdvancedMarker>
                    </>
                )}
                        </Map>

                    {Call && (
                        <div
                            style={{
                                position: "absolute",
                                top: "20px",
                                left: "50%",
                                transform: "translateX(-50%)",
                                zIndex: 20,
                                width: "360px",
                                backgroundColor: "white",
                                borderRadius: "12px",
                                padding: "18px",
                                boxShadow: "0 4px 15px rgba(0,0,0,0.25)",
                                textAlign: "center"
                            }}
                        >
                            <h3 style={{ margin: "0 0 8px" }}>
                                Ride Confirmation
                            </h3>

                            <p style={{ margin: "0 0 16px", color: "#555" }}>
                                The passenger has confirmed the ride and is ready
                                for pickup.
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
                            >
                                Proceed to Pickup
                            </button>
                        </div>
                    )}
                    {!showRequests && (
                    <button
                        onClick={() => setShowRequests(true)}
                        style={{
                            position: "absolute",
                            top: "40px",
                            right: "40px",
                            zIndex: 10,
                            backgroundColor: "#2563EB",
                            color: "white",
                            border: "none",
                            borderRadius: "8px",
                            padding: "10px 16px",
                            cursor: "pointer",
                            fontWeight: "600"
                        }}
                    >
                        Show Requests
                    </button>
                    )}

                    {showRequests&&(
                        <div
                style={{
                    position: "absolute",
                    top: "20px",
                    right: "20px",
                    width: "320px",
                    maxHeight: "450px",
                    overflowY: "auto",
                    backgroundColor: "white",
                    borderRadius: "12px",
                    padding: "16px",
                    boxShadow: "0 4px 15px rgba(0,0,0,0.25)",
                    zIndex: 10
                }}
            >
                    <button
                        onClick={() => setShowRequests(false)}
                        style={{
                            position: "absolute",
                            top: "10px",
                            right: "10px",
                            border: "none",
                            background: "transparent",
                            fontSize: "20px",
                            cursor: "pointer"
                        }}
                    >
                        ✕
                    </button>
                <h3>Ride Requests</h3>

                {requests.length === 0 ? (
                    <p>No pending ride requests</p>
                ) : (
                    requests.map((request) => (
                        <div
                            key={request.trip_req_id}
                            style={{
                                border: "1px solid #ddd",
                                borderRadius: "10px",
                                padding: "12px",
                                marginBottom: "10px",
                                backgroundColor: "#F8FAFC"
                            }}
                        >
                        <button onClick={()=>{closeRequest(request.trip_req_id),setAgreement("declined")}}>
                            ✕
                        </button>
                            <h4>New Ride Request</h4>

                            <p>
                                User ID: {request.user_id}
                            </p>

                            <p>
                                Status: {request.status}
                            </p>

                            <p>
                                Requested:{" "}
                                {new Date(
                                    request.created_at
                                ).toLocaleTimeString()}
                            </p>

                            <button
                                style={buttonStyle}
                                onClick={(e) =>{e.stopPropagation();
                                    setSelectedRequest(request);
                                }}
                            >
                                View Route
                            </button>

                            <button
                                style={{
                                    ...buttonStyle,
                                    backgroundColor: "#16A34A"
                                }}
                                onClick={(e)=>{e.stopPropagation();
                                    setAgreement("accepted");
                                    get_agreement(request.trip_req_id,"accepted")}}
                            >
                                Accept
                            </button>

                            <button
                                style={{
                                    ...buttonStyle,
                                    backgroundColor: "#DC2626"
                                }}
                                onClick={(e)=>{e.stopPropagation();
                                    setAgreement("rejected");
                                    get_agreement(request.trip_req_id,"rejected")}}
                            >
                                Reject
                            </button>
                        </div>
                    ))
                )}
            </div>)}
                        </div>
                </APIProvider>
            )
    }
    export default DriverGoogleMap;