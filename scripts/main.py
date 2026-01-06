#!/usr/bin/env python3
"""Video Management System CLI."""

import logging
import sys
from pathlib import Path
from typing import Optional
from uuid import UUID

import click

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.config_loader import get_config
from scripts.db import init_db

# Set up logging
def setup_logging():
    config = get_config()
    log_file = Path(config.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=config.settings.get("logging", {}).get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ),
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(debug: bool):
    """Video Management System - Upload, transcribe, clip, and compile videos."""
    setup_logging()
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)


# ============ Video Commands ============

@cli.group()
def video():
    """Video upload and management commands."""
    pass


@video.command("upload")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--user", "-u", help="Username of uploader")
@click.option("--name", "-n", help="Custom filename")
def video_upload(file_path: str, user: Optional[str], name: Optional[str]):
    """Upload a video to S3."""
    from scripts.upload_video import upload_video

    video_id, s3_key = upload_video(file_path, uploaded_by=user, custom_filename=name)
    if video_id:
        click.echo(f"Uploaded successfully!")
        click.echo(f"  Video ID: {video_id}")
        click.echo(f"  S3 Key: {s3_key}")
    else:
        click.echo("Upload failed.", err=True)
        sys.exit(1)


@video.command("list")
@click.option("--status", "-s", help="Filter by status")
@click.option("--limit", "-l", default=20, help="Max results")
def video_list(status: Optional[str], limit: int):
    """List videos in the database."""
    from scripts.upload_video import list_videos

    videos = list_videos(status=status, limit=limit)
    if not videos:
        click.echo("No videos found.")
        return

    click.echo(f"{'ID':<36} {'Filename':<30} {'Status':<12} {'Duration':<10}")
    click.echo("-" * 90)
    for v in videos:
        duration = f"{float(v['duration_seconds']):.1f}s" if v['duration_seconds'] else "N/A"
        click.echo(f"{str(v['id']):<36} {v['filename'][:28]:<30} {v['status']:<12} {duration:<10}")


@video.command("info")
@click.argument("video_id")
def video_info(video_id: str):
    """Show details for a video."""
    from scripts.upload_video import get_video

    video = get_video(UUID(video_id))
    if not video:
        click.echo("Video not found.", err=True)
        sys.exit(1)

    click.echo(f"ID: {video['id']}")
    click.echo(f"Filename: {video['filename']}")
    click.echo(f"Original: {video['original_filename']}")
    click.echo(f"S3 Key: {video['s3_key']}")
    click.echo(f"Status: {video['status']}")
    click.echo(f"Duration: {video['duration_seconds']}s" if video['duration_seconds'] else "Duration: N/A")
    click.echo(f"Resolution: {video['resolution'] or 'N/A'}")
    click.echo(f"Size: {video['file_size_bytes']:,} bytes" if video['file_size_bytes'] else "Size: N/A")
    click.echo(f"Uploaded: {video['created_at']}")


@video.command("delete")
@click.argument("video_id")
@click.option("--keep-s3", is_flag=True, help="Keep file in S3")
@click.confirmation_option(prompt="Are you sure you want to delete this video?")
def video_delete(video_id: str, keep_s3: bool):
    """Delete a video."""
    from scripts.upload_video import delete_video

    if delete_video(UUID(video_id), delete_from_s3=not keep_s3):
        click.echo("Video deleted.")
    else:
        click.echo("Failed to delete video.", err=True)
        sys.exit(1)


