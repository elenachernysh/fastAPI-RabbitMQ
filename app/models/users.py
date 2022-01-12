import sqlalchemy
from sqlalchemy.dialects.postgresql import UUID


metadata = sqlalchemy.MetaData()

users_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String(40), unique=True, index=True),
    sqlalchemy.Column("name", sqlalchemy.String(100)),
    sqlalchemy.Column("hashed_password", sqlalchemy.String()),
    sqlalchemy.Column(
        "is_active",
        sqlalchemy.Boolean(),
        server_default=sqlalchemy.sql.expression.true(),
        nullable=False,
    ),
)


tokens_table = sqlalchemy.Table(
    "tokens",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(
        "token",
        UUID(as_uuid=False),
        server_default=sqlalchemy.text("uuid_generate_v4()"),
        unique=True,
        nullable=False,
        index=True,
    ),
    sqlalchemy.Column("expires", sqlalchemy.DateTime()),
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id")),
)

# to see the list of loaded extensions query the view pg_extension as such:
# select * from pg_extension; or \df (for DB!!, not in general)

# CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
# After the uuid-ossp extension is successfully loaded,
# you should see it in the pg_extension view & the function uuid_generate_v4 should be available.
# more information about uuid https://www.postgresql.org/docs/12/uuid-ossp.html
