// types/trip.ts

export type DriverTripRequest = {
    trip_id: number;
    user_id: number;
    pickup_lat: number;
    pickup_long: number;
    dest_lat: number;
    dest_long: number;
    status: string;
    created_at: string;
};