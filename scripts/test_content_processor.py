#!/usr/bin/env python3
"""
Test suite for Content Processor

Basic validation of content processor functionality without requiring
full API credentials or extensive content.
"""

import sys
import os
from datetime import datetime

# Add paths for imports
sys.path.append('/Users/josephs./internal-platform/web')
sys.path.append('/Users/josephs./internal-platform')
sys.path.append('/Users/josephs./internal-platform/scripts')

try:
    from content_processor import ContentProcessor, ContentItem, SectionData, ChunkData
    from scripts.db import DatabaseSession
    from sqlalchemy import text
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def test_content_processor_initialization():
    """Test basic ContentProcessor initialization."""
    print("🧪 Testing ContentProcessor initialization...")

    try:
        processor = ContentProcessor()

        # Check basic attributes
        assert hasattr(processor, 'stats')
        assert hasattr(processor, 'logger')
        assert hasattr(processor, 'embedding_service')

        print(f"✅ ContentProcessor initialized successfully")
        print(f"  Checkpoint dir: {processor.checkpoint_dir}")
        print(f"  Logger: {processor.logger.name}")
        print(f"  Embedding service: {'Available' if processor.embedding_service else 'Not available'}")
        print(f"  Anthropic client: {'Available' if processor.anthropic_client else 'Not available'}")

        return True

    except Exception as e:
        print(f"❌ ContentProcessor initialization failed: {e}")
        return False


def test_utility_methods():
    """Test utility methods work correctly."""
    print("\n🔧 Testing utility methods...")

    try:
        processor = ContentProcessor()

        # Test token estimation
        test_text = "This is a test text for token estimation."
        tokens = processor._estimate_tokens(test_text)
        print(f"✅ Token estimation: {tokens} tokens for {len(test_text)} characters")

        # Test content hash
        content_hash = processor._compute_content_hash(test_text)
        print(f"✅ Content hash: {content_hash[:16]}...")

        # Test quality scoring
        quality = processor._calculate_quality_score(test_text, 'test')
        print(f"✅ Quality score: {quality}")

        return True

    except Exception as e:
        print(f"❌ Utility methods test failed: {e}")
        return False


def test_section_splitting():
    """Test section splitting with mock data."""
    print("\n📄 Testing section splitting...")

    try:
        processor = ContentProcessor()

        # Create mock content item
        content_item = ContentItem(
            source_type='document',
            source_id='test-123',
            title='Test Document',
            content_type='test',
            content_text="This is the first paragraph.\n\nThis is the second paragraph.\n\nThis is the third paragraph.",
            word_count=15,
            character_count=95
        )

        # Test section creation
        sections = processor.create_sections_from_content(content_item)

        print(f"✅ Section splitting successful")
        print(f"  Input text length: {len(content_item.content_text)} characters")
        print(f"  Sections created: {len(sections)}")

        for i, section in enumerate(sections):
            print(f"    Section {i}: {len(section.content_text)} chars, {section.word_count} words")

        return len(sections) > 0

    except Exception as e:
        print(f"❌ Section splitting test failed: {e}")
        return False


def test_chunking():
    """Test chunking algorithm with mock data."""
    print("\n🧩 Testing chunking algorithm...")

    try:
        processor = ContentProcessor()

        # Create mock section
        long_text = " ".join([f"This is sentence {i}." for i in range(100)])  # ~400 tokens

        section = SectionData(
            section_index=0,
            title="Test Section",
            section_type="test",
            content_text=long_text,
            word_count=len(long_text.split()),
            character_count=len(long_text)
        )

        content_item = ContentItem(
            source_type='test',
            source_id='test-chunk',
            title='Test Chunking',
            content_type='test'
        )

        # Test chunk creation
        chunks = processor.create_chunks_from_sections([section], content_item)

        print(f"✅ Chunking successful")
        print(f"  Input text: {len(long_text)} characters")
        print(f"  Estimated tokens: {processor._estimate_tokens(long_text)}")
        print(f"  Chunks created: {len(chunks)}")

        for i, chunk in enumerate(chunks):
            print(f"    Chunk {i}: {chunk.token_count} tokens, {chunk.character_count} chars")
            if chunk.context_before:
                print(f"      Context before: {len(chunk.context_before)} chars")
            if chunk.context_after:
                print(f"      Context after: {len(chunk.context_after)} chars")

        return len(chunks) > 0

    except Exception as e:
        print(f"❌ Chunking test failed: {e}")
        return False


def test_database_connectivity():
    """Test database connectivity and RAG tables exist."""
    print("\n🗄️ Testing database connectivity...")

    try:
        with DatabaseSession() as session:
            # Test that RAG tables exist
            tables_result = session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('rag_documents', 'rag_sections', 'rag_chunks', 'corpus_summary')
            """)).fetchall()

            table_names = [row[0] for row in tables_result]
            print(f"✅ Database connection successful")
            print(f"  Found RAG tables: {table_names}")

            if len(table_names) >= 4:
                print(f"✅ All required RAG tables exist")

                # Check current content counts
                doc_count = session.execute(text("SELECT COUNT(*) FROM rag_documents")).scalar()
                section_count = session.execute(text("SELECT COUNT(*) FROM rag_sections")).scalar()
                chunk_count = session.execute(text("SELECT COUNT(*) FROM rag_chunks")).scalar()

                print(f"  Current RAG content:")
                print(f"    Documents: {doc_count}")
                print(f"    Sections: {section_count}")
                print(f"    Chunks: {chunk_count}")

                return True
            else:
                print(f"❌ Missing RAG tables. Found: {table_names}")
                print(f"  Expected: ['rag_documents', 'rag_sections', 'rag_chunks', 'corpus_summary']")
                return False

    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False


def test_content_iteration():
    """Test content iteration (without processing)."""
    print("\n📊 Testing content iteration...")

    try:
        processor = ContentProcessor()

        # Test getting content items (limit to 5 for testing)
        content_items = processor.get_all_content_items(limit=5)

        print(f"✅ Content iteration successful")
        print(f"  Found {len(content_items)} content items (limited to 5)")

        for i, item in enumerate(content_items):
            print(f"    Item {i}: {item.source_type} - {item.title[:50]}...")

        return True

    except Exception as e:
        print(f"❌ Content iteration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("CONTENT PROCESSOR TEST SUITE")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    def run_test(test_func, description):
        nonlocal tests_passed, tests_failed
        try:
            if test_func():
                tests_passed += 1
                return True
            else:
                tests_failed += 1
                return False
        except Exception as e:
            print(f"❌ {description} crashed: {e}")
            tests_failed += 1
            return False

    # Run tests
    run_test(test_content_processor_initialization, "ContentProcessor initialization")
    run_test(test_utility_methods, "Utility methods")
    run_test(test_section_splitting, "Section splitting")
    run_test(test_chunking, "Chunking algorithm")
    run_test(test_database_connectivity, "Database connectivity")
    run_test(test_content_iteration, "Content iteration")

    # Print results
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    total_tests = tests_passed + tests_failed
    print(f"Tests passed: {tests_passed}/{total_tests}")
    print(f"Tests failed: {tests_failed}/{total_tests}")

    if tests_failed == 0:
        print("✅ ALL TESTS PASSED!")
        status = "READY FOR PRODUCTION USE"
    else:
        print("❌ SOME TESTS FAILED")
        status = "REQUIRES FIXES BEFORE USE"

    print(f"\nContent Processor Status: {status}")
    print("=" * 60)

    return tests_failed == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)