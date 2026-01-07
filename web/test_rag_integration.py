#!/usr/bin/env python3
"""
Test RAG Integration for Prompt 18

Basic validation of RAG integration functionality without requiring
a fully populated RAG database. Tests service integration, API compatibility,
and fallback mechanisms.
"""

import sys
import os
from datetime import datetime
import traceback

# Add paths for imports
sys.path.append('/Users/josephs./internal-platform/web')
sys.path.append('/Users/josephs./internal-platform')
sys.path.append('/Users/josephs./internal-platform/scripts')

def test_rag_service_integration():
    """Test RAG service can be imported and initialized."""
    print("🧪 Testing RAG service integration...")

    try:
        from services.rag_service import RAGService, RAGChunkResult, RAGSearchResult

        # Test service initialization
        rag_service = RAGService()

        print("✅ RAG service imported and initialized successfully")
        print(f"   Service type: {type(rag_service)}")
        print(f"   Has search method: {hasattr(rag_service, 'search_with_rag')}")
        print(f"   Has context assembly: {hasattr(rag_service, 'assemble_context_from_chunks')}")
        print(f"   Has fallback method: {hasattr(rag_service, 'search_with_fallback')}")

        return True

    except ImportError as e:
        print(f"❌ RAG service import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ RAG service initialization failed: {e}")
        return False


