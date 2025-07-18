# 🎲 GameDex

A personal web app that helps you catalog, organize, and intelligently explore your board game collection. GameDex lets you store rich metadata for each game and leverages AI to suggest games based on your preferences or context.

## ✨ Features

- **Game Catalog**: Add, edit, delete, and list board games with structured metadata
- **Rich Metadata**: Track number of players, game type, playtime, complexity, and personal ratings
- **Filtering & Search**: Easily search or filter by game attributes
- **AI Autofill**: Use GPT to fetch game metadata based on title
- **Game Recommender**: Ask natural-language questions like "What's good for 3 players who want something short?"

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Jinja2 Templates with HTMX
- **Database**: SQLite (local) → PostgreSQL (production)
- **AI**: OpenAI GPT API
- **Containerization**: Docker
- **Package Management**: Poetry

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Poetry
- Docker (optional)
- OpenAI API key (for AI features)

### Environment Setup

GameDex requires several environment variables to be set for security and functionality:

#### Required Environment Variables

1. **`SESSION_SECRET_KEY`** - Secret key for session management

   ```bash
   export SESSION_SECRET_KEY="your-very-long-random-secret-key-here"
   ```

   *Generate a secure key: `openssl rand -hex 32`*

2. **`FAMILY_PASSWORD`** - Password for family access to the app

   ```bash
   export FAMILY_PASSWORD="your-family-password"
   ```

3. **`OPENAI_API_KEY`** - OpenAI API key for AI features

   ```bash
   export OPENAI_API_KEY="sk-your-openai-api-key"
   ```

#### Optional Environment Variables

- **`DATABASE_URL`** - Database connection string (defaults to SQLite)

  ```bash
  export DATABASE_URL="postgresql://user:password@localhost/gamedex"
  ```

#### Environment File Setup

Create a `.env` file in the project root for local development:

```bash
SESSION_SECRET_KEY=your-very-long-random-secret-key-here
FAMILY_PASSWORD=your-family-password
OPENAI_API_KEY=sk-your-openai-api-key
DATABASE_URL=sqlite:///./gamedex.db
```

### Local Development

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd gamedex
   ```

2. **Install dependencies**

   ```bash
   poetry install
   ```

3. **Set up environment variables**

   ```bash
   # Option 1: Export directly
   export SESSION_SECRET_KEY="your-very-long-random-secret-key-here"
   export FAMILY_PASSWORD="your-family-password"
   export DATABASE_URL="sqlite:///./gamedex.db"
   export OPENAI_API_KEY="your-openai-api-key"
   export IS_PRODUCTION="false"
   ```

4. **Initialize the database**

   ```bash
   # Run database migrations
   poetry run alembic upgrade head
   ```

5. **Run the application**

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

6. **Visit the application**
   Open your browser and go to `http://localhost:8000`

7. **Login**
   Use your family password to access the application

### Testing

GameDex includes a comprehensive test suite covering models, database operations, AI utilities, API endpoints, and integration tests.

#### Running Tests

**Run tests with pytest directly:**

```bash
# Set up test database
export DATABASE_URL="sqlite:///./test.db"
poetry run pytest tests/ -v
```

**Run specific test files:**

```bash
export DATABASE_URL="sqlite:///./test.db"
poetry run pytest tests/test_models.py -v
poetry run pytest tests/test_api.py -v
```

**Run tests with coverage:**

```bash
export DATABASE_URL="sqlite:///./test.db"
poetry run pytest tests/ --cov=app --cov-report=html
```

#### Writing Tests

When adding new features, please include corresponding tests:

1. **Unit tests** for new functions and classes
2. **Integration tests** for new API endpoints
3. **Database tests** for new models or queries
4. **Update existing tests** if you change existing functionality

Example test structure:

```python
def test_new_feature():
    """Test description"""
    # Arrange
    # Act
    # Assert
```

### Docker Development

1. **Build the image**

   ```bash
   docker build -t gamedex .
   ```

2. **Run the container**

   ```bash
   docker run -p 8000:8000 \
      -e DATABASE_URL="sqlite:///./gamedex.db" \
     -e SESSION_SECRET_KEY="your-very-long-random-secret-key-here" \
     -e FAMILY_PASSWORD="your-family-password" \
     -e OPENAI_API_KEY="your-openai-api-key" \
     -e IS_PRODUCTION="false" \
     gamedex
   ```

3. **Using Docker Compose (recommended)**

   Create a `docker-compose.yml` file:

   ```yaml
   version: '3.8'
   services:
     gamedex:
       build: .
       ports:
         - "8000:8000"
       env_file:
         - .env
       restart: unless-stopped
   ```

   Then run:

   ```bash
   docker compose up -d
   ```

## 🔧 Configuration

### Environment Variables

- `DATABASE_URL` **(Required)**: Database connection string
  - **SQLite (local development)**: `sqlite:///./gamedex.db`
  - **PostgreSQL (production)**: `postgresql://user:password@localhost/gamedex`
  - **Test environment**: `sqlite:///./test.db`
- `OPENAI_API_KEY` (Optional): Your OpenAI API key for AI features
- `SESSION_SECRET_KEY`: Secret key for session management (generate with `openssl rand -hex 32`)
- `FAMILY_PASSWORD`: Password for family access to the application
- `IS_PRODUCTION` (Optional): Set to "true" to indicate production environment (defaults to "false")
  - **Development**: `IS_PRODUCTION=false` or unset
  - **Production**: `IS_PRODUCTION=true`

### Database Setup

The application requires a `DATABASE_URL` environment variable to be set. This ensures consistent database configuration across all environments and prevents accidental use of the wrong database.

#### Database URL Examples

```bash
# Local SQLite development
export DATABASE_URL="sqlite:///./gamedex.db"

# PostgreSQL development
export DATABASE_URL="postgresql://user:password@localhost/gamedex_dev"

# PostgreSQL production
export DATABASE_URL="postgresql://user:password@prod-server/gamedex_prod"

# Test environment
export DATABASE_URL="sqlite:///./test.db"
```

#### Running Migrations

After setting up your `DATABASE_URL`, run migrations to create/update the database schema:

```bash
# Apply all pending migrations
poetry run alembic upgrade head

# Check current migration status
poetry run alembic current

# Create a new migration (after model changes)
poetry run alembic revision --autogenerate -m "Description of changes"
```

## 🤖 AI Features

### Game Metadata Autofill

When adding a new game, you can use the AI autofill feature to automatically populate game metadata based on the title. This uses OpenAI's GPT model to fetch information about the game.

### Game Recommendations

Ask natural language questions to get AI-powered game recommendations:

- "What's good for 4 players who want something quick?"
- "I want a strategy game for 2 players"
- "Something fun and light for a party"

## 🎨 UI/UX Features

- **Modern Design**: Clean, responsive interface built with Tailwind CSS
- **Interactive Cards**: Hover effects and smooth transitions
- **Statistics Dashboard**: Overview of your collection with key metrics
- **Mobile Responsive**: Works great on all device sizes

## 🔒 Security

- Non-root Docker container
- Environment variable configuration
- SQL injection protection via SQLAlchemy
- Input validation and sanitization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information

---

Built with ❤️ using FastAPI, SQLAlchemy, and OpenAI
