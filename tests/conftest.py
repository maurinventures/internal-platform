"""
Pytest Configuration and Fixtures for API Tests (Prompt 24)

Provides test fixtures, mocks, and configuration for testing Flask API endpoints
without requiring real AI calls or external services.
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

# Add the project root to Python path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies before importing the app
@pytest.fixture(scope="session", autouse=True)
def mock_external_dependencies():
    """Mock external dependencies at session level."""

    # Mock database session
    with patch('scripts.db.DatabaseSession') as mock_db_session:
        from datetime import datetime
        mock_db = MagicMock()

        # Create a proper user mock that will be returned by the query chain
        mock_user_instance = Mock()
        mock_user_instance.id = '550e8400-e29b-41d4-a716-446655440000'
        mock_user_instance.email = 'test@example.com'
        mock_user_instance.name = 'Test User'
        mock_user_instance.is_active = True
        mock_user_instance.email_verified = True
        mock_user_instance.totp_enabled = False
        mock_user_instance.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_user_instance.last_login = datetime(2024, 1, 2, 10, 0, 0)
        mock_user_instance.check_password.return_value = True

        # Configure the query chain to return our mock user
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user_instance

        mock_db_session.return_value.__enter__ = Mock(return_value=mock_db)
        mock_db_session.return_value.__exit__ = Mock(return_value=None)

        # Mock AI service calls
        with patch('web.services.ai_service.AIService.generate_script_with_ai') as mock_ai_service:
            mock_ai_service.return_value = {
                'message': 'Mock AI response for testing',
                'clips': [],
                'has_script': False
            }

            # Mock usage limits service
            with patch('web.services.usage_limits_service.UsageLimitsService') as mock_usage_limits:
                mock_usage_limits.check_context_limit.return_value = {'allowed': True}
                mock_usage_limits.check_daily_user_limit.return_value = {'allowed': True, 'warning': False}
                mock_usage_limits.calculate_cost.return_value = (0.001, 0.002, 0.003)

                yield


@pytest.fixture
def app():
    """Create application for testing."""

    # Set environment to testing
    os.environ['TESTING'] = 'True'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'

    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()

    # Import the Flask app
    from web.app import app

    # Configure the app for testing
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'DATABASE_URL': f'sqlite:///{db_path}',
    })

    with app.app_context():
        yield app

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def mock_user_session():
    """Mock user session data."""
    return {
        'user_id': '550e8400-e29b-41d4-a716-446655440000',
        'user_email': 'test@example.com',
        'user_name': 'Test User'
    }


@pytest.fixture
def auth_headers():
    """Common headers for authenticated requests."""
    return {
        'Content-Type': 'application/json',
    }


@pytest.fixture
def mock_ai_response():
    """Mock AI response data."""
    return {
        'message': 'This is a mock AI response for testing purposes',
        'clips': [
            {
                'id': 'clip-1',
                'start_time': 10.5,
                'end_time': 25.0,
                'text': 'Mock clip content for testing',
                'video_id': 'test-video-123'
            }
        ],
        'has_script': True
    }


@pytest.fixture
def mock_models_data():
    """Mock AI models data."""
    return [
        {
            'id': 'claude-sonnet',
            'name': 'Claude Sonnet 4',
            'description': 'Balanced performance and capability',
            'provider': 'anthropic'
        },
        {
            'id': 'gpt-4o',
            'name': 'GPT-4o',
            'description': 'OpenAI\'s most capable model',
            'provider': 'openai'
        }
    ]


@pytest.fixture
def mock_library_content():
    """Mock library content data."""
    return {
        'content': [
            {
                'id': 'content-1',
                'title': 'Test Video Content',
                'description': 'A test video for API testing',
                'content_type': 'video',
                'file_name': 'test-video.mp4',
                'created_at': '2024-01-01T12:00:00Z'
            },
            {
                'id': 'content-2',
                'title': 'Test Audio Content',
                'description': 'A test audio for API testing',
                'content_type': 'audio',
                'file_name': 'test-audio.mp3',
                'created_at': '2024-01-02T12:00:00Z'
            }
        ],
        'total': 2,
        'page': 1,
        'per_page': 20
    }


@pytest.fixture
def mock_user_data():
    """Mock user data for authentication tests."""
    return {
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'email': 'test@example.com',
        'name': 'Test User',
        'password_hash': 'hashed_password_for_testing'
    }


@pytest.fixture(autouse=True)
def mock_database_operations():
    """Mock database operations to avoid real database calls."""

    with patch('scripts.db.User') as mock_user_model, \
         patch('scripts.db.AILog') as mock_ai_log_model, \
         patch('scripts.db.Conversation') as mock_conversation_model, \
         patch('scripts.db.GenerationJob') as mock_generation_job_model:

        # Mock User query operations
        from datetime import datetime
        mock_user_instance = Mock()
        mock_user_instance.id = '550e8400-e29b-41d4-a716-446655440000'
        mock_user_instance.email = 'test@example.com'
        mock_user_instance.name = 'Test User'
        mock_user_instance.is_active = True
        mock_user_instance.email_verified = True
        mock_user_instance.totp_enabled = False
        mock_user_instance.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_user_instance.last_login = datetime(2024, 1, 2, 10, 0, 0)
        mock_user_instance.check_password.return_value = True

        mock_user_model.query.filter.return_value.first.return_value = mock_user_instance

        yield {
            'user_model': mock_user_model,
            'ai_log_model': mock_ai_log_model,
            'conversation_model': mock_conversation_model,
            'generation_job_model': mock_generation_job_model,
            'user_instance': mock_user_instance
        }


@pytest.fixture
def authenticated_session(client, mock_user_session):
    """Helper to create an authenticated session."""
    with client.session_transaction() as sess:
        for key, value in mock_user_session.items():
            sess[key] = value
    return client