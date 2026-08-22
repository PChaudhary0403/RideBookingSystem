import { APIProvider,Map,AdvancedMarker,useMap } from "@vis.gl/react-google-maps"
import { useEffect } from 'react'
import userImage from "../assets/user.png";
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
            {location && (<AdvancedMarker position={mapLocation}>    
            <img
            src={userImage}
            alt="User"
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
            >
                🚗
            </AdvancedMarker>
            ))}
            </Map>
        </APIProvider>
    );
}
export default GoogleMap;