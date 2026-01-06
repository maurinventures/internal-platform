#!/usr/bin/env python3
"""
Analyze video database to identify issues with duration and descriptions.

This script examines the current video data to find:
1. Videos with missing or inaccurate duration_seconds values
2. Videos that have transcripts but poor/missing descriptions
"""

import sys
from pathlib import Path
from decimal import Decimal
from typing import List, Dict, Any

# Add the scripts directory to Python path
sys.path.append(str(Path(__file__).parent))

import db
from db import DatabaseSession, Video, Transcript
from sqlalchemy import func, and_, or_


def analyze_video_durations(session) -> Dict[str, List[Dict[str, Any]]]:
    """Analyze video duration data for issues."""
    print("🔍 Analyzing video durations...")

    results = {
        'missing_duration': [],
        'zero_duration': [],
        'suspicious_duration': [],
        'total_videos': 0
    }

    # Count total videos
    total_count = session.query(Video).count()
    results['total_videos'] = total_count
    print(f"📊 Total videos in database: {total_count}")

    # Find videos with missing duration
    missing_duration = session.query(Video).filter(Video.duration_seconds.is_(None)).all()
    for video in missing_duration:
        results['missing_duration'].append({
            'id': str(video.id),
            'filename': video.filename,
            'original_filename': video.original_filename,
            'status': video.status,
            'created_at': video.created_at.isoformat() if video.created_at else None
        })

    # Find videos with zero duration
    zero_duration = session.query(Video).filter(Video.duration_seconds == 0).all()
    for video in zero_duration:
        results['zero_duration'].append({
            'id': str(video.id),
            'filename': video.filename,
            'original_filename': video.original_filename,
            'duration_seconds': float(video.duration_seconds),
            'status': video.status
        })

    # Find videos with suspiciously short/long durations
    suspicious_duration = session.query(Video).filter(
        and_(
            Video.duration_seconds.is_not(None),
            or_(
                Video.duration_seconds < Decimal('0.1'),  # Less than 0.1 seconds
                Video.duration_seconds > Decimal('7200')  # More than 2 hours
            )
        )
    ).all()

    for video in suspicious_duration:
        results['suspicious_duration'].append({
            'id': str(video.id),
            'filename': video.filename,
            'original_filename': video.original_filename,
            'duration_seconds': float(video.duration_seconds),
            'status': video.status
        })

    return results


def analyze_video_descriptions(session) -> Dict[str, List[Dict[str, Any]]]:
    """Analyze video descriptions and identify improvement opportunities."""
    print("🔍 Analyzing video descriptions...")

    results = {
        'missing_description': [],
        'poor_description': [],
        'has_transcript_no_description': [],
        'has_transcript_poor_description': []
    }

    # Find videos with missing descriptions
    missing_desc = session.query(Video).filter(
        or_(Video.description.is_(None), Video.description == '')
    ).all()

    for video in missing_desc:
        # Check if this video has a transcript
        has_transcript = session.query(Transcript).filter(
            and_(
                Transcript.video_id == video.id,
                Transcript.status == 'completed'
            )
        ).first() is not None

        video_data = {
            'id': str(video.id),
            'filename': video.filename,
            'original_filename': video.original_filename,
            'status': video.status,
            'has_transcript': has_transcript
        }

        results['missing_description'].append(video_data)
        if has_transcript:
            results['has_transcript_no_description'].append(video_data)

    # Find videos with poor descriptions (very short, generic)
    poor_desc = session.query(Video).filter(
        and_(
            Video.description.is_not(None),
            Video.description != '',
            func.length(Video.description) < 50  # Less than 50 characters
        )
    ).all()

    for video in poor_desc:
        # Check if this video has a transcript
        has_transcript = session.query(Transcript).filter(
            and_(
                Transcript.video_id == video.id,
                Transcript.status == 'completed'
            )
        ).first() is not None

        video_data = {
            'id': str(video.id),
            'filename': video.filename,
            'original_filename': video.original_filename,
            'description': video.description,
            'description_length': len(video.description) if video.description else 0,
            'status': video.status,
            'has_transcript': has_transcript
        }

        results['poor_description'].append(video_data)
        if has_transcript:
            results['has_transcript_poor_description'].append(video_data)

    return results


