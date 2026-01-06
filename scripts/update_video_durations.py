#!/usr/bin/env python3
"""
Update video durations in database using accurate ffprobe measurements.

This script recalculates video file durations by downloading videos from S3,
running ffprobe to get accurate durations, and updating the database records.
"""

import json
import logging
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import boto3
from botocore.exceptions import ClientError
from tqdm import tqdm

# Add the scripts directory to Python path
sys.path.append(str(Path(__file__).parent))

try:
    from .config_loader import get_config
except ImportError:
    from config_loader import get_config

try:
    from .db import DatabaseSession, Video, get_session
except ImportError:
    from db import DatabaseSession, Video, get_session

logger = logging.getLogger(__name__)


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_s3_client():
    """Get configured S3 client."""
    config = get_config()
    session = boto3.Session()

    # Use AWS credentials from config
    if config.aws_access_key and config.aws_secret_key:
        session = boto3.Session(
            aws_access_key_id=config.aws_access_key,
            aws_secret_access_key=config.aws_secret_key,
            region_name=config.aws_region
        )

    return session.client('s3')


def get_video_duration_ffprobe(video_path: Path) -> Optional[Decimal]:
    """
    Get accurate video duration using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds as Decimal, or None if error
    """
    try:
        # Run ffprobe to get video metadata
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60  # 1 minute timeout
        )

        data = json.loads(result.stdout)

        # Try to get duration from format first (most reliable)
        if 'format' in data and 'duration' in data['format']:
            duration_str = data['format']['duration']
            try:
                return Decimal(str(duration_str)).quantize(Decimal('0.01'))
            except:
                pass

        # Fallback: get duration from video stream
        if 'streams' in data:
            for stream in data['streams']:
                if stream.get('codec_type') == 'video':
                    if 'duration' in stream:
                        try:
                            duration_str = stream['duration']
                            return Decimal(str(duration_str)).quantize(Decimal('0.01'))
                        except:
                            continue

        logger.warning(f"Could not determine duration for {video_path}")
        return None

    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe failed for {video_path}: {e}")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"ffprobe timeout for {video_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ffprobe output for {video_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting duration for {video_path}: {e}")
        return None


def download_video_from_s3(s3_client, bucket: str, s3_key: str, local_path: Path) -> bool:
    """
    Download video file from S3 to local path.

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        s3_key: S3 key for video file
        local_path: Local path to download to

    Returns:
        True if download successful, False otherwise
    """
    try:
        # Get file size for progress bar
        response = s3_client.head_object(Bucket=bucket, Key=s3_key)
        file_size = response['ContentLength']

        with tqdm(
            total=file_size,
            unit='B',
            unit_scale=True,
            desc=f"Downloading {Path(s3_key).name}"
        ) as pbar:
            def callback(bytes_transferred):
                pbar.update(bytes_transferred)

            s3_client.download_file(
                bucket,
                s3_key,
                str(local_path),
                Callback=callback
            )

        return True

    except ClientError as e:
        logger.error(f"Failed to download {s3_key}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {s3_key}: {e}")
        return False


def update_video_duration(video_id: UUID, new_duration: Decimal) -> bool:
    """
    Update video duration in database.

    Args:
        video_id: Video ID to update
        new_duration: New duration in seconds

    Returns:
        True if update successful
    """
    try:
        with DatabaseSession() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if not video:
                logger.error(f"Video {video_id} not found in database")
                return False

            old_duration = video.duration_seconds
            video.duration_seconds = new_duration
            session.commit()

            logger.info(
                f"Updated video {video_id} duration: "
                f"{old_duration} → {new_duration} seconds"
            )
            return True

    except Exception as e:
        logger.error(f"Failed to update duration for {video_id}: {e}")
        return False


def find_videos_needing_duration_update(
    session,
    check_all: bool = False
) -> List[Video]:
    """
    Find videos that need duration updates.

    Args:
        session: Database session
        check_all: If True, check all videos. If False, only check videos with missing/zero durations

    Returns:
        List of Video objects that need updates
    """
    if check_all:
        videos = session.query(Video).filter(Video.status == 'uploaded').all()
        logger.info(f"Found {len(videos)} total uploaded videos to check")
    else:
        # Find videos with missing, zero, or suspicious durations
        videos = session.query(Video).filter(
            Video.status == 'uploaded'
        ).filter(
            (Video.duration_seconds.is_(None)) |
            (Video.duration_seconds == 0) |
            (Video.duration_seconds < Decimal('0.1')) |
            (Video.duration_seconds > Decimal('7200'))  # > 2 hours
        ).all()
        logger.info(f"Found {len(videos)} videos with duration issues")

    return videos


def update_video_durations_batch(
    videos: List[Video],
    batch_size: int = 10,
    temp_dir: Optional[Path] = None
) -> Dict[str, int]:
    """
    Update durations for a batch of videos.

    Args:
        videos: List of Video objects to update
        batch_size: Number of videos to process simultaneously
        temp_dir: Directory for temporary files

    Returns:
        Dictionary with update statistics
    """
    if not videos:
        return {'processed': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

    config = get_config()
    s3_client = get_s3_client()
    stats = {'processed': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

    # Use provided temp dir or create one
    if temp_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix='video_duration_update_'))

    try:
        logger.info(f"Processing {len(videos)} videos in batches of {batch_size}")

        for i in range(0, len(videos), batch_size):
            batch = videos[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: videos {i+1}-{min(i+batch_size, len(videos))}")

            for video in tqdm(batch, desc="Processing videos"):
                stats['processed'] += 1

                try:
                    # Download video to temp location
                    temp_file = temp_dir / f"video_{video.id}.tmp"

                    success = download_video_from_s3(
                        s3_client,
                        video.s3_bucket,
                        video.s3_key,
                        temp_file
                    )

                    if not success:
                        stats['errors'] += 1
                        continue

                    # Get accurate duration using ffprobe
                    duration = get_video_duration_ffprobe(temp_file)

                    # Clean up temp file immediately
                    if temp_file.exists():
                        temp_file.unlink()

                    if duration is None:
                        logger.error(f"Could not determine duration for {video.filename}")
                        stats['errors'] += 1
                        continue

                    # Check if duration actually needs updating
                    current_duration = video.duration_seconds
                    if current_duration is not None:
                        # Allow for small differences due to rounding
                        diff = abs(float(duration) - float(current_duration))
                        if diff < 0.1:  # Less than 0.1 second difference
                            logger.debug(f"Duration for {video.filename} is already accurate ({current_duration}s)")
                            stats['skipped'] += 1
                            continue

                    # Update duration in database
                    success = update_video_duration(video.id, duration)
                    if success:
                        stats['updated'] += 1
                    else:
                        stats['errors'] += 1

                except Exception as e:
                    logger.error(f"Error processing video {video.filename}: {e}")
                    stats['errors'] += 1

                    # Clean up temp file if it exists
                    temp_file = temp_dir / f"video_{video.id}.tmp"
                    if temp_file.exists():
                        temp_file.unlink()

    finally:
        # Clean up temp directory
        try:
            if temp_dir.exists():
                for f in temp_dir.glob('*'):
                    f.unlink()
                temp_dir.rmdir()
        except Exception as e:
            logger.warning(f"Could not clean up temp directory {temp_dir}: {e}")

    return stats


def main():
    """Main function to update video durations."""
    setup_logging()

    import argparse
    parser = argparse.ArgumentParser(description='Update video durations in database')
    parser.add_argument(
        '--all',
        action='store_true',
        help='Check all videos, not just those with missing/zero durations'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of videos to process in each batch (default: 10)'
    )
    parser.add_argument(
        '--video-id',
        type=str,
        help='Update duration for a specific video ID only'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )

    args = parser.parse_args()

    logger.info("🚀 Starting video duration update process")

    try:
        with DatabaseSession() as session:
            if args.video_id:
                # Update specific video
                try:
                    video_id = UUID(args.video_id)
                    video = session.query(Video).filter(Video.id == video_id).first()
                    if not video:
                        logger.error(f"Video with ID {video_id} not found")
                        return 1
                    videos = [video]
                    logger.info(f"Processing single video: {video.filename}")
                except ValueError:
                    logger.error(f"Invalid video ID format: {args.video_id}")
                    return 1
            else:
                # Find videos needing updates
                videos = find_videos_needing_duration_update(session, args.all)

                if not videos:
                    logger.info("✅ No videos found that need duration updates!")
                    return 0

            if args.dry_run:
                logger.info("🔍 DRY RUN MODE - No database changes will be made")
                for video in videos:
                    logger.info(
                        f"Would update: {video.filename} "
                        f"(current: {video.duration_seconds}s)"
                    )
                logger.info(f"Total videos that would be processed: {len(videos)}")
                return 0

            # Update durations
            stats = update_video_durations_batch(videos, args.batch_size)

            # Print summary
            logger.info("=" * 60)
            logger.info("📊 UPDATE SUMMARY")
            logger.info(f"Processed: {stats['processed']}")
            logger.info(f"Updated: {stats['updated']}")
            logger.info(f"Skipped (already accurate): {stats['skipped']}")
            logger.info(f"Errors: {stats['errors']}")
            logger.info("=" * 60)

            if stats['updated'] > 0:
                logger.info(f"✅ Successfully updated {stats['updated']} video durations!")
            if stats['errors'] > 0:
                logger.warning(f"⚠️  {stats['errors']} videos had errors during processing")

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())