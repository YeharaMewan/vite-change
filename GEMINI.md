### Project Overview
This is a web application with a Python/FastAPI backend and a React/Vite frontend. The backend uses LangChain, which suggests AI-powered features, and a PostgreSQL database with pgvector for vector embeddings. The entire application is containerized using Docker.

### Building and Running
The application can be run using Docker Compose.

**Development:**
```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

**Production:**
```bash
docker-compose up -d --build
```

**Frontend:**
- To run the development server: `npm run dev`
- To build the project: `npm run build`
- To lint the code: `npm run lint`

**Backend:**
- To run the development server: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### Development Conventions
- The backend code is located in the `backend/app` directory.
- The frontend code is located in the `frontend/src` directory.
- The database initialization script is located in `database/init.sql`.
- The project uses Tailwind CSS for styling.
- The project uses ESLint for linting the frontend code.
