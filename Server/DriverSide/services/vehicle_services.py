from DriverSide.models.vehicle import Vehicle
from DriverSide.repositories.vehicle_repo import VehicleRepository

class VehicleService:
    def register_vehicle(self,
                driver_id,
                name,
                vehicle_type,
                registration_number,
                associated_licence,
                city,
                state,
                mileage,
                parent_company,
                model,
                color):
        
        vehicle=Vehicle(
                driver_id=driver_id,
                name=name,
                vehicle_type=vehicle_type,
                registration_number=registration_number,
                associated_licence=associated_licence,
                city=city,
                state=state,
                mileage=mileage,
                parent_company=parent_company,
                model=model,
                color=color)
        VehicleRepository.add(vehicle)
        return vehicle

    def get_driver_vehicles(self,driver_id):
        return VehicleRepository.show_vehicle(driver_id)
