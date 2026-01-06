# Video Database Update Scripts

This directory contains scripts to update video metadata in the PostgreSQL database with accurate durations and AI-generated descriptions based on transcript content.

## Overview

### Scripts Included

1. **`update_video_durations.py`** - Updates video durations using accurate ffprobe measurements
2. **`update_video_descriptions.py`** - Generates descriptions from transcript content using AI
3. **`update_video_metadata.py`** - Wrapper script to run both operations together
4. **`analyze_video_data.py`** - Analysis script to identify issues (requires decrypted credentials)

## Prerequisites

### 1. Database Access

Decrypt the credentials file to access the PostgreSQL database:

```bash
# Decrypt credentials (password in 1Password)
openssl aes-256-cbc -d -pbkdf2 -in config/credentials.yaml.enc -out config/credentials.yaml
```

### 2. Required Tools

- **ffprobe** (part of ffmpeg) for video duration analysis
- **Python 3.8+** with required packages
- **OpenAI API key** (configured in credentials.yaml)

### 3. Install Dependencies

```bash
pip install boto3 tqdm sqlalchemy psycopg2-binary openai pyyaml
```

## Usage

### Quick Start - Update All Problem Videos

```bash
# Update both durations and descriptions for videos with issues
python scripts/update_video_metadata.py

# Preview what would be updated (dry run)
python scripts/update_video_metadata.py --dry-run
```

### Individual Operations

#### Update Video Durations Only

```bash
# Update videos with missing/incorrect durations
python scripts/update_video_durations.py

# Update all videos (re-check existing durations too)
python scripts/update_video_durations.py --all

# Preview without changes
python scripts/update_video_durations.py --dry-run

# Update specific video
python scripts/update_video_durations.py --video-id 12345678-1234-1234-1234-123456789012
```

#### Update Video Descriptions Only

```bash
# Update videos with missing/poor descriptions (that have transcripts)
python scripts/update_video_descriptions.py

# Update all videos with transcripts
python scripts/update_video_descriptions.py --all

# Preview without changes
python scripts/update_video_descriptions.py --preview

# Update specific video
python scripts/update_video_descriptions.py --video-id 12345678-1234-1234-1234-123456789012
```

### Advanced Options

#### Batch Processing

```bash
# Process 20 videos at a time (default is 10)
python scripts/update_video_durations.py --batch-size 20
```

#### Rate Limiting

```bash
# Slower API calls to be nice to OpenAI (default is 1.0 second)
python scripts/update_video_descriptions.py --rate-limit 2.0
```

## How It Works

### Duration Updates (`update_video_durations.py`)

1. **Identifies videos needing updates:**
   - Videos with `duration_seconds = NULL`
   - Videos with `duration_seconds = 0`
   - Videos with suspiciously short (`< 0.1s`) or long (`> 2 hours`) durations

2. **For each video:**
   - Downloads video file from S3 to temporary location
   - Runs `ffprobe` to get accurate duration
   - Updates database with new duration
   - Cleans up temporary file

3. **Safety features:**
   - Skips videos where current duration is already accurate (< 0.1s difference)
   - Batch processing to avoid overwhelming S3/database
   - Comprehensive error handling and logging

### Description Updates (`update_video_descriptions.py`)

1. **Identifies videos needing updates:**
   - Videos with completed transcripts but no description
   - Videos with completed transcripts but poor descriptions (< 50 characters)

2. **For each video:**
   - Retrieves full transcript text from database
   - Sends transcript to OpenAI GPT-4o-mini with context (speaker name, event name, filename)
   - Gets AI-generated description (2-3 sentences, professional tone)
   - Updates database with new description

3. **AI prompt optimization:**
   - Uses cost-effective GPT-4o-mini model
   - Includes context about speaker and event when available
   - Limits description length to keep them concise
   - Uses low temperature (0.3) for consistent results

## Database Impact

### What Gets Updated

