from pydantic import BaseModel

class DataReceive(BaseModel):
    message: str

class DataSend(BaseModel):
    pass