@video.command("health-check")
@click.option("--fix", is_flag=True, help="Attempt to fix issues found")
def video_health_check(fix: bool):
    """Check video health (S3 sync, metadata consistency)."""
    from scripts.db import DatabaseSession
    from sqlalchemy import text
    import boto3
    from botocore.exceptions import ClientError
    from scripts.config_loader import get_config

    config = get_config()
    s3_client = boto3.client('s3')
    session = DatabaseSession()

    try:
        # Get all videos from DB
        result = session.execute(text("SELECT id, filename, s3_key, file_size_bytes, status FROM video"))
        videos = result.fetchall()

        issues_found = 0
        issues_fixed = 0

        click.echo("Video Health Check")
        click.echo("=" * 50)
        click.echo(f"Checking {len(videos)} videos...")
        click.echo()

        for video in videos:
            video_id, filename, s3_key, db_file_size, status = video

            # Check if S3 object exists
            try:
                s3_response = s3_client.head_object(Bucket=config.aws_s3_bucket, Key=s3_key)
                s3_size = s3_response['ContentLength']

                # Check size mismatch
                if db_file_size != s3_size:
                    click.echo(f"❌ {filename}: Size mismatch (DB: {db_file_size:,}, S3: {s3_size:,})")
                    issues_found += 1

                    if fix:
                        # Update DB with S3 size
                        session.execute(text("UPDATE video SET file_size_bytes = :size WHERE id = :id"),
                                      {"size": s3_size, "id": video_id})
                        click.echo(f"   ✅ Fixed: Updated DB size to {s3_size:,}")
                        issues_fixed += 1

            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    click.echo(f"❌ {filename}: S3 file missing ({s3_key})")
                    issues_found += 1

                    if fix and status != 'failed':
                        # Mark as failed
                        session.execute(text("UPDATE video SET status = 'failed' WHERE id = :id"),
                                      {"id": video_id})
                        click.echo(f"   ✅ Fixed: Marked as failed")
                        issues_fixed += 1
                else:
                    click.echo(f"❌ {filename}: S3 error - {e}")
                    issues_found += 1

        if fix:
            session.commit()

        click.echo()
        if issues_found == 0:
            click.echo("✅ All videos healthy!")
        else:
            click.echo(f"Found {issues_found} issues.")
            if fix:
                click.echo(f"Fixed {issues_fixed} issues.")
            else:
                click.echo("Run with --fix to attempt repairs.")

    except Exception as e:
        click.echo(f"Health check failed: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@video.command("bulk-status")
@click.argument("status")
@click.option("--filter-current", "-f", help="Only change videos currently in this status")
@click.confirmation_option(prompt="Are you sure you want to change video statuses?")
def video_bulk_status(status: str, filter_current: Optional[str]):
    """Bulk update video status."""
    from scripts.db import DatabaseSession
    from sqlalchemy import text

    session = DatabaseSession()
    try:
        # Build query
        if filter_current:
            query = "UPDATE video SET status = :new_status WHERE status = :current_status"
            params = {"new_status": status, "current_status": filter_current}
            description = f"videos with status '{filter_current}'"
        else:
            query = "UPDATE video SET status = :new_status"
            params = {"new_status": status}
            description = "all videos"

        result = session.execute(text(query), params)
        session.commit()

        click.echo(f"Updated {result.rowcount} {description} to status '{status}'")

    except Exception as e:
        click.echo(f"Bulk status update failed: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@video.command("metadata-update")
@click.option("--missing-only", is_flag=True, help="Only update videos with missing metadata")
@click.option("--limit", "-l", default=10, help="Max videos to process")
def video_metadata_update(missing_only: bool, limit: int):
    """Update video metadata (duration, resolution, etc)."""
    from scripts.db import DatabaseSession
    from sqlalchemy import text
    import boto3
    from scripts.config_loader import get_config
    import tempfile
    import subprocess
    import json

    config = get_config()
    s3_client = boto3.client('s3')
    session = DatabaseSession()

    try:
        # Find videos needing metadata updates
        if missing_only:
            query = """SELECT id, filename, s3_key FROM video
                      WHERE (duration_seconds IS NULL OR resolution IS NULL)
                      AND status = 'uploaded' LIMIT :limit"""
        else:
            query = "SELECT id, filename, s3_key FROM video WHERE status = 'uploaded' LIMIT :limit"

        result = session.execute(text(query), {"limit": limit})
        videos = result.fetchall()

        if not videos:
            click.echo("No videos need metadata updates.")
            return

        click.echo(f"Updating metadata for {len(videos)} videos...")

        for video_id, filename, s3_key in videos:
            click.echo(f"Processing {filename}...")

            try:
                # Download to temp file
                with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix) as temp_file:
                    s3_client.download_file(config.aws_s3_bucket, s3_key, temp_file.name)

                    # Use ffprobe to get metadata
                    cmd = [
                        'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
                        temp_file.name
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        click.echo(f"   ❌ Failed to analyze {filename}")
                        continue

                    data = json.loads(result.stdout)

                    # Extract metadata
                    duration = float(data['format']['duration'])

                    # Find video stream
                    video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
                    if video_stream:
                        resolution = f"{video_stream['width']}x{video_stream['height']}"
                    else:
                        resolution = None

                    # Update database
                    session.execute(text("""
                        UPDATE video SET duration_seconds = :duration, resolution = :resolution
                        WHERE id = :id
                    """), {"duration": duration, "resolution": resolution, "id": video_id})

                    click.echo(f"   ✅ Updated: {duration:.1f}s, {resolution}")

            except Exception as e:
                click.echo(f"   ❌ Error processing {filename}: {e}")

        session.commit()
        click.echo("Metadata update completed!")

    except Exception as e:
        click.echo(f"Metadata update failed: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


# ============ Transcription Commands ============

@cli.group()
def transcribe():
    """Transcription commands."""
    pass


@transcribe.command("start")
@click.argument("video_id")
@click.option("--provider", "-p", type=click.Choice(["aws", "whisper"]), help="Transcription provider")
@click.option("--no-wait", is_flag=True, help="Don't wait for completion (AWS only)")
def transcribe_start(video_id: str, provider: Optional[str], no_wait: bool):
    """Transcribe a video."""
    from scripts.transcribe import transcribe_video

    click.echo(f"Starting transcription for video {video_id}...")
    transcript_id = transcribe_video(UUID(video_id), provider=provider, wait=not no_wait)

    if transcript_id:
        click.echo(f"Transcription completed!")
        click.echo(f"  Transcript ID: {transcript_id}")
    else:
        click.echo("Transcription failed.", err=True)
        sys.exit(1)


@transcribe.command("status")
@click.argument("job_name")
def transcribe_status(job_name: str):
    """Check AWS Transcribe job status."""
    from scripts.transcribe import check_transcription_status

    status = check_transcription_status(job_name)
    click.echo(f"Status: {status['status']}")
    if status.get("output_uri"):
        click.echo(f"Output: {status['output_uri']}")
    if status.get("failure_reason"):
        click.echo(f"Error: {status['failure_reason']}")


@transcribe.command("view")
@click.argument("video_id")
def transcribe_view(video_id: str):
    """View transcript for a video."""
    from scripts.transcribe import get_transcript_for_video, get_transcript_segments

    transcript = get_transcript_for_video(UUID(video_id))
    if not transcript:
        click.echo("No transcript found for this video.", err=True)
        sys.exit(1)

    click.echo(f"Transcript ID: {transcript.id}")
    click.echo(f"Provider: {transcript.provider}")
    click.echo(f"Word count: {transcript.word_count}")
    click.echo(f"Status: {transcript.status}")
    click.echo("")
    click.echo("Segments:")
    click.echo("-" * 80)

    segments = get_transcript_segments(transcript.id)
    for seg in segments:
        start = f"{float(seg.start_time):.1f}s"
        end = f"{float(seg.end_time):.1f}s"
        click.echo(f"[{start} - {end}] {seg.text}")


@transcribe.command("search")
@click.argument("video_id")
@click.argument("query")
def transcribe_search(video_id: str, query: str):
    """Search transcript for a phrase."""
    from scripts.transcribe import search_transcript

    results = search_transcript(UUID(video_id), query)
    if not results:
        click.echo("No matches found.")
        return

    click.echo(f"Found {len(results)} matches:")
    click.echo("-" * 80)
    for r in results:
        click.echo(f"[{r['start_time']:.1f}s - {r['end_time']:.1f}s] {r['text']}")


# ============ Clip Commands ============

@cli.group()
def clip():
    """Clip management commands."""
    pass


@clip.command("create")
@click.argument("video_id")
@click.argument("start_time", type=float)
@click.argument("end_time", type=float)
@click.argument("clip_name")
@click.option("--notes", "-n", help="Notes about the clip")
@click.option("--user", "-u", help="Username of creator")
def clip_create(video_id: str, start_time: float, end_time: float, clip_name: str, notes: Optional[str], user: Optional[str]):
    """Create a clip from a video.

    START_TIME and END_TIME are in seconds.
    """
    from scripts.clip_video import create_clip

    click.echo(f"Creating clip from {start_time}s to {end_time}s...")
    clip_id = create_clip(
        UUID(video_id),
        start_time,
        end_time,
        clip_name,
        notes=notes,
        created_by=user,
    )

    if clip_id:
        click.echo(f"Clip created!")
        click.echo(f"  Clip ID: {clip_id}")
    else:
        click.echo("Failed to create clip.", err=True)
        sys.exit(1)


@clip.command("batch")
@click.argument("video_id")
@click.argument("clips_file", type=click.Path(exists=True))
@click.option("--user", "-u", help="Username of creator")
def clip_batch(video_id: str, clips_file: str, user: Optional[str]):
    """Create multiple clips from a JSON file.

    CLIPS_FILE should be a JSON file with array of objects:
    [{"start_time": 0, "end_time": 10, "clip_name": "intro", "notes": "optional"}]
    """
    import json
    from scripts.clip_video import create_clips_batch

    with open(clips_file) as f:
        clips_data = json.load(f)

    click.echo(f"Creating {len(clips_data)} clips...")
    clip_ids = create_clips_batch(UUID(video_id), clips_data, created_by=user)

    click.echo(f"Created {len(clip_ids)} clips:")
    for cid in clip_ids:
        click.echo(f"  {cid}")


@clip.command("list")
@click.option("--video", "-v", "video_id", help="Filter by source video ID")
@click.option("--status", "-s", help="Filter by status")
def clip_list(video_id: Optional[str], status: Optional[str]):
    """List clips."""
    from scripts.clip_video import list_clips

    vid = UUID(video_id) if video_id else None
    clips = list_clips(video_id=vid, status=status)

    if not clips:
        click.echo("No clips found.")
        return

    click.echo(f"{'ID':<36} {'Name':<25} {'Start':<8} {'End':<8} {'Status':<10}")
    click.echo("-" * 90)
    for c in clips:
        click.echo(f"{str(c.id):<36} {c.clip_name[:23]:<25} {float(c.start_time):<8.1f} {float(c.end_time):<8.1f} {c.status:<10}")


@clip.command("delete")
@click.argument("clip_id")
@click.option("--keep-s3", is_flag=True, help="Keep file in S3")
@click.confirmation_option(prompt="Are you sure you want to delete this clip?")
def clip_delete(clip_id: str, keep_s3: bool):
    """Delete a clip."""
    from scripts.clip_video import delete_clip

    if delete_clip(UUID(clip_id), delete_from_s3=not keep_s3):
        click.echo("Clip deleted.")
    else:
        click.echo("Failed to delete clip.", err=True)
        sys.exit(1)


# ============ Compile Commands ============

@cli.group()
def compile():
    """Compile videos from clips."""
    pass


@compile.command("create")
@click.argument("title")
@click.argument("clip_ids", nargs=-1, required=True)
@click.option("--description", "-d", help="Video description")
@click.option("--user", "-u", help="Username of creator")
@click.option("--no-normalize", is_flag=True, help="Skip resolution normalization")
def compile_create(title: str, clip_ids: tuple, description: Optional[str], user: Optional[str], no_normalize: bool):
    """Compile clips into a final video.

    CLIP_IDS are the UUIDs of clips to combine, in order.
    """
    from scripts.compile_video import compile_video

    clip_uuids = [UUID(cid) for cid in clip_ids]
    click.echo(f"Compiling {len(clip_uuids)} clips into '{title}'...")

    compiled_id = compile_video(
        title,
        clip_uuids,
        description=description,
        created_by=user,
        normalize_resolution=not no_normalize,
    )

    if compiled_id:
        click.echo(f"Video compiled!")
        click.echo(f"  Compiled Video ID: {compiled_id}")
    else:
        click.echo("Failed to compile video.", err=True)
        sys.exit(1)


@compile.command("list")
@click.option("--status", "-s", help="Filter by status")
@click.option("--limit", "-l", default=20, help="Max results")
def compile_list(status: Optional[str], limit: int):
    """List compiled videos."""
    from scripts.compile_video import list_compiled_videos

    videos = list_compiled_videos(status=status, limit=limit)
    if not videos:
        click.echo("No compiled videos found.")
        return

    click.echo(f"{'ID':<36} {'Title':<30} {'Duration':<12} {'Status':<10}")
    click.echo("-" * 90)
    for v in videos:
        duration = f"{v.total_duration_seconds:.1f}s" if v.total_duration_seconds else "N/A"
        click.echo(f"{str(v.id):<36} {v.title[:28]:<30} {duration:<12} {v.status:<10}")


@compile.command("info")
@click.argument("compiled_id")
def compile_info(compiled_id: str):
    """Show details for a compiled video."""
    from scripts.compile_video import get_compiled_video, get_compiled_video_clips

    video = get_compiled_video(UUID(compiled_id))
    if not video:
        click.echo("Compiled video not found.", err=True)
        sys.exit(1)

    click.echo(f"ID: {video.id}")
    click.echo(f"Title: {video.title}")
    click.echo(f"Description: {video.description or 'N/A'}")
    click.echo(f"S3 Key: {video.s3_key}")
    click.echo(f"Status: {video.status}")
    click.echo(f"Duration: {video.total_duration_seconds}s" if video.total_duration_seconds else "Duration: N/A")
    click.echo(f"Resolution: {video.resolution or 'N/A'}")
    click.echo(f"Size: {video.file_size_bytes:,} bytes" if video.file_size_bytes else "Size: N/A")
    click.echo(f"Created: {video.created_at}")
    click.echo("")
    click.echo("Clips:")

    clips = get_compiled_video_clips(UUID(compiled_id))
    for i, c in enumerate(clips):
        if c:
            click.echo(f"  {i+1}. {c.clip_name} ({float(c.end_time - c.start_time):.1f}s)")


@compile.command("delete")
@click.argument("compiled_id")
@click.option("--keep-s3", is_flag=True, help="Keep file in S3")
@click.confirmation_option(prompt="Are you sure you want to delete this compiled video?")
def compile_delete(compiled_id: str, keep_s3: bool):
    """Delete a compiled video."""
    from scripts.compile_video import delete_compiled_video

    if delete_compiled_video(UUID(compiled_id), delete_from_s3=not keep_s3):
        click.echo("Compiled video deleted.")
    else:
        click.echo("Failed to delete compiled video.", err=True)
        sys.exit(1)


@compile.command("download")
@click.argument("compiled_id")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def compile_download(compiled_id: str, output: Optional[str]):
    """Download a compiled video to local storage."""
    from scripts.compile_video import download_compiled_video

    output_path = Path(output) if output else None
    result = download_compiled_video(UUID(compiled_id), output_path)

    if result:
        click.echo(f"Downloaded to: {result}")
    else:
        click.echo("Failed to download video.", err=True)
        sys.exit(1)


# ============ S3 Commands ============

@cli.group()
def s3():
    """AWS S3 operations."""
    pass


@s3.command("list-buckets")
def s3_list_buckets():
    """List all S3 buckets."""
    import boto3
    from botocore.exceptions import ClientError

    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()

        click.echo("S3 Buckets:")
        click.echo("-" * 50)
        for bucket in response['Buckets']:
            click.echo(f"  {bucket['Name']} (created: {bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S')})")
    except ClientError as e:
        click.echo(f"Failed to list buckets: {e}", err=True)
        sys.exit(1)


@s3.command("list-objects")
@click.option("--bucket", "-b", help="S3 bucket name")
@click.option("--prefix", "-p", default="", help="Object prefix filter")
@click.option("--limit", "-l", default=50, help="Max objects to list")
def s3_list_objects(bucket: Optional[str], prefix: str, limit: int):
    """List objects in S3 bucket."""
    import boto3
    from botocore.exceptions import ClientError
    from scripts.config_loader import get_config

    if not bucket:
        config = get_config()
        bucket = config.aws_s3_bucket

    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=limit
        )

        if 'Contents' not in response:
            click.echo("No objects found.")
            return

        click.echo(f"Objects in {bucket} (prefix: '{prefix}'):")
        click.echo(f"{'Key':<50} {'Size':<12} {'Modified':<20}")
        click.echo("-" * 85)

        for obj in response['Contents']:
            size = f"{obj['Size']:,} bytes"
            modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
            click.echo(f"{obj['Key'][:48]:<50} {size:<12} {modified:<20}")

        if response.get('IsTruncated'):
            click.echo(f"\n... and more (showing first {limit})")

    except ClientError as e:
        click.echo(f"Failed to list objects: {e}", err=True)
        sys.exit(1)


@s3.command("download")
@click.argument("s3_key")
@click.option("--bucket", "-b", help="S3 bucket name")
@click.option("--output", "-o", type=click.Path(), help="Local output path")
def s3_download(s3_key: str, bucket: Optional[str], output: Optional[str]):
    """Download file from S3."""
    import boto3
    from botocore.exceptions import ClientError
    from scripts.config_loader import get_config
    from pathlib import Path

    if not bucket:
        config = get_config()
        bucket = config.aws_s3_bucket

    if not output:
        output = Path(s3_key).name

    try:
        s3_client = boto3.client('s3')
        click.echo(f"Downloading {bucket}/{s3_key} to {output}...")
        s3_client.download_file(bucket, s3_key, output)

        # Show file info
        file_path = Path(output)
        size_mb = file_path.stat().st_size / 1024 / 1024
        click.echo(f"Downloaded successfully! ({size_mb:.2f} MB)")

    except ClientError as e:
        click.echo(f"Failed to download: {e}", err=True)
        sys.exit(1)


@s3.command("upload-file")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--bucket", "-b", help="S3 bucket name")
@click.option("--key", "-k", help="S3 key (defaults to filename)")
def s3_upload_file(file_path: str, bucket: Optional[str], key: Optional[str]):
    """Upload file directly to S3."""
    import boto3
    from botocore.exceptions import ClientError
    from scripts.config_loader import get_config
    from pathlib import Path

    if not bucket:
        config = get_config()
        bucket = config.aws_s3_bucket

    if not key:
        key = Path(file_path).name

    try:
        s3_client = boto3.client('s3')
        file_size = Path(file_path).stat().st_size
        size_mb = file_size / 1024 / 1024

        click.echo(f"Uploading {file_path} to {bucket}/{key} ({size_mb:.2f} MB)...")
        s3_client.upload_file(file_path, bucket, key)
        click.echo("Upload successful!")
        click.echo(f"S3 URI: s3://{bucket}/{key}")

    except ClientError as e:
        click.echo(f"Failed to upload: {e}", err=True)
        sys.exit(1)


@s3.command("delete-object")
@click.argument("s3_key")
@click.option("--bucket", "-b", help="S3 bucket name")
@click.confirmation_option(prompt="Are you sure you want to delete this object?")
def s3_delete_object(s3_key: str, bucket: Optional[str]):
    """Delete object from S3."""
    import boto3
    from botocore.exceptions import ClientError
    from scripts.config_loader import get_config

    if not bucket:
        config = get_config()
        bucket = config.aws_s3_bucket

    try:
        s3_client = boto3.client('s3')
        s3_client.delete_object(Bucket=bucket, Key=s3_key)
        click.echo(f"Deleted {bucket}/{s3_key}")

    except ClientError as e:
        click.echo(f"Failed to delete: {e}", err=True)
        sys.exit(1)


@s3.command("info")
@click.argument("s3_key")
@click.option("--bucket", "-b", help="S3 bucket name")
def s3_info(s3_key: str, bucket: Optional[str]):
    """Get object metadata from S3."""
    import boto3
    from botocore.exceptions import ClientError
    from scripts.config_loader import get_config

    if not bucket:
        config = get_config()
        bucket = config.aws_s3_bucket

    try:
        s3_client = boto3.client('s3')
        response = s3_client.head_object(Bucket=bucket, Key=s3_key)

        click.echo(f"S3 Object Info: {bucket}/{s3_key}")
        click.echo("-" * 50)
        click.echo(f"Size: {response['ContentLength']:,} bytes ({response['ContentLength'] / 1024 / 1024:.2f} MB)")
        click.echo(f"Content Type: {response.get('ContentType', 'N/A')}")
        click.echo(f"Last Modified: {response['LastModified'].strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"ETag: {response['ETag']}")

        if response.get('Metadata'):
            click.echo("Metadata:")
            for key, value in response['Metadata'].items():
                click.echo(f"  {key}: {value}")

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            click.echo(f"Object not found: {bucket}/{s3_key}", err=True)
        else:
            click.echo(f"Failed to get object info: {e}", err=True)
        sys.exit(1)


# ============ Database Commands ============

@cli.group()
def db():
    """Database management commands."""
    pass


@db.command("init")
def db_init():
    """Initialize database tables (use SQL script for production)."""
    init_db()
    click.echo("Database tables created.")


@db.command("test")
def db_test():
    """Test database connection."""
    from scripts.db import get_engine

    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            click.echo("Database connection successful!")
    except Exception as e:
        click.echo(f"Database connection failed: {e}", err=True)
        sys.exit(1)


@db.command("stats")
def db_stats():
    """Show database statistics."""
    from scripts.db import DatabaseSession
    from sqlalchemy import text

    session = DatabaseSession()
    try:
        # Table counts
        tables_info = [
            ("Videos", "video", ["status"]),
            ("Transcripts", "transcript", ["status", "provider"]),
            ("TranscriptSegments", "transcript_segment", []),
            ("Clips", "clip", ["status"]),
            ("CompiledVideos", "compiled_video", ["status"]),
            ("Conversations", "conversation", []),
            ("ChatMessages", "chat_message", ["role"]),
            ("Users", "user", ["is_admin", "is_active"]),
            ("Projects", "project", []),
            ("Personas", "persona", [])
        ]

        click.echo("Database Statistics")
        click.echo("=" * 50)

        for table_name, table, breakdown_cols in tables_info:
            try:
                # Get total count
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                total = result.scalar()
                click.echo(f"{table_name}: {total:,}")

                # Get breakdown by status/other columns
                for col in breakdown_cols:
                    try:
                        result = session.execute(text(f"SELECT {col}, COUNT(*) FROM {table} WHERE {col} IS NOT NULL GROUP BY {col} ORDER BY COUNT(*) DESC"))
                        breakdown = result.fetchall()
                        if breakdown:
                            click.echo(f"  By {col}:")
                            for value, count in breakdown:
                                click.echo(f"    {value}: {count:,}")
                    except Exception:
                        pass
                click.echo()
            except Exception as e:
                click.echo(f"{table_name}: Error - {e}")
                click.echo()

    except Exception as e:
        click.echo(f"Failed to get statistics: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@db.command("query")
@click.argument("sql_query")
@click.option("--limit", "-l", default=100, help="Limit results")
@click.option("--format", "-f", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format")
def db_query(sql_query: str, limit: int, format: str):
    """Execute SQL query and display results."""
    from scripts.db import DatabaseSession
    from sqlalchemy import text
    import json

    session = DatabaseSession()
    try:
        # Add LIMIT if not present and limit > 0
        query = sql_query.strip()
        if limit > 0 and not query.upper().contains(" LIMIT "):
            query += f" LIMIT {limit}"

        result = session.execute(text(query))

        if result.returns_rows:
            rows = result.fetchall()
            if not rows:
                click.echo("No results found.")
                return

            columns = list(result.keys())

            if format == "json":
                data = [dict(zip(columns, row)) for row in rows]
                click.echo(json.dumps(data, indent=2, default=str))
            elif format == "csv":
                # Header
                click.echo(",".join(columns))
                # Data
                for row in rows:
                    escaped_values = []
                    for value in row:
                        str_val = str(value) if value is not None else ""
                        if "," in str_val or '"' in str_val:
                            str_val = '"' + str_val.replace('"', '""') + '"'
                        escaped_values.append(str_val)
                    click.echo(",".join(escaped_values))
            else:  # table format
                # Calculate column widths
                col_widths = {}
                for i, col in enumerate(columns):
                    max_width = max(len(col), max(len(str(row[i])) for row in rows))
                    col_widths[i] = min(max_width, 50)  # Cap at 50 chars

                # Header
                header_row = " | ".join(col.ljust(col_widths[i]) for i, col in enumerate(columns))
                click.echo(header_row)
                click.echo("-" * len(header_row))

                # Data
                for row in rows:
                    data_row = " | ".join(str(row[i])[:col_widths[i]].ljust(col_widths[i]) for i in range(len(columns)))
                    click.echo(data_row)

            click.echo(f"\n({len(rows)} row(s))")
        else:
            # Non-SELECT query
            click.echo(f"Query executed. Rows affected: {result.rowcount}")

    except Exception as e:
        click.echo(f"Query failed: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@db.command("backup-metadata")
@click.option("--output", "-o", default="db_backup.json", help="Output JSON file")
def db_backup_metadata(output: str):
    """Backup database metadata to JSON."""
    from scripts.db import DatabaseSession
    from sqlalchemy import text
    import json
    from datetime import datetime

    session = DatabaseSession()
    try:
        backup_data = {
            "backup_timestamp": datetime.now().isoformat(),
            "tables": {}
        }

        tables = ["video", "transcript", "transcript_segment", "clip", "compiled_video",
                 "conversation", "chat_message", "user", "project", "persona"]

        for table in tables:
            try:
                result = session.execute(text(f"SELECT * FROM {table}"))
                rows = result.fetchall()
                columns = list(result.keys())

                backup_data["tables"][table] = {
                    "columns": columns,
                    "row_count": len(rows),
                    "data": [dict(zip(columns, row)) for row in rows]
                }

                click.echo(f"Backed up {table}: {len(rows)} rows")
            except Exception as e:
                click.echo(f"Failed to backup {table}: {e}")

        with open(output, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)

        file_size = Path(output).stat().st_size / 1024 / 1024
        click.echo(f"\nBackup completed: {output} ({file_size:.2f} MB)")

    except Exception as e:
        click.echo(f"Backup failed: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@db.command("users")
@click.option("--active-only", is_flag=True, help="Show only active users")
def db_users(active_only: bool):
    """List users."""
    from scripts.db import DatabaseSession
    from sqlalchemy import text

    session = DatabaseSession()
    try:
        query = "SELECT username, email, is_admin, is_active, created_at, last_login_at FROM user"
        if active_only:
            query += " WHERE is_active = true"
        query += " ORDER BY created_at DESC"

        result = session.execute(text(query))
        users = result.fetchall()

        if not users:
            click.echo("No users found.")
            return

        click.echo(f"{'Username':<20} {'Email':<30} {'Admin':<6} {'Active':<7} {'Created':<20} {'Last Login':<20}")
        click.echo("-" * 110)

        for user in users:
            username, email, is_admin, is_active, created_at, last_login = user
            admin_str = "Yes" if is_admin else "No"
            active_str = "Yes" if is_active else "No"
            created_str = created_at.strftime('%Y-%m-%d %H:%M') if created_at else "N/A"
            login_str = last_login.strftime('%Y-%m-%d %H:%M') if last_login else "Never"

            click.echo(f"{username:<20} {email:<30} {admin_str:<6} {active_str:<7} {created_str:<20} {login_str:<20}")

    except Exception as e:
        click.echo(f"Failed to list users: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@db.command("conversations")
@click.option("--user", "-u", help="Filter by username")
@click.option("--limit", "-l", default=20, help="Limit results")
def db_conversations(user: Optional[str], limit: int):
    """List recent conversations."""
    from scripts.db import DatabaseSession
    from sqlalchemy import text

    session = DatabaseSession()
    try:
        query = """
            SELECT c.id, c.title, u.username, c.created_at, c.updated_at,
                   (SELECT COUNT(*) FROM chat_message WHERE conversation_id = c.id) as message_count
            FROM conversation c
            LEFT JOIN user u ON c.user_id = u.id
        """
        params = {}

        if user:
            query += " WHERE u.username = :username"
            params["username"] = user

        query += " ORDER BY c.updated_at DESC LIMIT :limit"
        params["limit"] = limit

        result = session.execute(text(query), params)
        conversations = result.fetchall()

        if not conversations:
            click.echo("No conversations found.")
            return

        click.echo(f"{'ID':<36} {'Title':<30} {'User':<15} {'Messages':<9} {'Updated':<20}")
        click.echo("-" * 115)

        for conv in conversations:
            conv_id, title, username, created_at, updated_at, msg_count = conv
            title_display = (title[:27] + "...") if title and len(title) > 30 else (title or "Untitled")
            username_display = username or "Unknown"
            updated_str = updated_at.strftime('%Y-%m-%d %H:%M') if updated_at else "N/A"

            click.echo(f"{str(conv_id):<36} {title_display:<30} {username_display:<15} {msg_count:<9} {updated_str:<20}")

    except Exception as e:
        click.echo(f"Failed to list conversations: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


# ============ Storyline Commands ============

@cli.group()
def storylines():
    """AI-powered storyline generator and auto-editor."""
    pass


@storylines.command("generate")
@click.option("--refresh", is_flag=True, help="Force regeneration (ignore cache)")
def storylines_generate(refresh: bool):
    """Generate 5 storylines from all transcripts using AI."""
    from scripts.storylines import generate_storylines, format_storylines_display

    click.echo("Analyzing transcripts and generating storylines...")
    click.echo("(This may take 30-60 seconds)\n")

    try:
        storyline_list = generate_storylines(force_refresh=refresh)
        click.echo(format_storylines_display(storyline_list))
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Failed to generate storylines: {e}", err=True)
        sys.exit(1)


@storylines.command("preview")
@click.argument("storyline_id", type=int)
def storylines_preview(storyline_id: int):
    """Preview clips for a specific storyline."""
    from scripts.storylines import preview_storyline, format_storyline_preview, get_cached_storylines

    storylines_list = get_cached_storylines()
    if not storylines_list:
        click.echo("No storylines found. Run 'storylines generate' first.", err=True)
        sys.exit(1)

    storyline = preview_storyline(storyline_id)
    if not storyline:
        click.echo(f"Storyline {storyline_id} not found.", err=True)
        click.echo(f"Available: {[s.id for s in storylines_list]}")
        sys.exit(1)

    click.echo(format_storyline_preview(storyline))


@storylines.command("create")
@click.argument("storyline_id", type=int)
@click.option("--output", "-o", help="Output filename")
def storylines_create(storyline_id: int, output: Optional[str]):
    """Create the final video for a storyline."""
    from scripts.storylines import create_storyline_video, preview_storyline

    storyline = preview_storyline(storyline_id)
    if not storyline:
        click.echo(f"Storyline {storyline_id} not found. Run 'storylines generate' first.", err=True)
        sys.exit(1)

    click.echo(f"Creating video: {storyline.title}")
    click.echo(f"Clips: {len(storyline.clips)}")
    click.echo(f"Duration: ~{storyline.estimated_duration:.1f}s")
    click.echo("")

    result = create_storyline_video(storyline_id, output_name=output)

    if result:
        click.echo(f"\nVideo created successfully!")
        click.echo(f"Output: {result}")
        click.echo(f"Size: {result.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        click.echo("Failed to create video.", err=True)
        sys.exit(1)


@storylines.command("list")
def storylines_list():
    """List cached storylines without regenerating."""
    from scripts.storylines import get_cached_storylines, format_storylines_display

    storylines_list = get_cached_storylines()
    if not storylines_list:
        click.echo("No storylines cached. Run 'storylines generate' first.")
        return

    click.echo(format_storylines_display(storylines_list))


if __name__ == "__main__":
    cli()
