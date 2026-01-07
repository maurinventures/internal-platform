#!/usr/bin/env python3
"""
Check data volumes to understand the scope of transcript processing.
"""

import sys
import os

# Add the current directory to sys.path so we can import our modules
sys.path.append('/Users/josephs./internal-platform/web')
sys.path.append('/Users/josephs./internal-platform')

try:
    from scripts.db import DatabaseSession, Video, Transcript, TranscriptSegment, User, Conversation, ExternalContent
except ImportError:
    print("Could not import database modules")
    sys.exit(1)


def check_data_volumes():
    """Check the current data volumes in the system."""
    print("Checking data volumes in the database...")

    try:
        with DatabaseSession() as db_session:
            # Count main entities
            video_count = db_session.query(Video).count()
            transcript_count = db_session.query(Transcript).count()
            segment_count = db_session.query(TranscriptSegment).count()
            user_count = db_session.query(User).count()
            conversation_count = db_session.query(Conversation).count()
            external_content_count = db_session.query(ExternalContent).count()

            print(f"\nDATA VOLUMES:")
            print(f"  Videos: {video_count:,}")
            print(f"  Transcripts: {transcript_count:,}")
            print(f"  Transcript segments: {segment_count:,}")
            print(f"  Users: {user_count:,}")
            print(f"  Conversations: {conversation_count:,}")
            print(f"  External content: {external_content_count:,}")

            # Get sample transcript segment lengths
            if segment_count > 0:
                segments = db_session.query(TranscriptSegment).limit(100).all()
                segment_lengths = [len(seg.text) for seg in segments if seg.text]

                if segment_lengths:
                    avg_segment_length = sum(segment_lengths) / len(segment_lengths)
                    max_segment_length = max(segment_lengths)
                    min_segment_length = min(segment_lengths)

                    print(f"\nTRANSCRIPT SEGMENT ANALYSIS (sample of {len(segment_lengths)}):")
                    print(f"  Average segment length: {avg_segment_length:.0f} chars")
                    print(f"  Max segment length: {max_segment_length:,} chars")
                    print(f"  Min segment length: {min_segment_length:,} chars")

                    # Estimate tokens (rough: ~4 chars per token)
                    avg_tokens_per_segment = avg_segment_length / 4
                    print(f"  Estimated avg tokens per segment: {avg_tokens_per_segment:.0f}")

                    # With 30-second context expansion, estimate context size
                    # Typically 3-5 segments per 30 seconds of context
                    estimated_context_segments = 4
                    estimated_context_tokens = avg_tokens_per_segment * estimated_context_segments
                    print(f"  Estimated tokens per context (4 segments): {estimated_context_tokens:.0f}")

            # Check for completed transcripts with word counts
            completed_transcripts = db_session.query(Transcript).filter(
                Transcript.status == 'completed',
                Transcript.word_count.isnot(None)
            ).limit(10).all()

            if completed_transcripts:
                word_counts = [t.word_count for t in completed_transcripts if t.word_count]
                if word_counts:
                    avg_words = sum(word_counts) / len(word_counts)
                    print(f"\nTRANSCRIPT WORD COUNTS (sample of {len(word_counts)}):")
                    print(f"  Average words per transcript: {avg_words:,.0f}")
                    print(f"  Estimated tokens per transcript: {avg_words * 1.3:.0f}")  # ~1.3 tokens per word

    except Exception as e:
        print(f"Error querying database: {e}")


if __name__ == "__main__":
    try:
        check_data_volumes()
    except Exception as e:
        print(f"Error running check: {e}")
        import traceback
        traceback.print_exc()