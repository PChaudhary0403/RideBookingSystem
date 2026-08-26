import { APIProvider,Map,AdvancedMarker,useMap } from "@vis.gl/react-google-maps"
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

type GoogleMapsProps={
    location:Location|null;
    drivers:Driver[];
}
type MapControllerProps = {
    location: Location | null;
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
async function getDriverProfile(driverId: number) {
    const response = await fetch(
        `${import.meta.env.VITE_API_URL}/drivers/${driverId}/profile`,
        {
            credentials: "include"
        }
    )
}
function FitDrivers({ drivers,location}:GoogleMapsProps) {
    const map = useMap();
  
    useEffect(() => {
      if(!map) return
      if (drivers.length === 0) return
      const bounds = new google.maps.LatLngBounds()

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
function GoogleMap({location,drivers}:GoogleMapsProps){
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
                onClick={() => getDriverProfile(driver.driver_id)}
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
            }}/>
            </AdvancedMarker>
            ))}
            </Map>
        </APIProvider>
    );
}
export default GoogleMap;