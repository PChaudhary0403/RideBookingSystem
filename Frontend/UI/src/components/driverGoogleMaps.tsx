    import { APIProvider,Map,AdvancedMarker,useMap } from "@vis.gl/react-google-maps"
    import { useEffect } from 'react'
    // import userImage from "../assets/user.png";
    import driverImage from "../assets/driver.jpg"
    type Location={
        latitude:number,
        longitude:number
    }

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
    type DriverTripRequest = {
        trip_id: number;
        user_id: number;
        status: string;
        created_at: string;
    };
    
    type GoogleMapsProps = {
        location: Location | null;
        requests: DriverTripRequest[];
    };

    type MapControllerProps = {
        location: Location | null;
    };
    // type FitDriversProps = {
    //     location: Location | null;
    // };
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
    function DriverGoogleMap({location,requests}:GoogleMapsProps){
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
                        >
            
                            <MapController location={location} />
            
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
                        </Map>
                        <div
                            style={{
                                position: "absolute",
                                top: "20px",
                                right: "20px",
                                width: "300px",
                                maxHeight: "400px",
                                overflowY: "auto",
                                backgroundColor: "white",
                                borderRadius: "12px",
                                padding: "16px",
                                boxShadow: "0 4px 15px rgba(0,0,0,0.25)",
                                zIndex: 10
                            }}
                        >
                        <h3>Ride Requests</h3>

                        {requests.length === 0 ? (
                            <p>No pending ride requests</p>
                        ) : (
                            requests.map((request) => (
                                <div
                                    key={request.trip_id}
                                    style={{
                                        border: "1px solid #ddd",
                                        borderRadius: "10px",
                                        padding: "12px",
                                        marginBottom: "10px",
                                        backgroundColor: "#F8FAFC"
                                    }}
                                >
                                    <h4>
                                        New Ride Request
                                    </h4>

                                    <p>
                                        User ID: {request.user_id}
                                    </p>

                                    <p>
                                        Status: {request.status}
                                    </p>

                                    <p>
                                        Requested:{" "}
                                        {new Date(request.created_at).toLocaleTimeString()}
                                    </p>

                                    <div>
                                    <button
                                        style={{
                                            backgroundColor: "#16A34A",
                                            color: "white",
                                            border: "none",
                                            borderRadius: "6px",
                                            padding: "8px 12px",
                                            marginRight: "8px",
                                            cursor: "pointer"
                                        }}
                                    >
                                    Accept
                                </button>

                                <button
                                style={{
                                    backgroundColor: "#DC2626",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "6px",
                                    padding: "8px 12px",
                                    cursor: "pointer"
                                }}
                            >
                                Reject
                                </button>
                                </div>
                            </div>
                                ))
                            )}
                            </div>
                        </div>
                </APIProvider>
            )
    }
    export default DriverGoogleMap;