# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Google Calendar OAuth authentication server built with Flask and PostgreSQL. The application handles OAuth2 authentication with Google Calendar API, stores credentials in a PostgreSQL database, and displays calendar events. It's designed for deployment on Heroku (includes Procfile for gunicorn).

## Architecture

- **Single-file Flask application** (`app.py`): Contains all OAuth flow logic, database operations, and routing
- **PostgreSQL database**: Stores OAuth credentials with UPSERT operations for user tokens
- **OAuth2 flow**: Uses google-auth-oauthlib for Google Calendar API authentication with offline access
- **Environment-based configuration**: All sensitive data managed through `.env` file

## Key Components

- **OAuth flow**: `/authorize` → Google auth → `/oauth2callback` → credential storage
- **Database initialization**: Auto-creates credentials table on first request via `@app.before_request`
- **Credential management**: JSON serialization of OAuth tokens with refresh capability
- **Calendar display**: Retrieves and shows upcoming events from primary calendar

## Development Commands

### Setup and Run
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

### Database Setup
```bash
# Apply schema to PostgreSQL database
psql -U <username> -d <database> -f schema.sql
```

### Deployment
```bash
# Production deployment uses gunicorn via Procfile
web: gunicorn app:app
```

## Environment Configuration

Required `.env` variables:
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret  
- `GOOGLE_REDIRECT_URI`: OAuth callback URL (default: http://localhost:5000/oauth2callback)
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Flask session secret

## Important Notes

- Development mode disables HTTPS requirements for OAuth (`OAUTHLIB_INSECURE_TRANSPORT=1`)
- Fixed user ID (`Ud4cc4c3b7e9ec9875f9951d1d0352a7a`) used for demo purposes
- Database connection uses autocommit mode for all operations
- OAuth flow requests offline access with consent prompt for refresh tokens