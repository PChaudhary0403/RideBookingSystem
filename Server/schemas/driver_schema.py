from pydantic import BaseModel
class DriverCreate(BaseModel):
        name:str
        surname:str
        email:str
        phone:str
        password:str
        address:str
        licenceno:str

class DriverLogin(BaseModel):
        email:str
        password:str
