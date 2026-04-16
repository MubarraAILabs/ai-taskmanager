# AI Task Manager

A production-ready FastAPI application for managing tasks with AI-powered task generation, built with clean architecture principles.

## Features

- ✅ **CRUD Operations**: Create, read, update, and delete tasks
- 🤖 **AI Task Generation**: Break down goals into structured tasks using OpenAI
- 📊 **Task Prioritization**: Automatic priority assignment and time estimation
- 🗄️ **SQLite Database**: Persistent storage with SQLAlchemy ORM
- 🔒 **Pydantic Validation**: Strong typing and data validation
- 🏗️ **Clean Architecture**: Separated concerns with services, repositories, and schemas

## Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to the project
cd ai-fastapi-demo

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure OpenAI API

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 3. Run the Application

```bash
# Start the server
uvicorn main:app --reload

# Server will be available at http://127.0.0.1:8000
```

### 4. API Documentation

Visit `http://127.0.0.1:8000/docs` for interactive Swagger UI documentation.

## API Endpoints

### Task Management
- `GET /tasks` - List all tasks
- `POST /tasks` - Create a new task
- `GET /tasks/{task_id}` - Get a specific task
- `PUT /tasks/{task_id}` - Update a task
- `DELETE /tasks/{task_id}` - Delete a task

### AI Features
- `POST /ai/generate-tasks` - Generate tasks from a goal

## Example Usage

### Generate Tasks from a Goal

```bash
curl -X POST "http://127.0.0.1:8000/ai/generate-tasks" \
     -H "Content-Type: application/json" \
     -d '{"goal": "Build a personal blog website"}'
```

**Response:**
```json
{
  "goal": "Build a personal blog website",
  "tasks": [
    {
      "title": "Design website layout and user interface",
      "description": "Create wireframes and mockups for the blog layout, including header, navigation, content area, and footer",
      "priority": "high",
      "estimated_time_hours": 8.0
    },
    {
      "title": "Set up development environment",
      "description": "Install necessary tools, frameworks, and dependencies for web development",
      "priority": "high",
      "estimated_time_hours": 2.0
    },
    {
      "title": "Implement responsive design",
      "description": "Ensure the website works well on desktop, tablet, and mobile devices",
      "priority": "medium",
      "estimated_time_hours": 6.0
    }
  ],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Create a Task

```bash
curl -X POST "http://127.0.0.1:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Design website layout",
       "description": "Create wireframes and mockups",
       "priority": "high"
     }'
```

## Project Structure

```
app/
├── api/
│   └── routes.py          # API endpoints
├── core/
│   ├── config.py          # Application configuration
│   └── database.py        # Database setup
├── models/
│   └── task.py            # SQLAlchemy models
├── repositories/
│   └── task_repository.py # Data access layer
├── schemas/
│   └── task.py            # Pydantic schemas
└── services/
    ├── task_service.py    # Business logic
    └── ai_service.py      # AI integration
```

## Architecture Principles

- **Separation of Concerns**: Each layer has a single responsibility
- **Dependency Injection**: Services depend on abstractions
- **Strong Typing**: Full type hints throughout the codebase
- **Validation**: Input validation with Pydantic
- **Error Handling**: Proper HTTP status codes and error messages

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest
```

### Database Migrations

The app uses SQLAlchemy with automatic table creation on startup. For production, consider using Alembic for migrations.

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required for AI features)
- `DATABASE_URL`: Database connection string (default: SQLite)
- `DEBUG`: Enable debug mode (default: false)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License