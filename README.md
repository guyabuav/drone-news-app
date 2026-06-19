# Drone News Application

A full-stack application for browsing and searching drone-related news articles from around the world.

## Project Structure

```
drone-news-app/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── database.py
│   │   └── news_client.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
└── frontend/         # Simple HTML/CSS/JS frontend
    ├── index.html
    └── server.py
```

## Features

- 📰 Browse latest drone-related news from around the world
- 🔍 Search articles by keyword
- 📄 Clean card-based UI for displaying articles
- ⏱️ Automatic article sync from NewsAPI (every hour)
- 📱 Responsive design
- 🔄 Pagination for large result sets
- ⚡ Fast and lightweight

## Prerequisites

- Python 3.10+
- News API Key (get one for free at https://newsapi.org)

## Backend Setup

### 1. Navigate to backend directory

```bash
cd backend
```

### 2. Create and activate virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

Edit `.env` and add your News API key:

```env
NEWS_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///./drone_news.db
```

Get a free API key at: https://newsapi.org/register

### 5. Run the backend

```bash
$env:PYTHONPATH = "."; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --log-level info
```

**Backend will be available at:** `http://127.0.0.1:8000`

**API Documentation:** `http://127.0.0.1:8000/docs`

## Frontend Setup

### 1. Navigate to frontend directory

```bash
cd frontend
```

### 2. Run the frontend server

**Windows (PowerShell):**
```powershell
python server.py
```

**macOS/Linux:**
```bash
python3 server.py
```

**Frontend will be available at:** `http://127.0.0.1:8080`

### Alternative: Open directly in browser

You can also directly open `frontend/index.html` in your browser by double-clicking it. Make sure the backend is running first.

## Backend API Endpoints

- `GET /` - Health check
- `GET /articles` - Get articles with pagination and search
  - Query params: `keyword` (optional), `skip` (default 0), `limit` (default 50, max 100)
  - Example: `GET /articles?keyword=drone&skip=0&limit=10`
- `POST /articles/sync` - Manually trigger article sync (rate-limited to 1 request per 5 minutes)

## How It Works

### Backend

1. **Article Sync**: The backend automatically syncs drone-related articles from NewsAPI every hour
2. **Deduplication**: Articles are checked for duplicates using their URL
3. **Search**: Articles can be searched by keyword (title, description, or content)
4. **Pagination**: Results are paginated for better performance

### Frontend

1. **Fetches** articles from the backend API
2. **Displays** them as cards with all available information
3. **Allows** searching by keyword with debouncing for efficiency
4. **Supports** pagination for browsing through large result sets
5. **Shows** loading, error, and empty states for better UX

## Testing

Run the test suite:

```bash
cd backend
$env:PYTHONPATH = "."; pytest tests/ -v
```

All 13 tests should pass.

## Environment Variables

**Backend (.env file):**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEWS_API_KEY` | Yes | - | Your NewsAPI.org API key |
| `DATABASE_URL` | No | `sqlite:///./drone_news.db` | Database URL |

## Troubleshooting

### Backend won't start

1. Check that Python 3.10+ is installed: `python --version`
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Ensure `NEWS_API_KEY` is set in `.env`
4. Check if port 8000 is already in use

### Frontend can't connect to backend

1. Make sure the backend is running at `http://127.0.0.1:8000`
2. Check that CORS is enabled (should be by default)
3. Look for errors in the browser console (F12)

### No articles showing

1. Trigger a manual sync: `POST http://127.0.0.1:8000/articles/sync`
2. Wait for articles to be fetched from NewsAPI (first sync may take a few seconds)
3. Check backend logs for any errors

## Architecture Notes

- **Backend**: FastAPI with SQLAlchemy ORM and SQLite database
- **Frontend**: Vanilla HTML/CSS/JavaScript (no external dependencies)
- **API**: RESTful JSON API with CORS support
- **Scheduling**: Background job runs every hour to sync articles
- **Rate Limiting**: Manual sync endpoint is rate-limited to 1 request per 5 minutes per IP

## Future Improvements

- Add article categories/filtering by topic
- Implement user favorites/bookmarks
- Add dark mode
- Implement article caching/offline support
- Add email notifications for new articles
- Support multiple news sources
- Add admin panel for managing sync schedule

## License

This is a home assignment project.
