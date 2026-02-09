# FastAPI Jwt Auth

Fully **asynchronous** **FastAPI** server that uses **JWT** authentication with **PostgreSQL**.
Uses **Docker** and **Docker Compose** for deployable setup.

Checkout notes.txt for more useful information

## Important Design Architecture Decision

Complete separation of **Pydantic** Schemas (DTOs) and **SQLAlchemy** ORM (Models) to minimize human-error of accidentally showing internal fields to users.

## To run

Install Docker and Docker Compose
To run:
```
docker compose up --build
```
To stop
```
docker compose down
```

## To use
While the server is running, using a browser, navigate to 
```
localhost:5000/docs
```    
This will show you the endpoints

## Endpoints
```
/api/auth/signup
/api/auth/login
/api/auth/logout
/api/auth/refresh
/api/protected/me <--This needs Authorization: Bearer <access token> header
```