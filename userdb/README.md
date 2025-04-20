# UserDB Service

The UserDB service is a gRPC-based user database management service for the ArtificialInsight platform. It provides functionality for creating, retrieving, updating, and deleting user records, as well as tracking usage statistics like request counts.

## Features

- User CRUD operations (Create, Read, Update, Delete)
- User request count tracking
- Token-based authentication
- Language preference management
- LLM (Language Learning Model) preference storage

## Technology Stack

- **Rust**: For efficient, reliable server implementation
- **tonic**: gRPC framework for Rust
- **sqlx**: Asynchronous SQL toolkit for Rust
- **PostgreSQL**: Database backend
- **tokio**: Asynchronous runtime
- **Protocol Buffers**: For API definition and data serialization

## Configuration

The service can be configured using environment variables:

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `USERDB_PG_URL` | PostgreSQL connection string | `""` (empty string) |
| `USERDB_ADDR` | Host address to bind the service | `localhost` |
| `USERDB_PORT` | Port to bind the service | `2780` |

Example PostgreSQL connection string: `postgres://username:password@localhost/userdb`

## Building the Service

### Prerequisites

- Rust 1.67 or newer
- PostgreSQL database
- Protocol Buffer compiler (protoc)

### Build Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/ArtificialInsight/userdb.git
   cd userdb
   ```

2. Build the project:
   ```bash
   cargo build --release
   ```

## Running the Service

1. Ensure PostgreSQL is running and accessible
2. Set environment variables (optional, or use defaults)
3. Run the service:
   ```bash
   cargo run --release
   ```

The service will automatically:
- Create the database if it doesn't exist
- Run any pending migrations
- Start the gRPC server on the configured address/port

## API Documentation

The UserDB service provides the following gRPC endpoints:

### GetUser

Retrieves a user by their token.

```protobuf
rpc GetUser (GetUserRequest) returns (GetUserResponse)
```

### CreateUser

Creates a new user and returns their token.

```protobuf
rpc CreateUser (CreateUserRequest) returns (CreateUserResponse)
```

### UpdateUser

Updates an existing user's information.

```protobuf
rpc UpdateUser (UpdateUserRequest) returns (UpdateUserResponse)
```

### DeleteUser

Deletes a user by their token.

```protobuf
rpc DeleteUser (DeleteUserRequest) returns (DeleteUserResponse)
```

### UpdateUserRequestCount

Increments the number of requests made by a user.

```protobuf
rpc UpdateUserRequestCount (UpdateUserRequestCountRequest) returns (UpdateUserRequestCountResponse)
```

## Database Schema

The service uses a PostgreSQL database with the following schema:

```sql
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    token VARCHAR(256) NOT NULL,
    language VARCHAR(50) NOT NULL DEFAULT 'en',
    llm_preference VARCHAR(100),
    description TEXT,
    num_requests INTEGER NOT NULL DEFAULT 0
);
```

## Development

### Running Migrations

The service automatically runs migrations on startup. To manually run migrations:

```bash
cargo install sqlx-cli
sqlx migrate run --database-url postgres://username:password@localhost/userdb
```

### Testing

To run the test suite:

```bash
cargo test
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
