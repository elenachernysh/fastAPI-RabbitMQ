import json
from uuid import UUID
from functools import wraps
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.responses import JSONResponse
from schemas import messages
from fastapi.security import OAuth2PasswordBearer
from schemas.users import UserBase
from utils.users import get_user_by_token
import aio_pika

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_sender(decorated):
    @wraps(decorated)
    async def wrapper(message: messages.MessageCreate, current_user: UserBase = Depends(get_current_user), *args, **kwargs):
        sender = dict(current_user).get('email')
        message.sender = sender
        return await decorated(message, *args, **kwargs)
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
    return user


@router.post("/message", response_model=messages.MessageCreate)
@get_sender
async def create_message(message: messages.MessageCreate,
                         request: Request,
                         current_user: UserBase = Depends(get_current_user)):
    """ Post new message to RabbitMQ (queue name equals message sender : message recipient) """
    try:
        connection = request.app.state.connection
        routing_key = json.dumps({message.sender: message.to})
        channel = await connection.channel()
        queue = await channel.declare_queue(routing_key, durable=True)
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
async def get_message(sender: messages.MessageSender,
                      request: Request, current_user:
                      UserBase = Depends(get_current_user)):
    """ Get one message (the oldest because FIFO) from sender """
    connection = request.app.state.connection
    routing_key = json.dumps({sender.email: dict(current_user).get('email')})
    channel = await connection.channel()
    queue = await channel.declare_queue(routing_key, durable=True)
    try:
        message = await queue.get(no_ack=True)
        return JSONResponse(content=json.loads(message.body))
    except aio_pika.exceptions.QueueEmpty:
        import traceback
        traceback.print_exc()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
