# Test project with FastAPI & RabbitMQ

There will be a project description... As soon, as I invent smth to write.

## Getting Started

### Database

PostgreSQL, database needs the extension 'uuid-ossp' (uuid_generate_v4).

### RabbitMQ

```
docker run --hostname localhost -p 8080:5672 -p 15672:15672 rabbitmq:3-management
```
http://localhost:15672/ - web-interface
http://localhost:8080/ - api-requests
