#!/usr/bin/env python3
"""
Verify video database updates.

This script checks the results of duration and description updates.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add the scripts directory to Python path
sys.path.append(str(Path(__file__).parent))

try:
    from .db import DatabaseSession, Video, Transcript
except ImportError:
    from db import DatabaseSession, Video, Transcript

from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def check_duration_quality(session) -> Dict[str, int]:
    """Check the quality of video durations in database."""
    results = {
        'total_videos': 0,
        'has_duration': 0,
        'missing_duration': 0,
        'zero_duration': 0,
        'suspicious_duration': 0,
        'good_duration': 0
    }

    total_videos = session.query(Video).count()
    results['total_videos'] = total_videos

    if total_videos == 0:
        return results

    # Count videos with durations
    has_duration = session.query(Video).filter(Video.duration_seconds.is_not(None)).count()
    results['has_duration'] = has_duration

    # Count missing durations
    missing_duration = session.query(Video).filter(Video.duration_seconds.is_(None)).count()
    results['missing_duration'] = missing_duration

    # Count zero durations
    zero_duration = session.query(Video).filter(Video.duration_seconds == 0).count()
    results['zero_duration'] = zero_duration

    # Count suspicious durations
    suspicious_duration = session.query(Video).filter(
        and_(
            Video.duration_seconds.is_not(None),
            (Video.duration_seconds < 0.1) | (Video.duration_seconds > 7200)
        )
    ).count()
    results['suspicious_duration'] = suspicious_duration

    # Count good durations
    good_duration = session.query(Video).filter(
        and_(
            Video.duration_seconds.is_not(None),
            Video.duration_seconds >= 0.1,
            Video.duration_seconds <= 7200
        )
    ).count()
    results['good_duration'] = good_duration

    return results


def check_description_quality(session) -> Dict[str, int]:
    """Check the quality of video descriptions in database."""
    results = {
        'total_videos': 0,
        'has_description': 0,
        'missing_description': 0,
        'short_description': 0,  # < 50 chars
        'good_description': 0,   # >= 50 chars
        'with_transcripts': 0,
        'transcripts_no_description': 0,
        'transcripts_with_description': 0
    }

    total_videos = session.query(Video).count()
    results['total_videos'] = total_videos

    if total_videos == 0:
        return results

    # Count videos with descriptions
    has_description = session.query(Video).filter(
        and_(Video.description.is_not(None), Video.description != '')
    ).count()
    results['has_description'] = has_description

    # Count missing descriptions
    missing_description = session.query(Video).filter(
        (Video.description.is_(None)) | (Video.description == '')
    ).count()
    results['missing_description'] = missing_description

    # Count short descriptions
    short_description = session.query(Video).filter(
        and_(
            Video.description.is_not(None),
            Video.description != '',
            func.length(Video.description) < 50
        )
    ).count()
    results['short_description'] = short_description

    # Count good descriptions
    good_description = session.query(Video).filter(
        and_(
            Video.description.is_not(None),
            Video.description != '',
            func.length(Video.description) >= 50
        )
    ).count()
    results['good_description'] = good_description

    # Transcript-related metrics
    with_transcripts = session.query(Video).join(Transcript).filter(
        Transcript.status == 'completed'
    ).distinct().count()
    results['with_transcripts'] = with_transcripts

    transcripts_no_description = session.query(Video).join(Transcript).filter(
        and_(
            Transcript.status == 'completed',
            (Video.description.is_(None)) | (Video.description == '') |
            (func.length(Video.description) < 50)
        )
    ).distinct().count()
    results['transcripts_no_description'] = transcripts_no_description

    transcripts_with_description = session.query(Video).join(Transcript).filter(
        and_(
            Transcript.status == 'completed',
            Video.description.is_not(None),
            Video.description != '',
            func.length(Video.description) >= 50
        )
    ).distinct().count()
    results['transcripts_with_description'] = transcripts_with_description

    return results


def check_recent_updates(session, hours: int = 24) -> Dict[str, int]:
    """Check for recent updates to video metadata."""
    since = datetime.utcnow() - timedelta(hours=hours)

    recent_updates = session.query(Video).filter(
        Video.updated_at >= since
    ).count()

    # Get some examples of recent updates
    recent_videos = session.query(Video).filter(
        Video.updated_at >= since
    ).order_by(Video.updated_at.desc()).limit(5).all()

    return {
        'recent_updates': recent_updates,
        'examples': [
            {
                'filename': v.filename,
                'updated_at': v.updated_at.isoformat(),
                'duration_seconds': float(v.duration_seconds) if v.duration_seconds else None,
                'description_length': len(v.description) if v.description else 0
            }
            for v in recent_videos
        ]
    }


def print_verification_report(duration_stats: Dict, description_stats: Dict, recent_stats: Dict):
    """Print a comprehensive verification report."""
    print("\n" + "="*80)
    print("📊 VIDEO DATABASE VERIFICATION REPORT")
    print("="*80)

    # Duration Analysis
    print(f"\n🕒 DURATION QUALITY")
    total = duration_stats['total_videos']
    if total > 0:
        print(f"├─ Total videos: {total}")
        print(f"├─ With duration: {duration_stats['has_duration']} ({duration_stats['has_duration']/total*100:.1f}%)")
        print(f"├─ Missing duration: {duration_stats['missing_duration']} ({duration_stats['missing_duration']/total*100:.1f}%)")
        print(f"├─ Zero duration: {duration_stats['zero_duration']} ({duration_stats['zero_duration']/total*100:.1f}%)")
        print(f"├─ Suspicious duration: {duration_stats['suspicious_duration']} ({duration_stats['suspicious_duration']/total*100:.1f}%)")
        print(f"└─ Good duration: {duration_stats['good_duration']} ({duration_stats['good_duration']/total*100:.1f}%)")

        # Duration health score
        duration_health = duration_stats['good_duration'] / total * 100
        if duration_health >= 95:
            print(f"   ✅ Duration Health: {duration_health:.1f}% (Excellent)")
        elif duration_health >= 80:
            print(f"   🟡 Duration Health: {duration_health:.1f}% (Good)")
        else:
            print(f"   ❌ Duration Health: {duration_health:.1f}% (Needs Improvement)")
    else:
        print("├─ No videos in database")

    # Description Analysis
    print(f"\n📝 DESCRIPTION QUALITY")
    if total > 0:
        print(f"├─ Total videos: {total}")
        print(f"├─ With description: {description_stats['has_description']} ({description_stats['has_description']/total*100:.1f}%)")
        print(f"├─ Missing description: {description_stats['missing_description']} ({description_stats['missing_description']/total*100:.1f}%)")
        print(f"├─ Short description (<50 chars): {description_stats['short_description']} ({description_stats['short_description']/total*100:.1f}%)")
        print(f"└─ Good description (≥50 chars): {description_stats['good_description']} ({description_stats['good_description']/total*100:.1f}%)")

        # Description health score
        description_health = description_stats['good_description'] / total * 100
        if description_health >= 80:
            print(f"   ✅ Description Health: {description_health:.1f}% (Excellent)")
        elif description_health >= 60:
            print(f"   🟡 Description Health: {description_health:.1f}% (Good)")
        else:
            print(f"   ❌ Description Health: {description_health:.1f}% (Needs Improvement)")

    # Transcript Utilization
    print(f"\n📊 TRANSCRIPT UTILIZATION")
    if total > 0:
        print(f"├─ Videos with transcripts: {description_stats['with_transcripts']}")
        print(f"├─ Transcripts missing descriptions: {description_stats['transcripts_no_description']}")
        print(f"└─ Transcripts with good descriptions: {description_stats['transcripts_with_description']}")

        if description_stats['with_transcripts'] > 0:
            transcript_utilization = description_stats['transcripts_with_description'] / description_stats['with_transcripts'] * 100
            if transcript_utilization >= 80:
                print(f"   ✅ Transcript Utilization: {transcript_utilization:.1f}% (Excellent)")
            elif transcript_utilization >= 60:
                print(f"   🟡 Transcript Utilization: {transcript_utilization:.1f}% (Good)")
            else:
                print(f"   ❌ Transcript Utilization: {transcript_utilization:.1f}% (Poor)")

    # Recent Updates
    print(f"\n🕒 RECENT ACTIVITY (Last 24 Hours)")
    print(f"└─ Videos updated: {recent_stats['recent_updates']}")

    if recent_stats['examples']:
        print(f"\n   Recent updates:")
        for example in recent_stats['examples']:
            desc_len = example['description_length']
            duration = example['duration_seconds']
            print(f"   • {example['filename']}")
            print(f"     Duration: {duration}s, Description: {desc_len} chars")

    # Overall Assessment
    print(f"\n💡 OVERALL ASSESSMENT")

    issues = []
    if duration_stats['missing_duration'] > 0:
        issues.append(f"{duration_stats['missing_duration']} videos missing durations")
    if duration_stats['zero_duration'] > 0:
        issues.append(f"{duration_stats['zero_duration']} videos with zero duration")
    if duration_stats['suspicious_duration'] > 0:
        issues.append(f"{duration_stats['suspicious_duration']} videos with suspicious durations")
    if description_stats['transcripts_no_description'] > 0:
        issues.append(f"{description_stats['transcripts_no_description']} transcripts without good descriptions")

    if not issues:
        print("└─ ✅ Database is in excellent condition!")
    else:
        print("└─ ❌ Issues found:")
        for issue in issues:
            print(f"     • {issue}")

    print("="*80)


def main():
    """Run verification checks."""
    setup_logging()

    import argparse
    parser = argparse.ArgumentParser(description='Verify video database updates')
    parser.add_argument(
        '--recent-hours',
        type=int,
        default=24,
        help='Check for updates within this many hours (default: 24)'
    )

    args = parser.parse_args()

    print("🔍 Running video database verification...")

    try:
        with DatabaseSession() as session:
            duration_stats = check_duration_quality(session)
            description_stats = check_description_quality(session)
            recent_stats = check_recent_updates(session, args.recent_hours)

            print_verification_report(duration_stats, description_stats, recent_stats)

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())