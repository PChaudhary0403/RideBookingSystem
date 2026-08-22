from pydantic import BaseModel
class UserCreate(BaseModel):
    name:str
    phone:str
    emailID:str
    password:str

class UserLogin(BaseModel):
    emailID:str
    password:str