def analyze_transcript_coverage(session) -> Dict[str, Any]:
    """Analyze transcript coverage and quality."""
    print("🔍 Analyzing transcript coverage...")

    # Count videos with and without transcripts
    total_videos = session.query(Video).count()

    videos_with_completed_transcripts = session.query(Video).join(Transcript).filter(
        Transcript.status == 'completed'
    ).distinct().count()

    videos_with_any_transcripts = session.query(Video).join(Transcript).distinct().count()

    # Get transcript quality stats
    transcript_stats = session.query(
        func.avg(Transcript.word_count),
        func.min(Transcript.word_count),
        func.max(Transcript.word_count),
        func.count(Transcript.id)
    ).filter(Transcript.status == 'completed').first()

    avg_words, min_words, max_words, transcript_count = transcript_stats

    return {
        'total_videos': total_videos,
        'videos_with_completed_transcripts': videos_with_completed_transcripts,
        'videos_with_any_transcripts': videos_with_any_transcripts,
        'videos_without_transcripts': total_videos - videos_with_any_transcripts,
        'transcript_coverage_percent': (videos_with_completed_transcripts / total_videos * 100) if total_videos > 0 else 0,
        'completed_transcript_count': transcript_count,
        'avg_words_per_transcript': float(avg_words) if avg_words else 0,
        'min_words_per_transcript': min_words if min_words else 0,
        'max_words_per_transcript': max_words if max_words else 0
    }


def print_analysis_report(duration_results: Dict, description_results: Dict, transcript_results: Dict):
    """Print a comprehensive analysis report."""
    print("\n" + "="*80)
    print("📋 VIDEO DATABASE ANALYSIS REPORT")
    print("="*80)

    # Duration Analysis
    print(f"\n🕒 DURATION ANALYSIS")
    print(f"├─ Total videos: {duration_results['total_videos']}")
    print(f"├─ Missing duration: {len(duration_results['missing_duration'])}")
    print(f"├─ Zero duration: {len(duration_results['zero_duration'])}")
    print(f"└─ Suspicious duration: {len(duration_results['suspicious_duration'])}")

    if duration_results['missing_duration']:
        print(f"\n   ❌ Videos with missing duration:")
        for video in duration_results['missing_duration'][:5]:  # Show first 5
            print(f"      • {video['original_filename']} (ID: {video['id'][:8]}...)")
        if len(duration_results['missing_duration']) > 5:
            print(f"      ... and {len(duration_results['missing_duration']) - 5} more")

    # Description Analysis
    print(f"\n📝 DESCRIPTION ANALYSIS")
    print(f"├─ Missing descriptions: {len(description_results['missing_description'])}")
    print(f"├─ Poor descriptions: {len(description_results['poor_description'])}")
    print(f"├─ Has transcript, no description: {len(description_results['has_transcript_no_description'])}")
    print(f"└─ Has transcript, poor description: {len(description_results['has_transcript_poor_description'])}")

    # Show opportunities for transcript-based descriptions
    transcript_opportunities = (
        len(description_results['has_transcript_no_description']) +
        len(description_results['has_transcript_poor_description'])
    )

    if transcript_opportunities > 0:
        print(f"\n   ✨ Opportunities for transcript-based descriptions: {transcript_opportunities}")

        # Show some examples
        examples = (description_results['has_transcript_no_description'] +
                   description_results['has_transcript_poor_description'])[:3]
        for video in examples:
            desc = video.get('description', 'No description')
            if not desc or desc == '':
                desc = 'No description'
            print(f"      • {video['original_filename']}: \"{desc}\"")

    # Transcript Coverage
    print(f"\n📊 TRANSCRIPT COVERAGE")
    print(f"├─ Total videos: {transcript_results['total_videos']}")
    print(f"├─ With completed transcripts: {transcript_results['videos_with_completed_transcripts']}")
    print(f"├─ Coverage: {transcript_results['transcript_coverage_percent']:.1f}%")
    print(f"├─ Average words per transcript: {transcript_results['avg_words_per_transcript']:.0f}")
    print(f"└─ Word count range: {transcript_results['min_words_per_transcript']}-{transcript_results['max_words_per_transcript']}")

    # Summary and Recommendations
    print(f"\n💡 RECOMMENDATIONS")

    total_duration_issues = (
        len(duration_results['missing_duration']) +
        len(duration_results['zero_duration']) +
        len(duration_results['suspicious_duration'])
    )

    if total_duration_issues > 0:
        print(f"├─ Fix {total_duration_issues} videos with duration issues using ffprobe")

    if transcript_opportunities > 0:
        print(f"├─ Generate descriptions for {transcript_opportunities} videos using transcript content")

    videos_needing_transcripts = transcript_results['videos_without_transcripts']
    if videos_needing_transcripts > 0:
        print(f"└─ Consider generating transcripts for {videos_needing_transcripts} videos without them")

    if total_duration_issues == 0 and transcript_opportunities == 0:
        print("└─ ✅ Video database looks good! All durations and descriptions are in good shape.")

    print("="*80)


def main():
    """Run the video database analysis."""
    print("🚀 Starting video database analysis...")

    try:
        with DatabaseSession() as session:
            # Run all analyses
            duration_results = analyze_video_durations(session)
            description_results = analyze_video_descriptions(session)
            transcript_results = analyze_transcript_coverage(session)

            # Print comprehensive report
            print_analysis_report(duration_results, description_results, transcript_results)

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())