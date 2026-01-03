# Contributing to MV Internal

Welcome to the MV Internal video management platform! This guide will help you get set up for local development.

## Prerequisites

- Python 3.9+
- PostgreSQL client (for database access)
- AWS CLI (optional, for S3 operations)
- Git

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/maurinventures/video-management.git
cd video-management
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Secrets

Create `config/secrets.yaml` with the required credentials:

```yaml
database:
  host: "your-database-host"
  port: 5432
  name: "your-database-name"
  user: "your-username"
  password: "your-password"

aws:
  access_key_id: "your-aws-access-key"
  secret_access_key: "your-aws-secret-key"

anthropic:
  api_key: "your-anthropic-api-key"

openai:
  api_key: "your-openai-api-key"
```

**Important:** Never commit `secrets.yaml` to git (it's in `.gitignore`).

Contact the project owner to get the actual credentials.

### 4. Run Locally

```bash
# Start the Flask development server
cd web
python app.py

# Or use gunicorn (production-like)
gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 web.app:app
```

The app will be available at: http://localhost:5000

## Project Structure

```
video-management/
├── web/
│   ├── app.py              # Main Flask application
│   ├── templates/          # HTML templates
│   └── static/             # CSS, JS, images
├── scripts/
│   ├── db.py               # Database models (SQLAlchemy)
│   ├── config_loader.py    # Configuration loading
│   └── import_otter_ai.py  # Otter AI transcript importer
├── config/
│   ├── settings.yaml       # App settings (committed)
│   └── secrets.yaml        # Credentials (NOT committed)
├── migrations/             # SQL migration files
└── requirements.txt        # Python dependencies
```

## Key Features

- **Video Management**: Upload, transcode, and manage video content
- **Transcription**: AWS Transcribe integration for video transcripts
- **AI Chat**: Generate video scripts using Claude/GPT with transcript context
- **Audio Clips**: Otter AI transcript imports with audio playback
- **Personas**: AI personas for copy generation (LinkedIn, X, etc.)
- **2FA Authentication**: TOTP-based two-factor authentication

## Development Workflow

### Making Changes

1. Pull latest changes:
   ```bash
   git pull origin main
   ```

2. Make your changes

3. Test locally

4. Commit and push:
   ```bash
   git add -A
   git commit -m "Description of changes"
   git push origin main
   ```

### Deploying to Production

The production server is at `maurinventures.com`. To deploy:

```bash
# SSH to server and pull changes
ssh brain "cd ~/video-management && git pull && sudo systemctl restart mv-internal"
```

Note: You need SSH access to the EC2 server. Contact the project owner for access.

## Database

The app uses PostgreSQL (AWS RDS). Key tables:

- `videos` - Video metadata and S3 locations
- `transcripts` - Transcription jobs and status
- `transcript_segments` - Timestamped transcript text
- `audio_recordings` - Otter AI audio imports
- `audio_segments` - Audio transcript segments
- `personas` - AI personas for content generation
- `users` - User accounts with 2FA support
- `conversations` - Chat history

### Running Migrations

```bash
# Connect to database and run SQL
psql -h <host> -U <user> -d <database> -f migrations/001_initial.sql
```

## API Endpoints

Key endpoints:

- `POST /api/chat` - AI chat for script generation
- `GET /api/videos` - List videos
- `GET /api/video-preview/<id>` - Stream video
- `GET /api/audio-clip/<id>` - Stream audio clip
- `POST /api/copy/generate` - Generate social copy

## Environment Variables

Optional environment variables:

- `FLASK_SECRET_KEY` - Session encryption key
- `FLASK_ENV` - Set to `development` for debug mode

## Getting Help

- Check existing code for patterns and conventions
- Ask in the team chat for guidance
- Review recent commits for context

## Code Style

- Use clear, descriptive variable names
- Add docstrings to functions
- Keep functions focused and small
- Test changes locally before pushing
