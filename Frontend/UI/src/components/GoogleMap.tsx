import { APIProvider,Map,AdvancedMarker,useMap,useMapsLibrary } from "@vis.gl/react-google-maps"
import { useEffect } from 'react'
import userImage from "../assets/user.png";
import driverImage from "../assets/driver.jpg"
type Location={
    latitude:number,
    longitude:number
}

type Driver = {
    driver_id: number;
    latitude: number;
    longitude: number;
    distance_km?: number;
}
type DriverProfile = {
    driver_id: number;
    name: string;
    surname: string;
    rating: number | null;
    total_reviews: number;
};

type GoogleMapsProps={
    location:Location|null;
    drivers:Driver[];
    onDriverSelect:(driverId:number)=>void;
    selectedDriver:DriverProfile|null;
    onCloseDriverProfile:()=>void;
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
function GoogleMap({location,drivers,onDriverSelect,selectedDriver,onCloseDriverProfile}:GoogleMapsProps){
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
    return(
        <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
        <Map
        defaultCenter={mapLocation}
        defaultZoom={14}
        mapId={import.meta.env.VITE_GOOGLE_MAPS_MAP_ID}
        style={{width:"100%",
            height:"500px"
        }}>
            <MapController location={location} />
            <FitDrivers drivers={drivers} location={location}></FitDrivers>
            {location && (<AdvancedMarker position={mapLocation}>    
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
            }}/>
            </AdvancedMarker>
            )}
            {drivers.map((driver) => (
            <AdvancedMarker
                key={driver.driver_id}
                position={{
                    lat: driver.latitude,
                    lng: driver.longitude
                }}
                onClick={() => onDriverSelect(driver.driver_id)}
            >
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
                onClick={onCloseDriverProfile}
                style={{
                    position: "absolute",
                    right: "10px",
                    top: "8px",
                    border: "none",
                    background: "transparent",
                    fontSize: "18px",
                    cursor: "pointer"
                }}
            >
                ×
            </button>
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
            }}/>
                                <h3>
                        {selectedDriver.name}{" "} {selectedDriver.surname}
                    </h3>

                    <p>
                        ⭐ {selectedDriver.rating ?? "New Driver"}
                    </p>

                    <p>
                        📝 {selectedDriver.total_reviews} reviews
                    </p>

                    <button>
                        Request Ride
                    </button>
            </div>
                )}
            </AdvancedMarker>
            ))}
            </Map>
        </APIProvider>
    );
}
export default GoogleMap;