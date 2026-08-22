from DataBase.Connection import SessionLocal
from UserSide.models.User import User
from sqlalchemy.exc import IntegrityError
class UserRepository:
    @staticmethod
    def add(user):
        db=SessionLocal()
        try:
            db.add(user)      
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            print("Phone number already registered!")
        finally:
            db.close()

    @staticmethod
    def find_by_email(emailID):
        db=SessionLocal()
        try:
            print("Email Recieved: ",repr(emailID))
            users=db.query(User).all()
            for user in users:
                print(
                    "DB:",
                    user.id,
                    repr(user.emailID)
                )
            user = db.query(User).filter(User.emailID == emailID).first()
            print("Matched User:", user)
            return user
        finally:
            db.close()

    def update_status(user_id,is_online,is_available,last_seen=None):
        db=SessionLocal()
        try:
            user=db.query(User).filter(User.id==user_id).first()
            if user is None:
                return None
            user.is_online=is_online
            user.is_available=is_available
            if last_seen is not None:
                user.last_seen=last_seen
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()