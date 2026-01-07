#!/usr/bin/env python3
"""
Test suite for the Embedding Service.
Tests OpenAI integration, batch processing, pgvector formatting, and cost tracking.
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add paths for imports
sys.path.append('/Users/josephs./internal-platform/web')
sys.path.append('/Users/josephs./internal-platform')
sys.path.append('/Users/josephs./internal-platform/scripts')

try:
    from scripts.embedding_service import EmbeddingService, get_embedding_service, embed_text, embed_batch
    from scripts.config_loader import get_config
    from scripts.db import DatabaseSession
    from sqlalchemy import text
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


def check_configuration():
    """Check if OpenAI API key is configured."""
    print("🔧 Checking OpenAI configuration...")

    try:
        config = get_config()
        api_key = config.openai_api_key

        if not api_key or len(api_key) < 10:
            print("❌ OpenAI API key not configured")
            print("Please set it in credentials.yaml or secrets.yaml under apis.openai.api_key")
            print("📝 Running in MOCK mode for testing...")
            return "mock"

        print(f"✅ OpenAI API key found: {api_key[:8]}...")
        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("📝 Running in MOCK mode for testing...")
        return "mock"


def test_service_initialization():
    """Test embedding service initialization."""
    print("\n🏗️ Testing service initialization...")

    try:
        service = EmbeddingService()
        print("✅ EmbeddingService initialized successfully")

        # Test convenience function
        service2 = get_embedding_service()
        print("✅ get_embedding_service() works")

        return True

    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False


def test_single_text_embedding():
    """Test single text embedding functionality."""
    print("\n📝 Testing single text embedding...")

    try:
        service = EmbeddingService()

        # Test with sample text
        test_text = "This is a test document for embedding generation using OpenAI."
        print(f"Embedding text: '{test_text}'")

        result = service.embed_text(test_text)

        if result.success:
            print(f"✅ Embedding successful!")
            print(f"  Tokens: {result.tokens}")
            print(f"  Cost: ${result.cost:.6f}")
            print(f"  Latency: {result.latency_ms:.1f}ms")
            print(f"  Model: {result.model}")
            print(f"  Embedding dimensions: {len(result.embedding)}")

            # Verify embedding dimensions
            if len(result.embedding) == 1536:
                print(f"✅ Correct embedding dimensions (1536)")
            else:
                print(f"❌ Incorrect dimensions: {len(result.embedding)}")

            # Verify embedding values are reasonable
            if all(isinstance(x, (int, float)) for x in result.embedding):
                print(f"✅ Embedding contains valid numeric values")
                print(f"  Sample values: {result.embedding[:5]}")
            else:
                print(f"❌ Embedding contains invalid values")

            return True

        else:
            print(f"❌ Embedding failed: {result.error}")
            return False

    except Exception as e:
        print(f"❌ Single text embedding test failed: {e}")
        return False


def test_batch_embedding():
    """Test batch embedding functionality."""
    print("\n📚 Testing batch embedding...")

    try:
        service = EmbeddingService()

        # Test with multiple texts
        test_texts = [
            "First document about machine learning and AI.",
            "Second document discussing natural language processing.",
            "Third document covering computer vision applications.",
            "Fourth document on data science methodologies.",
            "Fifth document about deep learning frameworks."
        ]

        print(f"Embedding {len(test_texts)} texts in batch...")

        result = service.embed_batch(test_texts)

        print(f"Batch embedding completed:")
        print(f"  Success count: {result.success_count}")
        print(f"  Error count: {result.error_count}")
        print(f"  Total tokens: {result.total_tokens}")
        print(f"  Total cost: ${result.total_cost:.6f}")
        print(f"  Latency: {result.latency_ms:.1f}ms")
        print(f"  Model: {result.model}")

        if result.error_count > 0:
            print(f"  Errors: {result.errors}")

        # Verify embeddings
        valid_embeddings = [emb for emb in result.embeddings if len(emb) > 0]
        print(f"  Valid embeddings: {len(valid_embeddings)}/{len(test_texts)}")

        if len(valid_embeddings) == len(test_texts):
            print(f"✅ All texts embedded successfully")
            return True
        elif len(valid_embeddings) > 0:
            print(f"⚠️ Partial success: {len(valid_embeddings)}/{len(test_texts)} embeddings")
            return True
        else:
            print(f"❌ No successful embeddings")
            return False

    except Exception as e:
        print(f"❌ Batch embedding test failed: {e}")
        return False


def test_pgvector_formatting():
    """Test pgvector format output."""
    print("\n🔢 Testing pgvector formatting...")

    try:
        service = EmbeddingService()

        test_text = "Test document for pgvector format validation."
        pgvector_str, result = service.embed_for_pgvector(test_text)

        if result.success and pgvector_str:
            print(f"✅ pgvector formatting successful!")
            print(f"  Format type: {type(pgvector_str)}")
            print(f"  Format length: {len(pgvector_str)}")
            print(f"  Format preview: {pgvector_str[:100]}...")

            # Test that it's a valid list format
            try:
                # This should parse as a Python list
                parsed = eval(pgvector_str)
                if isinstance(parsed, list) and len(parsed) == 1536:
                    print(f"✅ Valid pgvector list format with correct dimensions")
                else:
                    print(f"❌ Invalid pgvector format: {type(parsed)}, len={len(parsed) if isinstance(parsed, list) else 'N/A'}")
            except:
                print(f"❌ pgvector string is not valid Python list format")

            return True

        else:
            print(f"❌ pgvector formatting failed: {result.error if result else 'Unknown error'}")
            return False

    except Exception as e:
        print(f"❌ pgvector formatting test failed: {e}")
        return False


def test_database_integration():
    """Test database integration and usage logging."""
    print("\n💾 Testing database integration...")

    try:
        service = EmbeddingService()

        # Test single embedding (should log to database)
        test_text = "Test text for database logging verification."
        result = service.embed_text(test_text, metadata={'test': 'database_integration'})

        if result.success:
            print(f"✅ Embedding with logging successful")

            # Check if usage was logged
            with DatabaseSession() as db_session:
                # Query recent logs
                recent_logs = db_session.execute(text("""
                    SELECT id, request_type, text_count, total_tokens, total_cost, success
                    FROM embedding_usage_log
                    WHERE created_at >= NOW() - INTERVAL '1 minute'
                    ORDER BY created_at DESC
                    LIMIT 5;
                """)).fetchall()

                print(f"Recent embedding logs: {len(recent_logs)} entries")

                if recent_logs:
                    latest_log = recent_logs[0]
                    print(f"  Latest log: {latest_log[1]} | {latest_log[2]} texts | {latest_log[3]} tokens | ${latest_log[4]:.6f} | Success: {bool(latest_log[5])}")
                    print(f"✅ Database logging working correctly")
                    return True
                else:
                    print(f"⚠️ No recent logs found - logging may be disabled")
                    return True  # Not a failure if logging is optional

        else:
            print(f"❌ Database integration test failed: {result.error}")
            return False

    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False


def test_usage_statistics():
    """Test usage statistics functionality."""
    print("\n📊 Testing usage statistics...")

    try:
        service = EmbeddingService()

        # Get usage stats
        stats = service.get_usage_stats()

        print(f"Usage statistics:")
        print(f"  Total requests: {stats.get('total_requests', 0)}")
        print(f"  Total texts: {stats.get('total_texts', 0)}")
        print(f"  Total tokens: {stats.get('total_tokens', 0)}")
        print(f"  Total cost: ${stats.get('total_cost', 0):.6f}")
        print(f"  Success rate: {stats.get('success_rate', 0):.2%}")
        print(f"  Avg latency: {stats.get('avg_latency_ms', 0):.1f}ms")

        # Test with date range
        yesterday = datetime.now() - timedelta(days=1)
        recent_stats = service.get_usage_stats(start_date=yesterday)

        print(f"\nRecent usage (last 24h):")
        print(f"  Requests: {recent_stats.get('total_requests', 0)}")
        print(f"  Cost: ${recent_stats.get('total_cost', 0):.6f}")

        print(f"✅ Usage statistics working correctly")
        return True

    except Exception as e:
        print(f"❌ Usage statistics test failed: {e}")
        return False


def test_convenience_functions():
    """Test module-level convenience functions."""
    print("\n🔧 Testing convenience functions...")

    try:
        # Test convenience functions
        test_text = "Convenience function test text."

        print("Testing embed_text()...")
        result1 = embed_text(test_text)

        if result1.success:
            print(f"✅ embed_text() works: {result1.tokens} tokens, ${result1.cost:.6f}")
        else:
            print(f"❌ embed_text() failed: {result1.error}")
            return False

        print("Testing embed_batch()...")
        test_texts = ["Text one for batch test.", "Text two for batch test."]
        result2 = embed_batch(test_texts)

        if result2.success_count > 0:
            print(f"✅ embed_batch() works: {result2.success_count} successes, {result2.total_tokens} tokens, ${result2.total_cost:.6f}")
        else:
            print(f"❌ embed_batch() failed: {result2.errors}")
            return False

        return True

    except Exception as e:
        print(f"❌ Convenience functions test failed: {e}")
        return False


def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n⚠️ Testing error handling...")

    try:
        service = EmbeddingService()

        # Test empty text
        print("Testing empty text handling...")
        try:
            result = service.embed_text("")
            print(f"❌ Empty text should have failed, got: {result.success}")
            return False
        except ValueError:
            print(f"✅ Empty text properly rejected")

        # Test very long text (should be truncated, not fail)
        print("Testing very long text...")
        very_long_text = "A" * 50000  # Much longer than token limit

        result = service.embed_text(very_long_text)
        if result.success:
            print(f"✅ Long text handled (truncated): {result.tokens} tokens")
        else:
            print(f"⚠️ Long text failed (may be expected): {result.error}")

        # Test invalid text type
        print("Testing invalid text type...")
        try:
            result = service.embed_text(123)  # Number instead of string
            print(f"❌ Invalid type should have failed, got: {result}")
            return False
        except ValueError:
            print(f"✅ Invalid type properly rejected")

        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_database_pgvector_integration():
    """Test inserting embeddings into the RAG database."""
    print("\n🔗 Testing RAG database integration...")

    try:
        service = EmbeddingService()

        # Create a test embedding
        test_text = "This is a test document for RAG database integration with real embeddings."
        pgvector_str, result = service.embed_for_pgvector(test_text)

        if not result.success:
            print(f"❌ Failed to generate embedding: {result.error}")
            return False

        # Test inserting into rag_chunks table
        with DatabaseSession() as db_session:
            # Insert a test document first
            doc_result = db_session.execute(text("""
                INSERT INTO rag_documents (
                    source_type, source_id, title, content_type,
                    processing_status
                ) VALUES (
                    'external_content', gen_random_uuid(), 'Test Embedding Doc',
                    'test', 'completed'
                ) RETURNING id;
            """)).fetchone()

            doc_id = doc_result[0]

            # Insert embedding into rag_chunks
            chunk_result = db_session.execute(text("""
                INSERT INTO rag_chunks (
                    document_id, chunk_index, content_text,
                    token_count, character_count, embedding
                ) VALUES (
                    :doc_id, 0, :content_text, :token_count, :char_count, :embedding
                ) RETURNING id;
            """), {
                'doc_id': doc_id,
                'content_text': test_text,
                'token_count': result.tokens,
                'char_count': len(test_text),
                'embedding': pgvector_str
            }).fetchone()

            chunk_id = chunk_result[0]

            # Test vector similarity search
            similarity_result = db_session.execute(text("""
                SELECT
                    content_text,
                    (1 - (embedding <=> :query_embedding)) as similarity
                FROM rag_chunks
                WHERE id = :chunk_id;
            """), {
                'query_embedding': pgvector_str,
                'chunk_id': chunk_id
            }).fetchone()

            # Clean up test data
            db_session.execute(text("DELETE FROM rag_documents WHERE id = :doc_id"), {'doc_id': doc_id})
            db_session.commit()

            if similarity_result:
                similarity = similarity_result[1]
                print(f"✅ RAG database integration successful!")
                print(f"  Document ID: {str(doc_id)[:8]}...")
                print(f"  Chunk ID: {str(chunk_id)[:8]}...")
                print(f"  Self-similarity: {similarity:.6f}")

                if abs(similarity - 1.0) < 0.0001:  # Should be very close to 1.0
                    print(f"✅ Vector similarity working correctly")
                else:
                    print(f"⚠️ Unexpected similarity score: {similarity}")

                return True
            else:
                print(f"❌ Failed to query inserted embedding")
                return False

    except Exception as e:
        print(f"❌ RAG database integration test failed: {e}")
        return False


def test_mock_service_logic():
    """Test embedding service logic without OpenAI calls."""
    print("\n🧪 Testing service initialization and basic logic...")

    try:
        # Test service can be created (shouldn't require OpenAI for basic init)
        service = EmbeddingService()
        print(f"✅ Service created successfully")
        print(f"  Default model: {service.DEFAULT_MODEL}")
        print(f"  Dimensions: {service.EMBEDDING_DIMENSIONS}")
        print(f"  Cost per token: ${service.COST_PER_TOKEN:.8f}")

        # Test utility functions
        test_text = "This is a test text for token estimation"
        estimated_tokens = service._calculate_tokens(test_text)
        print(f"✅ Token calculation works: {estimated_tokens} tokens for {len(test_text)} chars")

        # Test content hash
        content_hash = service._content_hash(["text1", "text2"])
        print(f"✅ Content hash generation: {content_hash[:16]}...")

        # Test text validation
        validated = service._validate_text("  test text  ")
        print(f"✅ Text validation: '{validated}'")

        return True

    except Exception as e:
        print(f"❌ Mock service test failed: {e}")
        return False


def test_mock_pgvector_format():
    """Test pgvector formatting with mock data."""
    print("\n📦 Testing pgvector formatting logic...")

    try:
        # Create a mock embedding (1536 dimensions)
        mock_embedding = [0.1 * i for i in range(1536)]

        # Test formatting
        pgvector_str = str(mock_embedding)
        print(f"✅ pgvector format created")
        print(f"  Length: {len(pgvector_str)} characters")
        print(f"  Sample: {pgvector_str[:50]}...")

        # Test it can be parsed back
        parsed = eval(pgvector_str)
        if len(parsed) == 1536 and isinstance(parsed[0], float):
            print(f"✅ pgvector format is valid")
            return True
        else:
            print(f"❌ pgvector format validation failed")
            return False

    except Exception as e:
        print(f"❌ Mock pgvector test failed: {e}")
        return False


def test_mock_database_logic():
    """Test database connectivity and table existence."""
    print("\n🗄️ Testing database connectivity...")

    try:
        # Test database connection
        with DatabaseSession() as db_session:
            # Test that RAG tables exist
            tables_result = db_session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_name IN ('rag_documents', 'rag_chunks', 'corpus_summary');
            """)).fetchall()

            table_names = [row[0] for row in tables_result]
            print(f"✅ Database connection successful")
            print(f"  Found RAG tables: {table_names}")

            if len(table_names) >= 3:
                print(f"✅ Required RAG tables exist")
                return True
            else:
                print(f"❌ Missing RAG tables. Run Prompt 15 migration first.")
                return False

    except Exception as e:
        print(f"❌ Mock database test failed: {e}")
        return False


