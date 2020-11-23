from schemas import messages as message_schema
import aio_pika


async def on_message(message: aio_pika.IncomingMessage):
    # TODO process messages
    print(message.body)
    message.ack()
    return message


async def post_message_in_queue(message: message_schema.MessageCreate):
    try:
        connection = await aio_pika.connect_robust(
            "amqp://guest:guest@localhost:8081/%2f"
        )
        if not connection:
            raise Exception('Broken connection to RabbitMQ')
        channel = await connection.channel()
        queue = await channel.declare_queue('test', durable=True)
        await queue.consume(
            callback=on_message,
            no_ack=False,
        )
        return message
    except ConnectionError:
        raise Exception('Broken connection to RabbitMQ')

