from DataBase.Connection import SessionLocal
from DriverSide.models.Driver import Rider

class RiderRepository:
    @staticmethod
    def add(rider):
        db=SessionLocal()
        db.add(rider)
        db.commit()
        db.refresh(rider)
        db.close()

    @staticmethod
    def find_by_email(email):
        db=SessionLocal()
        try:
            print("Email Recieved: ",repr(email))
            riders=db.query(Rider).all()
            for rider in riders:
                print(
                    "DB:",
                    rider.id,
                    repr(rider.email)
                )
            rider = db.query(Rider).filter(Rider.email == email).first()
            print("Matched rider:", rider)
            return rider
        finally:
            db.close()

    @staticmethod
    def find_by_id(driver_id):
        db=SessionLocal()
        try:
            return db.query(Rider).filter(Rider.id==driver_id).first()
        finally:
            db.close()
