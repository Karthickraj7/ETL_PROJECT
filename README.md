# Data Engineering  Task

A REST API for user management with ETL pipeline for data grouping.

## Features
- RESTful API with CRUD operations for users, employment, and bank details
- PostgreSQL database with proper relationships and constraints
- ETL pipeline to group users by bank, company, and pincode
- Docker containerization for easy deployment
- Comprehensive Postman collection for API testing

## Prerequisites
- Docker and Docker Compose
- Python 3.14 (for local development)

## Quick Start

### Using Docker (Recommended)
1. Clone the repository
2. Run: docker-compose up --build
3. API will be available at: http://localhost:5000
4. Database will be available at: localhost:5432

### Local Development
1. Install PostgreSQL and create a database named userdb
2. Create virtual environment: python -m venv venv
3. Activate venv: source venv/bin/activate (Linux/Mac) or venv\Scripts\activate (Windows)
4. Install dependencies: pip install -r service/requirements.txt
5. Set environment variable: export DATABASE_URL=postgresql://postgres:password@localhost:5432/userdb
6. Run the app: cd service && python app.py

## API Endpoints
### Users
- POST /users - Create new user with optional employment and bank details
- GET /users - Get all users (optional filters: company, bank, pincode)
- GET /users/{id} - Get specific user with all details
- PUT /users/{id} - Update user information
- DELETE /users/{id} - Delete user and cascade related data


## ETL Pipeline
Run the ETL script to group users:
```bash
cd etl
python group_users.py --db-uri "postgresql://postgres:password@localhost:5432/userdb" --output-dir ./output