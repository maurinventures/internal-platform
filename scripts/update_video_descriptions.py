#!/usr/bin/env python3
"""
Generate and update video descriptions using transcript content.

This script analyzes video transcripts using AI to generate meaningful,
informative descriptions and updates the database records.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import openai

# Add the scripts directory to Python path
sys.path.append(str(Path(__file__).parent))

try:
    from .config_loader import get_config
except ImportError:
    from config_loader import get_config

try:
    from .db import DatabaseSession, Video, Transcript, TranscriptSegment, get_session
except ImportError:
    from db import DatabaseSession, Video, Transcript, TranscriptSegment, get_session

from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_openai_client():
    """Get configured OpenAI client."""
    config = get_config()
    api_key = config.openai_api_key

    if not api_key:
        raise ValueError("OpenAI API key not found in configuration")

    return openai.OpenAI(api_key=api_key)


def generate_description_from_transcript(
    transcript_text: str,
    video_filename: str,
    speaker_name: Optional[str] = None,
    event_name: Optional[str] = None
) -> Optional[str]:
    """
    Generate a meaningful description from transcript text using AI.

    Args:
        transcript_text: Full transcript text
        video_filename: Original video filename for context
        speaker_name: Speaker name if available
        event_name: Event name if available

    Returns:
        Generated description or None if failed
    """
    try:
        client = get_openai_client()

        # Truncate transcript if too long (OpenAI has token limits)
        max_transcript_length = 8000  # Conservative limit
        if len(transcript_text) > max_transcript_length:
            transcript_text = transcript_text[:max_transcript_length] + "..."

        # Build context information
        context_parts = []
        if speaker_name:
            context_parts.append(f"Speaker: {speaker_name}")
        if event_name:
            context_parts.append(f"Event: {event_name}")
        if video_filename:
            context_parts.append(f"Filename: {video_filename}")

        context_info = " | ".join(context_parts) if context_parts else ""

        # Create prompt for description generation
        prompt = f"""
Please analyze the following video transcript and generate a concise, informative description (2-3 sentences maximum).

The description should:
- Summarize the main topic or purpose of the video
- Highlight key points or insights discussed
- Be professional and clear
- Be suitable for a video management system

{f"Additional context: {context_info}" if context_info else ""}

Transcript:
{transcript_text}

Description:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective model for this task
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that creates concise, informative descriptions for business videos based on their transcripts. Keep descriptions professional, clear, and under 200 characters when possible."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=150,  # Limit to keep descriptions concise
            temperature=0.3  # Lower temperature for more consistent outputs
        )

        description = response.choices[0].message.content.strip()

        # Clean up the description
        if description.startswith('"') and description.endswith('"'):
            description = description[1:-1]

        # Ensure it's not too long
        if len(description) > 500:  # Database field limit
            description = description[:497] + "..."

        return description

    except Exception as e:
        logger.error(f"Failed to generate description: {e}")
        return None


def get_transcript_text(session, video_id: UUID) -> Optional[str]:
    """
    Get the full transcript text for a video.

    Args:
        session: Database session
        video_id: Video ID

    Returns:
        Full transcript text or None if not available
    """
    try:
        # Get the completed transcript
        transcript = session.query(Transcript).filter(
            Transcript.video_id == video_id,
            Transcript.status == 'completed'
        ).first()

        if not transcript:
            return None

        # Prefer full_text if available
        if transcript.full_text and transcript.full_text.strip():
            return transcript.full_text.strip()

        # Fallback: reconstruct from segments
        segments = session.query(TranscriptSegment).filter(
            TranscriptSegment.transcript_id == transcript.id
        ).order_by(TranscriptSegment.segment_index).all()

        if not segments:
            return None

        # Join segments with proper spacing
        text_parts = []
        for segment in segments:
            if segment.text and segment.text.strip():
                text_parts.append(segment.text.strip())

        return " ".join(text_parts) if text_parts else None

    except Exception as e:
        logger.error(f"Failed to get transcript for video {video_id}: {e}")
        return None


def update_video_description(video_id: UUID, new_description: str) -> bool:
    """
    Update video description in database.

    Args:
        video_id: Video ID to update
        new_description: New description text

    Returns:
        True if update successful
    """
    try:
        with DatabaseSession() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if not video:
                logger.error(f"Video {video_id} not found in database")
                return False

            old_description = video.description
            video.description = new_description
            session.commit()

            logger.info(
                f"Updated video {video.filename} description:\n"
                f"  Old: {repr(old_description)}\n"
                f"  New: {repr(new_description)}"
            )
            return True

    except Exception as e:
        logger.error(f"Failed to update description for {video_id}: {e}")
        return False


def find_videos_needing_description_update(
    session,
    update_existing: bool = False
) -> List[Video]:
    """
    Find videos that need description updates.

    Args:
        session: Database session
        update_existing: If True, update all videos with transcripts.
                        If False, only update videos with missing/poor descriptions

    Returns:
        List of Video objects that need updates
    """
    if update_existing:
        # Get all videos that have completed transcripts
        videos = session.query(Video).join(Transcript).filter(
            Transcript.status == 'completed'
        ).distinct().all()
        logger.info(f"Found {len(videos)} videos with transcripts")
    else:
        # Get videos that have transcripts but missing or poor descriptions
        videos = session.query(Video).join(Transcript).filter(
            Transcript.status == 'completed'
        ).filter(
            (Video.description.is_(None)) |
            (Video.description == '') |
            (func.length(Video.description) < 50)  # Less than 50 characters
        ).distinct().all()
        logger.info(f"Found {len(videos)} videos with transcripts but missing/poor descriptions")

    return videos


