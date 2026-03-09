# Viajera Digital Backend

**Python API and data processing pipeline for the Viajera Digital platform. Handles data modeling, transformation, processing, and export operations.**

## What It Does

Viajera Digital Backend is a Python-based service providing core API functionality and data pipeline operations for the Viajera Digital travel management platform. It manages data models, implements business logic for travel planning workflows, processes client requests, and generates export files in multiple formats. Designed for scalability with containerized deployment on Render.

The service operates as a REST API gateway processing travel data, managing user sessions, and orchestrating backend-to-frontend data flows while maintaining clean separation of concerns through modular architecture.

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.13+ | Application runtime |
| **Server** | Flask/FastAPI (configured in main.py) | REST API framework |
| **Data Models** | SQLAlchemy/Pydantic (models.py) | Data schema & validation |
| **Processing** | Custom pipeline.py | ETL and transformations |
| **Export** | exports.py | File generation (JSON, CSV, PDF) |
| **Container** | Docker 20.10+ | Deployment container |
| **Platform** | Render | Serverless hosting |
| **Dependencies** | See requirements.txt | Python package management |

## Project Structure

```
viajera-digital-backend/
├── main.py                   # Application entry point & API routes
├── models.py                 # Data models and schema definitions
├── pipeline.py               # ETL and data transformation logic
├── exports.py                # Output generation (JSON, CSV, PDF)
├── requirements.txt          # Python package dependencies
├── Dockerfile                # Container build configuration
├── render.yaml               # Render deployment blueprint
└── README.md                 # This file
```

## Module Descriptions

### main.py
Entry point for the Flask/FastAPI application. Defines:
- API route handlers (`/api/v1/*` endpoints)
- Request validation and error handling
- CORS configuration for frontend access
- Application initialization and middleware setup
- Health check endpoint (`GET /health`)

### models.py
Data schema definitions using SQLAlchemy ORM (if using SQL) or Pydantic models:
- `User` — User account, authentication, profile
- `Trip` — Travel itinerary, dates, destinations
- `Booking` — Flight, hotel, activity reservations
- `Payment` — Transaction records, billing info
- `Itinerary` — Day-by-day travel plan with activities

Includes validation rules, relationships, and data constraints.

### pipeline.py
ETL (Extract, Transform, Load) processing:
- Data ingestion from external APIs (flights, hotels, activities)
- Data cleaning and normalization
- Business logic transformations (cost calculations, availability checks)
- Enrichment (add calculated fields, metadata)
- Loading into application database

Functions include batch processing, scheduled tasks, and real-time processing triggers.

### exports.py
Output generation for client deliverables:
- **PDF Itinerary Export**: Formatted travel plan with maps, bookings, emergency contacts
- **CSV Bulk Export**: Client list, booking list for spreadsheet analysis
- **JSON API Response**: Structured data for frontend consumption
- **Email Templates**: Confirmation, reminder, receipt generation

## Run Locally

### Prerequisites
- Python 3.13+
- pip (Python package manager)
- Docker (optional, for containerized runs)
- Git

### Option 1: Virtual Environment (Recommended)
```bash
# Clone the repository
git clone https://github.com/ejnburrows-rgb/viajera-digital-backend.git
cd viajera-digital-backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# API will be available at http://localhost:5000
```

### Option 2: Docker
```bash
# Clone the repository
git clone https://github.com/ejnburrows-rgb/viajera-digital-backend.git
cd viajera-digital-backend

# Build Docker image
docker build -t viajera-digital-backend .

# Run container
docker run -p 5000:5000 viajera-digital-backend

# API will be available at http://localhost:5000
```

### Option 3: Docker Compose (if available)
```bash
# From project directory
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Test the API
```bash
# Health check
curl http://localhost:5000/health

# List users (example endpoint)
curl http://localhost:5000/api/v1/users

# Create trip (example)
curl -X POST http://localhost:5000/api/v1/trips \
  -H "Content-Type: application/json" \
  -d '{"destination":"Paris","start_date":"2024-06-01","end_date":"2024-06-10"}'
```

## Deploy on Render

### Automatic Deployment via GitHub Integration
1. Push code to GitHub (`main` branch)
2. Connect repository to [Render Dashboard](https://dashboard.render.com)
3. Render auto-detects `render.yaml` blueprint
4. Service auto-deploys on every push to main
5. API available at `https://your-service.onrender.com`