#### `videos` Table Fields:

- **`duration_seconds`** - Updated with accurate ffprobe-measured duration
- **`description`** - Updated with AI-generated description based on transcript

#### Safety Measures:

- ✅ **Read-only for most fields** - Only updates the two specific fields
- ✅ **Transaction safety** - Uses database transactions, rolls back on error
- ✅ **Logging** - Comprehensive logging of all changes
- ✅ **Validation** - Validates video exists before updating
- ✅ **Dry-run mode** - Preview changes before applying

## Performance & Costs

### Duration Updates

- **Time:** ~2-3 minutes per video (download + ffprobe + upload)
- **Network:** Downloads each video once, removes after processing
- **Cost:** S3 data transfer costs only

### Description Updates

- **Time:** ~2-3 seconds per video
- **API Calls:** 1 OpenAI API call per video
- **Cost:** ~$0.001-0.002 per video (GPT-4o-mini pricing)

### Batch Recommendations

- **Small batch (< 50 videos):** Run normally
- **Large batch (100+ videos):** Use `--batch-size 5` to be gentler on S3
- **Very large batch (500+ videos):** Run overnight or in chunks

## Error Handling

### Common Issues

1. **"Connection refused" database error**
   ```bash
   # Decrypt credentials first
   openssl aes-256-cbc -d -pbkdf2 -in config/credentials.yaml.enc -out config/credentials.yaml
   ```

2. **"ffprobe not found"**
   ```bash
   # Install ffmpeg
   brew install ffmpeg  # macOS
   apt-get install ffmpeg  # Ubuntu
   ```

3. **"OpenAI API key not found"**
   - Ensure credentials.yaml is decrypted and contains OpenAI API key

4. **S3 download failures**
   - Usually temporary; script will retry automatically
   - Check AWS credentials in decrypted credentials.yaml

### Recovery

- Scripts are designed to be re-runnable
- If interrupted, simply run again - it will skip already-processed videos
- Use `--video-id` to retry specific failed videos

## Monitoring

### Log Output

Scripts provide detailed logging:
- Progress bars for downloads
- Before/after values for updates
- Error details for failed videos
- Final summary statistics

### Database Verification

After running, you can verify updates:

```sql
-- Check updated durations
SELECT filename, duration_seconds, updated_at
FROM videos
WHERE updated_at > NOW() - INTERVAL '1 hour'
ORDER BY updated_at DESC;

-- Check updated descriptions
SELECT filename, description, updated_at
FROM videos
WHERE description IS NOT NULL
  AND updated_at > NOW() - INTERVAL '1 hour'
ORDER BY updated_at DESC;
```

## Example Workflow

### Complete Database Update

```bash
# 1. Decrypt credentials
openssl aes-256-cbc -d -pbkdf2 -in config/credentials.yaml.enc -out config/credentials.yaml

# 2. Preview what needs updating
python scripts/update_video_metadata.py --dry-run

# 3. Update problem videos
python scripts/update_video_metadata.py

# 4. Optionally update all videos to refresh everything
python scripts/update_video_metadata.py --all

# 5. Clean up credentials (optional, for security)
rm config/credentials.yaml
```

### Target Specific Issues

```bash
# Only fix missing durations
python scripts/update_video_durations.py

# Only add descriptions where transcripts exist
python scripts/update_video_descriptions.py

# Fix one specific video
python scripts/update_video_metadata.py --video-id abc123...
```

## Security Notes

- Keep credentials.yaml decrypted only when needed
- Scripts use read-only S3 access where possible
- Database updates are transactional and logged
- No sensitive data is sent to OpenAI (only transcript content)

## Support

If you encounter issues:
1. Check the log output for specific error messages
2. Verify credentials are properly decrypted
3. Ensure required tools (ffprobe) are installed
4. Try running with `--dry-run` or `--preview` first
5. For urgent issues, restore from database backup if needed