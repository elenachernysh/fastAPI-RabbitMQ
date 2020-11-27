from pydantic import BaseModel, EmailStr


class MessageRead(BaseModel):
    sender: EmailStr
    recipient: EmailStr = None


class MessageCreate(BaseModel):
    recipient: EmailStr
    sender: EmailStr = None
    message: str


class Message(MessageCreate):
    id: str