# Smart Parking Backend

Production-ready backend for smart parking system.

## Features
- User authentication via Line LIFF/Line Login
- Store user and parking info in MySQL
- Generate and send QR code for payment (PromptPay/TrueMoney) via Line
- Receive and verify payment slip (SlipOK API)
- RESTful API for frontend
- WebSocket for real-time parking status
- .env config, Dockerfile, best practices

## Getting Started
1. Install dependencies: `npm install`
2. Copy `.env.example` to `.env` and fill in your config
3. Start server: `npm start`

## Folder Structure
- `/src` - main source code
- `/src/controllers` - API controllers
- `/src/models` - database models
- `/src/routes` - API routes
- `/src/services` - business logic (Line, QR, SlipOK, etc.)
- `/src/utils` - utility functions
- `/public` - static files
- `/config` - config files

## Environment Variables
See `.env.example` for required variables (MySQL, Line, SlipOK, etc.)

## License
MIT
