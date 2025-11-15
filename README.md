# Behavioral Authentication System - React Frontend with Node.js Backend

This project is a modern implementation of a behavioral authentication system using React.js for the frontend and Node.js for the backend.

## Project Structure

```
behavior_auth_system/
├── behavior-auth-frontend/    # React frontend
├── backend/                   # Node.js backend
└── behavior_auth_system/      # Original Python implementation
```

## Features

1. **User Authentication**
   - Login and registration with email and PIN
   - Secure PIN storage with bcrypt hashing
   - JWT-based session management

2. **Baseline Training**
   - 5-minute behavioral data collection
   - Real-time metrics display
   - Progress tracking

3. **Dashboard**
   - Real-time behavioral metrics
   - ML model accuracy metrics
   - Security events monitoring

4. **Profile Management**
   - User profile information
   - Security settings
   - PIN change functionality

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

## Installation

1. **Install backend dependencies:**
   ```bash
   cd backend
   npm install
   ```

2. **Install frontend dependencies:**
   ```bash
   cd ../behavior-auth-frontend
   npm install
   ```

## Running the Application

1. **Start the backend server:**
   ```bash
   cd backend
   npm start
   ```
   The server will run on http://localhost:5000

2. **Start the frontend development server:**
   ```bash
   cd behavior-auth-frontend
   npm start
   ```
   The frontend will run on http://localhost:3000

## Building for Production

1. **Build the frontend:**
   ```bash
   cd behavior-auth-frontend
   npm run build
   ```

2. **The built files will be in the `build` directory and can be served by the Node.js backend.**

## API Endpoints

- `POST /api/login` - User login
- `POST /api/register` - User registration
- `POST /api/baseline` - Save baseline data
- `GET /api/dashboard/:userId` - Get dashboard data
- `GET /api/profile/:userId` - Get profile data
- `PUT /api/profile/pin` - Change PIN

## Demo Credentials

- Email: demo@example.com
- PIN: 123456

## Technologies Used

### Frontend
- React.js
- CSS3
- Fetch API for HTTP requests

### Backend
- Node.js
- Express.js
- bcrypt for password hashing
- jsonwebtoken for JWT tokens
- cors for cross-origin resource sharing

## Future Enhancements

1. Integration with the original Python behavioral monitoring system
2. Real-time WebSocket connections for live metrics
3. Database integration (SQLite, PostgreSQL, or MongoDB)
4. Enhanced security features
5. Mobile-responsive design