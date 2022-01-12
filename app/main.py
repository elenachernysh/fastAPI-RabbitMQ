import uvicorn
import aio_pika
from fastapi import FastAPI
from models.database import database
from routers import users, messages
from os import environ

app = FastAPI()
RABBIT_HOST = environ.get("RABBIT_HOST", "localhost")


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


async def subscribe_to_rabbit_queue():
    """ Store a connection pool to RabbitMQ"""
    try:
        app.state.connection = await aio_pika.connect_robust(
                f"amqp://guest:guest@{RABBIT_HOST}:8080/%2f"
            )
    except ConnectionError:
        raise Exception('Broken connection to RabbitMQ')


app.include_router(users.router)
app.include_router(messages.router)
app.add_event_handler("startup", subscribe_to_rabbit_queue)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)


# docker run --hostname localhost -p 8080:5672 -p 15672:15672 rabbitmq:3-management