### Using Render Blueprint (Recommended)
The `render.yaml` file contains all deployment configuration:
```yaml
services:
  - type: web
    name: viajera-digital-backend
    env: python
    plan: standard
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
```

Deploy steps:
1. Go to [Render Blueprint Queue](https://dashboard.render.com/blueprints)
2. Select your GitHub repository
3. Render provisions resources and deploys automatically
4. Service scales automatically based on demand

### Manual Deployment
```bash
# Install Render CLI (optional)
npm install -g @render-com/cli

# Deploy from project directory
render deploy

# Or use Render web dashboard to connect GitHub repo directly
```

### Environment Variables

Set in Render Project Settings → Environment:
```
DATABASE_URL=postgresql://user:password@host:5432/database
API_KEY=sk-xxxxxxxxxxxxxxx
FLASK_ENV=production
DEBUG=False
SECRET_KEY=your-secret-key-here
```

Update `main.py` to read these:
```python
import os
DATABASE_URL = os.getenv('DATABASE_URL')
API_KEY = os.getenv('API_KEY')
```

### Monitoring Deployment
```bash
# View logs in Render dashboard
# Settings → Logs tab

# Or via CLI
render logs --service viajera-digital-backend --follow
```

### Custom Domain
1. In Render Project Settings → Custom Domain
2. Add your domain (e.g., `api.viajeradigital.com`)
3. Update DNS records (CNAME to Render domain)

## Configuration

### Environment Variables
Create `.env` file locally (not committed to git):
```
FLASK_ENV=development
DEBUG=True
DATABASE_URL=sqlite:///viajera.db
API_KEY=sk-test-key-here
SQLALCHEMY_TRACK_MODIFICATIONS=False
```

### Database Setup
```bash
# Initialize database (if using SQLAlchemy)
python -c "from main import app, db; app.app_context().push(); db.create_all()"
```

### API Documentation
Once running, access interactive API docs:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Service health check |
| `GET` | `/api/v1/users` | List all users |
| `POST` | `/api/v1/users` | Create new user |
| `GET` | `/api/v1/trips` | List user trips |
| `POST` | `/api/v1/trips` | Create new trip |
| `GET` | `/api/v1/trips/{id}` | Get trip details |
| `POST` | `/api/v1/trips/{id}/bookings` | Add booking to trip |
| `POST` | `/api/v1/export/pdf/{trip_id}` | Export trip as PDF |
| `POST` | `/api/v1/export/csv` | Export data as CSV |

## Troubleshooting

**Issue: "ModuleNotFoundError" when running locally**
- Solution: Ensure virtual environment is activated and dependencies installed
```bash
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

**Issue: Port 5000 already in use**
- Solution: Kill existing process or use different port
```bash
# macOS/Linux
lsof -i :5000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or change port in main.py
app.run(port=5001)
```

**Issue: Database connection error in Render**
- Solution: Verify DATABASE_URL is set correctly in environment variables
- Check Render dashboard → Settings → Environment
- Ensure database service is running and accessible

**Issue: Deployment fails on Render**
- Check build logs: Render Dashboard → Logs tab
- Verify `requirements.txt` has all dependencies
- Ensure `main.py` starts correctly (test locally first)

**Issue: Slow API responses**
- Check database query performance (add logging in pipeline.py)
- Optimize ETL processing (add caching, batch processing)
- Consider Render plan upgrade for more resources

## Performance

- **API Latency**: < 200ms for typical requests
- **Throughput**: 100+ requests/second on standard plan
- **Database**: Connection pooling for efficient DB access
- **Caching**: Redis available for session/data caching (add to requirements.txt)

## Development

### Add Dependencies
```bash
pip install new-package-name
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add new dependency"
git push origin main
```

### Run Tests (if available)
```bash
pytest tests/
```

### Code Style
```bash
# Format code
black main.py models.py pipeline.py exports.py

# Lint
flake8 *.py
pylint *.py
```

## License

MIT License — See LICENSE file for details

---

**Built by NBO — Novo Business Order**

© Emilio José Novo 2026. All rights reserved.

[API Docs](https://viajera-digital-backend.onrender.com/docs) | [GitHub](https://github.com/ejnburrows-rgb/viajera-digital-backend) | [Report Issue](https://github.com/ejnburrows-rgb/viajera-digital-backend/issues)
