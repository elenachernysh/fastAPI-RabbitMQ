from functools import wraps
from fastapi import APIRouter, HTTPException, Depends, status, Request
from schemas import messages
from utils import messages as messages_utils
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


def validate_token(token: str):
    return bool(31 < len(token) < 37)


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
async def create_message(message: messages.MessageCreate, request: Request, current_user: UserBase = Depends(get_current_user)):
    try:
        connection = request.app.state.connection
        routing_key = message.sender
        channel = await connection.channel()
        queue = await channel.declare_queue(routing_key)
        await channel.default_exchange.publish(
            aio_pika.Message(body="Hello {}".format(routing_key).encode()),
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

    # return await messages_utils.post_message_in_queue(message=message)