def update_video_descriptions_batch(
    videos: List[Video],
    rate_limit_delay: float = 1.0
) -> Dict[str, int]:
    """
    Update descriptions for a batch of videos.

    Args:
        videos: List of Video objects to update
        rate_limit_delay: Delay between API calls to respect rate limits

    Returns:
        Dictionary with update statistics
    """
    if not videos:
        return {'processed': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

    stats = {'processed': 0, 'updated': 0, 'errors': 0, 'skipped': 0}

    logger.info(f"Processing {len(videos)} videos for description updates")

    with DatabaseSession() as session:
        for i, video in enumerate(videos, 1):
            stats['processed'] += 1

            logger.info(f"[{i}/{len(videos)}] Processing: {video.filename}")

            try:
                # Get transcript text
                transcript_text = get_transcript_text(session, video.id)

                if not transcript_text:
                    logger.warning(f"No transcript text available for {video.filename}")
                    stats['skipped'] += 1
                    continue

                if len(transcript_text.strip()) < 50:
                    logger.warning(f"Transcript too short for {video.filename} ({len(transcript_text)} chars)")
                    stats['skipped'] += 1
                    continue

                # Generate description using AI
                description = generate_description_from_transcript(
                    transcript_text,
                    video.original_filename or video.filename,
                    video.speaker,
                    video.event_name
                )

                if not description:
                    logger.error(f"Failed to generate description for {video.filename}")
                    stats['errors'] += 1
                    continue

                # Update database
                success = update_video_description(video.id, description)
                if success:
                    stats['updated'] += 1
                else:
                    stats['errors'] += 1

                # Rate limiting to be nice to OpenAI API
                if rate_limit_delay > 0:
                    time.sleep(rate_limit_delay)

            except Exception as e:
                logger.error(f"Error processing video {video.filename}: {e}")
                stats['errors'] += 1

    return stats


def preview_description_updates(videos: List[Video], max_preview: int = 5) -> None:
    """
    Preview what descriptions would be generated without updating the database.

    Args:
        videos: List of videos to preview
        max_preview: Maximum number of videos to preview
    """
    logger.info(f"🔍 PREVIEW MODE - Showing description generation for first {min(max_preview, len(videos))} videos")

    with DatabaseSession() as session:
        for i, video in enumerate(videos[:max_preview], 1):
            logger.info(f"\n[{i}] Video: {video.filename}")
            logger.info(f"Current description: {repr(video.description or 'None')}")

            try:
                # Get transcript text
                transcript_text = get_transcript_text(session, video.id)

                if not transcript_text:
                    logger.info("❌ No transcript available")
                    continue

                logger.info(f"Transcript length: {len(transcript_text)} characters")
                logger.info(f"Transcript preview: {transcript_text[:200]}...")

                # Generate description
                description = generate_description_from_transcript(
                    transcript_text,
                    video.original_filename or video.filename,
                    video.speaker,
                    video.event_name
                )

                if description:
                    logger.info(f"✅ Generated description: {repr(description)}")
                else:
                    logger.info("❌ Failed to generate description")

                # Small delay to be nice to API
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error previewing {video.filename}: {e}")


def main():
    """Main function to update video descriptions."""
    setup_logging()

    import argparse
    parser = argparse.ArgumentParser(description='Update video descriptions using transcript content')
    parser.add_argument(
        '--all',
        action='store_true',
        help='Update descriptions for all videos with transcripts (including those with existing descriptions)'
    )
    parser.add_argument(
        '--video-id',
        type=str,
        help='Update description for a specific video ID only'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview what descriptions would be generated without updating database'
    )
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.0,
        help='Delay between API calls in seconds (default: 1.0)'
    )

    args = parser.parse_args()

    logger.info("🚀 Starting video description update process")

    try:
        # Test OpenAI connection
        try:
            get_openai_client()
            logger.info("✅ OpenAI API connection successful")
        except Exception as e:
            logger.error(f"❌ Failed to connect to OpenAI API: {e}")
            return 1

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
                videos = find_videos_needing_description_update(session, args.all)

                if not videos:
                    logger.info("✅ No videos found that need description updates!")
                    return 0

            if args.preview:
                preview_description_updates(videos)
                return 0

            # Confirm before proceeding with updates
            if len(videos) > 10:
                response = input(f"About to update descriptions for {len(videos)} videos. This will use OpenAI API. Continue? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Operation cancelled by user")
                    return 0

            # Update descriptions
            stats = update_video_descriptions_batch(videos, args.rate_limit)

            # Print summary
            logger.info("=" * 60)
            logger.info("📊 UPDATE SUMMARY")
            logger.info(f"Processed: {stats['processed']}")
            logger.info(f"Updated: {stats['updated']}")
            logger.info(f"Skipped: {stats['skipped']}")
            logger.info(f"Errors: {stats['errors']}")
            logger.info("=" * 60)

            if stats['updated'] > 0:
                logger.info(f"✅ Successfully updated {stats['updated']} video descriptions!")
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