def test_database_integration():
    """Test database connectivity and RAG table existence."""
    print("\n🗄️ Testing database integration...")

    try:
        from scripts.db import DatabaseSession
        from sqlalchemy import text

        with DatabaseSession() as session:
            # Check RAG tables exist
            tables_result = session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('rag_documents', 'rag_sections', 'rag_chunks', 'corpus_summary')
            """)).fetchall()

            table_names = [row[0] for row in tables_result]
            print(f"✅ Database connection successful")
            print(f"   Found RAG tables: {table_names}")

            if len(table_names) >= 4:
                print("✅ All required RAG tables exist")

                # Check if hybrid_search function exists
                function_result = session.execute(text("""
                    SELECT proname
                    FROM pg_proc
                    WHERE proname = 'hybrid_search'
                """)).fetchall()

                if function_result:
                    print("✅ hybrid_search function exists")
                else:
                    print("⚠️  hybrid_search function not found")

                # Check current content counts
                doc_count = session.execute(text("SELECT COUNT(*) FROM rag_documents")).scalar()
                section_count = session.execute(text("SELECT COUNT(*) FROM rag_sections")).scalar()
                chunk_count = session.execute(text("SELECT COUNT(*) FROM rag_chunks")).scalar()

                print(f"   Current RAG content:")
                print(f"     Documents: {doc_count}")
                print(f"     Sections: {section_count}")
                print(f"     Chunks: {chunk_count}")

                return True
            else:
                print(f"❌ Missing RAG tables. Found: {table_names}")
                return False

    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False


def test_ai_service_integration():
    """Test AI service RAG parameter integration."""
    print("\n🤖 Testing AI service integration...")

    try:
        from services.ai_service import AIService
        import inspect

        # Check generate_script_with_ai signature
        script_sig = inspect.signature(AIService.generate_script_with_ai)
        if 'use_rag' in script_sig.parameters:
            print("✅ generate_script_with_ai has use_rag parameter")
        else:
            print("❌ generate_script_with_ai missing use_rag parameter")
            return False

        # Check generate_copy_with_ai signature
        copy_sig = inspect.signature(AIService.generate_copy_with_ai)
        if 'use_rag' in copy_sig.parameters:
            print("✅ generate_copy_with_ai has use_rag parameter")
        else:
            print("❌ generate_copy_with_ai missing use_rag parameter")
            return False

        # Check log_ai_call signature for RAG metrics
        log_sig = inspect.signature(AIService.log_ai_call)
        rag_params = ['search_method', 'rag_chunks_used', 'rag_embedding_cost']
        missing_params = [p for p in rag_params if p not in log_sig.parameters]

        if not missing_params:
            print("✅ log_ai_call has all RAG metric parameters")
        else:
            print(f"❌ log_ai_call missing RAG parameters: {missing_params}")
            return False

        print("✅ AI service integration validated")
        return True

    except ImportError as e:
        print(f"❌ AI service import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ AI service integration test failed: {e}")
        return False


def test_transcript_service_integration():
    """Test transcript service RAG parameter integration."""
    print("\n📄 Testing transcript service integration...")

    try:
        from services.transcript_service import TranscriptService
        import inspect

        # Check search_for_context signature
        search_sig = inspect.signature(TranscriptService.search_for_context)
        if 'use_rag' in search_sig.parameters:
            print("✅ search_for_context has use_rag parameter")

            # Test default value
            default_value = search_sig.parameters['use_rag'].default
            print(f"   use_rag default value: {default_value}")

            return True
        else:
            print("❌ search_for_context missing use_rag parameter")
            return False

    except ImportError as e:
        print(f"❌ Transcript service import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Transcript service integration test failed: {e}")
        return False


def test_database_schema_updates():
    """Test that AILog model has RAG fields."""
    print("\n🗃️ Testing database schema updates...")

    try:
        from scripts.db import AILog

        # Check RAG-specific columns exist in model
        rag_fields = [
            'search_method', 'rag_chunks_used', 'rag_similarity_scores',
            'rag_embedding_cost', 'rag_search_time_ms', 'context_compression_ratio',
            'estimated_cost_savings', 'rag_fallback_reason'
        ]

        missing_fields = []
        for field in rag_fields:
            if not hasattr(AILog, field):
                missing_fields.append(field)

        if not missing_fields:
            print("✅ AILog model has all RAG fields")
            print(f"   RAG fields verified: {len(rag_fields)}")
            return True
        else:
            print(f"❌ AILog model missing RAG fields: {missing_fields}")
            return False

    except ImportError as e:
        print(f"❌ Database model import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False


def test_embedding_service_availability():
    """Test embedding service is available for RAG."""
    print("\n🔢 Testing embedding service availability...")

    try:
        from scripts.embedding_service import EmbeddingService

        # Test service initialization
        embedding_service = EmbeddingService()
        print("✅ EmbeddingService imported and initialized")
        print(f"   Default model: {embedding_service.DEFAULT_MODEL}")
        print(f"   Dimensions: {embedding_service.EMBEDDING_DIMENSIONS}")

        # Test method availability
        methods = ['embed_text', 'embed_for_pgvector']
        for method in methods:
            if hasattr(embedding_service, method):
                print(f"✅ {method} method available")
            else:
                print(f"❌ {method} method missing")
                return False

        return True

    except ImportError as e:
        print(f"❌ EmbeddingService import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ EmbeddingService test failed: {e}")
        return False


def test_fallback_functionality():
    """Test RAG fallback mechanisms work."""
    print("\n🔄 Testing fallback functionality...")

    try:
        # Test RAG service fallback
        from services.rag_service import RAGService

        rag_service = RAGService()

        # Test search with fallback method
        if hasattr(rag_service, 'search_with_fallback'):
            print("✅ RAG service has fallback method")

            # Test the method signature
            import inspect
            sig = inspect.signature(rag_service.search_with_fallback)
            expected_params = ['query', 'limit', 'similarity_threshold']

            for param in expected_params:
                if param in sig.parameters:
                    print(f"✅ search_with_fallback has {param} parameter")
                else:
                    print(f"❌ search_with_fallback missing {param} parameter")
                    return False

            return True
        else:
            print("❌ RAG service missing fallback method")
            return False

    except Exception as e:
        print(f"❌ Fallback functionality test failed: {e}")
        return False


def run_integration_test_suite():
    """Run the complete RAG integration test suite."""
    print("=" * 70)
    print("RAG INTEGRATION TEST SUITE - Prompt 18")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    tests = [
        ("RAG Service Integration", test_rag_service_integration),
        ("Database Integration", test_database_integration),
        ("AI Service Integration", test_ai_service_integration),
        ("Transcript Service Integration", test_transcript_service_integration),
        ("Database Schema Updates", test_database_schema_updates),
        ("Embedding Service Availability", test_embedding_service_availability),
        ("Fallback Functionality", test_fallback_functionality),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            traceback.print_exc()
            failed += 1

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    total = passed + failed
    print(f"Tests run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")

    if failed == 0:
        status = "✅ ALL TESTS PASSED - RAG INTEGRATION READY"
    elif passed > failed:
        status = "⚠️  MOSTLY WORKING - Minor issues to resolve"
    else:
        status = "❌ INTEGRATION ISSUES - Requires fixes"

    print(f"\nStatus: {status}")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    try:
        success = run_integration_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)