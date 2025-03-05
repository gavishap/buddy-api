# Waggy API

A FastAPI backend for the Waggy Sitters pet sitting application. This API provides endpoints for user authentication, pet management, booking services, and communication between pet owners and sitters.

## Features

- User authentication with JWT
- User profile management
- Pet profile management
- Booking and scheduling
- Sitter search and filtering
- Messaging between owners and sitters
- MongoDB integration

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT with Python-JOSE
- **Password Hashing**: Passlib with BCrypt
- **Data Validation**: Pydantic
- **Environment Variables**: Python-dotenv

## Getting Started

### Prerequisites

- Python 3.8+
- MongoDB (local or Atlas)
- Virtual environment (recommended)

### Installation

1. Clone the repository

```bash
git clone https://github.com/yourusername/waggy-api.git
cd waggy-api
```

2. Create and activate a virtual environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set up environment variables

- Copy `.env.example` to `.env`
- Update the values in `.env` with your configuration

5. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the application is running, you can access:

- Interactive API documentation: http://localhost:8000/docs
- Alternative API documentation: http://localhost:8000/redoc

## Project Structure

```
waggy-api/
├── app/
│   ├── api/           # API endpoints
│   │   ├── deps.py    # Dependencies (auth, etc.)
│   │   └── routes/    # API route modules
│   ├── core/          # Core functionality
│   │   ├── config.py  # App configuration
│   │   └── security.py # Security utilities
│   ├── db/            # Database setup
│   │   └── mongodb.py # MongoDB connection
│   ├── models/        # MongoDB models
│   ├── schemas/       # Pydantic schemas
│   └── main.py        # FastAPI application
├── .env               # Environment variables
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
