from pydantic import BaseModel, EmailStr


class MessageCreate(BaseModel):
    to: EmailStr
    sender: EmailStr = None
    message: str


class Message(MessageCreate):
    id: str