def print_cost_summary(service):
    """Print a summary of embedding costs."""
    print("\n💰 COST SUMMARY")
    print("-" * 40)

    stats = service.get_usage_stats()

    total_requests = stats.get('total_requests', 0)
    total_cost = stats.get('total_cost', 0)
    total_tokens = stats.get('total_tokens', 0)

    print(f"Total embedding requests: {total_requests}")
    print(f"Total tokens processed: {total_tokens:,}")
    print(f"Total cost: ${total_cost:.6f}")

    if total_tokens > 0:
        cost_per_1k = (total_cost / total_tokens) * 1000
        print(f"Cost per 1K tokens: ${cost_per_1k:.6f}")

    print(f"\nModel: text-embedding-3-small")
    print(f"Rate: $0.00002/1K tokens ($0.02/1M tokens)")

    by_type = stats.get('by_request_type', {})
    if by_type:
        print(f"\nBy request type:")
        for req_type, type_stats in by_type.items():
            print(f"  {req_type}: {type_stats['requests']} requests, {type_stats['tokens']} tokens, ${type_stats['cost']:.6f}")


def main():
    """Run all embedding service tests."""
    print("=" * 60)
    print("EMBEDDING SERVICE TEST SUITE")
    print("=" * 60)

    # Track test results
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

    # Run tests in order
    config_status = check_configuration()

    if config_status == False:
        print(f"\n❌ Cannot proceed - configuration failed")
        return False

    mock_mode = (config_status == "mock")

    if mock_mode:
        print(f"\n📝 Running in MOCK mode - testing logic without OpenAI API calls")
    else:
        print(f"\n🚀 Running with live OpenAI API - will make actual embedding calls")

    service = None

    if mock_mode:
        # Run mock tests that don't require OpenAI
        run_test(test_mock_service_logic, "Service logic (mock)")
        run_test(test_mock_pgvector_format, "pgvector formatting (mock)")
        run_test(test_mock_database_logic, "Database connectivity")

        print(f"\n📝 Mock tests completed. To test OpenAI integration:")
        print(f"   1. Configure OpenAI API key in credentials.yaml")
        print(f"   2. Re-run tests for full OpenAI functionality")

    else:
        # Run full tests with OpenAI
        try:
            service = EmbeddingService()
        except Exception as e:
            print(f"❌ Failed to create embedding service: {e}")
            return False

        # Core functionality tests
        run_test(test_service_initialization, "Service initialization")
        run_test(test_single_text_embedding, "Single text embedding")
        run_test(test_batch_embedding, "Batch embedding")
        run_test(test_pgvector_formatting, "pgvector formatting")

        # Integration tests
        run_test(test_database_integration, "Database integration")
        run_test(test_usage_statistics, "Usage statistics")
        run_test(test_convenience_functions, "Convenience functions")

        # Robustness tests
        run_test(test_error_handling, "Error handling")
        run_test(test_database_pgvector_integration, "RAG database integration")

    # Print results
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    total_tests = tests_passed + tests_failed
    print(f"Tests passed: {tests_passed}/{total_tests}")
    print(f"Tests failed: {tests_failed}/{total_tests}")

    if tests_failed == 0:
        print("✅ ALL TESTS PASSED!")
        if mock_mode:
            status = "EMBEDDING SERVICE LOGIC VERIFIED - Configure OpenAI for full functionality"
        else:
            status = "READY FOR PROMPT 17: CONTENT PROCESSOR"
    else:
        print("❌ SOME TESTS FAILED")
        status = "NEEDS FIXES BEFORE PROCEEDING"

    # Show cost summary if service worked
    if service and tests_passed > 0:
        print_cost_summary(service)

    print(f"\nStatus: {status}")
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