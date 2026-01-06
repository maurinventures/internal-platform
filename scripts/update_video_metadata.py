#!/usr/bin/env python3
"""
Update video metadata: durations and descriptions.

This wrapper script runs both duration and description updates in sequence.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def run_script(script_name: str, args: list) -> bool:
    """
    Run a script with given arguments.

    Args:
        script_name: Name of script to run
        args: Arguments to pass to script

    Returns:
        True if script succeeded, False otherwise
    """
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)] + args

    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True)
        logger.info(f"✅ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {script_name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to run {script_name}: {e}")
        return False


def main():
    """Main function."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description='Update video metadata: durations and descriptions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update durations and descriptions for videos with issues
  python update_video_metadata.py

  # Preview what would be updated without making changes
  python update_video_metadata.py --dry-run

  # Update all videos (including those with existing data)
  python update_video_metadata.py --all

  # Only update durations
  python update_video_metadata.py --durations-only

  # Only update descriptions
  python update_video_metadata.py --descriptions-only

  # Update specific video
  python update_video_metadata.py --video-id 12345678-1234-1234-1234-123456789012
        """
    )

    parser.add_argument(
        '--durations-only',
        action='store_true',
        help='Only update video durations, skip descriptions'
    )
    parser.add_argument(
        '--descriptions-only',
        action='store_true',
        help='Only update video descriptions, skip durations'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Update all videos, not just those with missing/poor data'
    )
    parser.add_argument(
        '--video-id',
        type=str,
        help='Update only the specified video ID'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Batch size for duration updates (default: 10)'
    )
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.0,
        help='Rate limit for description API calls in seconds (default: 1.0)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.durations_only and args.descriptions_only:
        logger.error("Cannot specify both --durations-only and --descriptions-only")
        return 1

    logger.info("🚀 Starting video metadata update process")

    success_count = 0
    total_operations = 0

    # Update durations
    if not args.descriptions_only:
        total_operations += 1
        duration_args = []

        if args.all:
            duration_args.append('--all')
        if args.video_id:
            duration_args.extend(['--video-id', args.video_id])
        if args.dry_run:
            duration_args.append('--dry-run')
        if args.batch_size != 10:
            duration_args.extend(['--batch-size', str(args.batch_size)])

        logger.info("=" * 60)
        logger.info("🕒 UPDATING VIDEO DURATIONS")
        logger.info("=" * 60)

        if run_script('update_video_durations.py', duration_args):
            success_count += 1

    # Update descriptions
    if not args.durations_only:
        total_operations += 1
        description_args = []

        if args.all:
            description_args.append('--all')
        if args.video_id:
            description_args.extend(['--video-id', args.video_id])
        if args.dry_run:
            description_args.append('--preview')  # Different flag name for description script
        if args.rate_limit != 1.0:
            description_args.extend(['--rate-limit', str(args.rate_limit)])

        logger.info("=" * 60)
        logger.info("📝 UPDATING VIDEO DESCRIPTIONS")
        logger.info("=" * 60)

        if run_script('update_video_descriptions.py', description_args):
            success_count += 1

    # Final summary
    logger.info("=" * 60)
    logger.info("🏁 FINAL SUMMARY")
    logger.info(f"Operations completed successfully: {success_count}/{total_operations}")

    if success_count == total_operations:
        logger.info("✅ All operations completed successfully!")
        return 0
    else:
        logger.error(f"❌ {total_operations - success_count} operations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())