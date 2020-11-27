import json
import aio_pika
from typing import Tuple, Union
from uuid import UUID
from functools import wraps
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.responses import JSONResponse
from schemas import messages
from fastapi.security import OAuth2PasswordBearer
from schemas.users import UserBase
from utils.users import get_user_by_token, get_user_by_email
from pydantic import EmailStr

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def validate_user_existence(user_email: str):
    recipient = await get_user_by_email(email=user_email)
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recipient credentials (no such user)"
        )


def get_sender(decorated):
    @wraps(decorated)
    async def wrapper(message: Union[messages.MessageRead, messages.MessageCreate],
                      request: Request,
                      current_user: UserBase = Depends(get_current_user)):
        await validate_user_existence(user_email=message.recipient)
        if current_user == message.recipient:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="You can't be both a sender and a recipient."
            )
        message.sender = current_user
        return await decorated(message, request)
    return wrapper


def validate_token(token: str) -> bool:
    try:
        return bool(UUID(token, version=4))
    except ValueError:
        return False


async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    user = await get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return dict(user).get('email')


async def rabbit_connect(routing_key: str, request: Request) -> Tuple[aio_pika.Channel, aio_pika.Queue]:
    connection = request.app.state.connection
    channel = await connection.channel()
    queue = await channel.declare_queue(routing_key, durable=True)
    return channel, queue


@router.post("/message", response_model=messages.MessageCreate)
@get_sender
async def create_message(message: messages.MessageCreate,
                         request: Request,
                         current_user: UserBase = Depends(get_current_user)):
    """ Post new message to RabbitMQ (queue name equals message sender : message recipient) """
    try:
        routing_key = json.dumps({message.sender: message.recipient})
        channel, queue = await rabbit_connect(routing_key=routing_key, request=request)
        message_to_send = json.dumps(dict(message))
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_to_send.encode()),
            routing_key=routing_key,
        )
        return message
    except ConnectionError:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Broken connection to RabbitMQ"
        )


@router.post("/receive_message")
async def get_message(message: messages.MessageRead,
                      request: Request,
                      current_user: UserBase = Depends(get_current_user)):
    """ Get one message (the oldest because FIFO) from sender """
    if message.sender == current_user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="You can't be both a sender and a recipient."
        )
    routing_key = json.dumps({message.sender: current_user})
    _, queue = await rabbit_connect(routing_key=routing_key, request=request)
    try:
        message = await queue.get(no_ack=True)
        return JSONResponse(content=json.loads(message.body))
    except aio_pika.exceptions.QueueEmpty:
        import traceback
        traceback.print_exc()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
