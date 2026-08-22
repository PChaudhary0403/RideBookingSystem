from DataBase.Connection import Base,engine
from DataBase.Connection import SessionLocal
from DriverSide.models.Driver import Rider
from DriverSide.services.rider_services import RiderService
from DriverSide.services.vehicle_services import VehicleService,Vehicle
from DriverSide.models.vehicle import VehicleType
from UserSide.models.User import User
from UserSide.services.user_services import UserService
db=SessionLocal()
Base.metadata.create_all(engine)
# name,
# vehicle_type,
# registration_number,
# city,
# state,
# mileage,
# parent_company,
# model,
# color
# vehicle_service=VehicleService()
# vehicle_service.register_vehicle("SanjuTaxi",VehicleType.CAR,"MH02AC1254","Mumbai","Maharashtra",10,"Mahindra","Ertica","Black")
# print("vehicle added")
rider=db.query(Rider).first()
# # user=User()
# vehicle=db.query(Vehicle).filter(Vehicle.id==1).first()
for vehicle in rider.vehicles:
    print(vehicle.name)
    print(vehicle.registration_number)
# vehicle.rider=rider
# db.commit()

print("relation commited")

