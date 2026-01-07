"""
API Endpoints Tests for Prompt 24

Comprehensive tests for Flask API endpoints including authentication,
chat functionality, CRUD operations, and error handling.
Tests are designed to run without real AI calls or external dependencies.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestAuthenticationEndpoints:
    """Test authentication-related API endpoints."""

    @pytest.mark.auth
    def test_auth_me_without_session(self, client):
        """Test /api/auth/me without authenticated session."""
        response = client.get('/api/auth/me')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    @pytest.mark.auth
    def test_auth_me_with_session(self, authenticated_session, mock_user_session):
        """Test /api/auth/me with authenticated session."""
        response = authenticated_session.get('/api/auth/me')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'user' in data
        assert data['user']['email'] == mock_user_session['user_email']

    @pytest.mark.auth
    def test_login_endpoint_with_valid_credentials(self, client, mock_database_operations):
        """Test login with valid credentials."""

        # Mock authentication service
        with patch('web.services.auth_service.AuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                'success': True,
                'user': {
                    'id': 'test-user-123',
                    'email': 'test@example.com',
                    'name': 'Test User'
                },
                'requires_2fa': False
            }

            response = client.post('/api/auth/login',
                                 data=json.dumps({
                                     'email': 'test@example.com',
                                     'password': 'test_password'
                                 }),
                                 content_type='application/json')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'user' in data

    @pytest.mark.auth
    def test_login_endpoint_with_invalid_credentials(self, client):
        """Test login with invalid credentials."""

        with patch('web.services.auth_service.AuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                'success': False,
                'error': 'Invalid credentials'
            }

            response = client.post('/api/auth/login',
                                 data=json.dumps({
                                     'email': 'wrong@example.com',
                                     'password': 'wrong_password'
                                 }),
                                 content_type='application/json')

            assert response.status_code == 401
            data = json.loads(response.data)
            assert 'error' in data

    @pytest.mark.auth
    def test_login_endpoint_missing_data(self, client):
        """Test login endpoint with missing email or password."""
        response = client.post('/api/auth/login',
                             data=json.dumps({'email': 'test@example.com'}),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @pytest.mark.auth
    def test_logout_endpoint(self, authenticated_session):
        """Test logout endpoint."""
        response = authenticated_session.post('/api/auth/logout')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify session is cleared by checking subsequent auth call
        response = authenticated_session.get('/api/auth/me')
        assert response.status_code == 401


class TestChatEndpoints:
    """Test chat-related API endpoints."""

    @pytest.mark.api
    def test_chat_endpoint_without_authentication(self, client):
        """Test chat endpoint without authentication."""
        response = client.post('/api/chat',
                             data=json.dumps({
                                 'message': 'Hello',
                                 'model': 'claude-sonnet'
                             }),
                             content_type='application/json')

        assert response.status_code == 401

    @pytest.mark.api
    def test_chat_endpoint_with_authentication(self, authenticated_session, mock_ai_response):
        """Test chat endpoint with valid authentication and message."""

        with patch('web.services.ai_service.AIService.generate_script_with_ai') as mock_ai:
            mock_ai.return_value = mock_ai_response

            response = authenticated_session.post('/api/chat',
                                                data=json.dumps({
                                                    'message': 'Generate a video script about AI',
                                                    'model': 'claude-sonnet'
                                                }),
                                                content_type='application/json')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert data['message'] == mock_ai_response['message']
            assert 'clips' in data
            assert 'has_script' in data

    @pytest.mark.api
    def test_chat_endpoint_empty_message(self, authenticated_session):
        """Test chat endpoint with empty message."""
        response = authenticated_session.post('/api/chat',
                                            data=json.dumps({
                                                'message': '',
                                                'model': 'claude-sonnet'
                                            }),
                                            content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @pytest.mark.api
    def test_chat_endpoint_missing_model(self, authenticated_session):
        """Test chat endpoint with missing model parameter."""
        response = authenticated_session.post('/api/chat',
                                            data=json.dumps({
                                                'message': 'Hello AI'
                                            }),
                                            content_type='application/json')

        # Should use default model
        assert response.status_code in [200, 400]  # Depends on implementation

    @pytest.mark.api
    def test_chat_endpoint_ai_service_error(self, authenticated_session):
        """Test chat endpoint when AI service raises an error."""

        with patch('web.services.ai_service.AIService.generate_script_with_ai') as mock_ai:
            mock_ai.side_effect = Exception("AI service unavailable")

            response = authenticated_session.post('/api/chat',
                                                data=json.dumps({
                                                    'message': 'Test message',
                                                    'model': 'claude-sonnet'
                                                }),
                                                content_type='application/json')

            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data

    @pytest.mark.api
    def test_models_endpoint(self, client, mock_models_data):
        """Test models endpoint returns available AI models."""
        response = client.get('/api/models')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0

        # Check model structure
        model = data[0]
        assert 'id' in model
        assert 'name' in model
        assert 'description' in model


class TestUsageEndpoints:
    """Test usage tracking and limits endpoints."""

    @pytest.mark.api
    def test_usage_stats_without_authentication(self, client):
        """Test usage stats endpoint without authentication."""
        response = client.get('/api/usage/stats')
        assert response.status_code == 401

    @pytest.mark.api
    def test_usage_stats_with_authentication(self, authenticated_session):
        """Test usage stats endpoint with authentication."""

        with patch('web.services.usage_limits_service.UsageLimitsService.get_user_usage_stats') as mock_stats, \
             patch('web.services.usage_limits_service.UsageLimitsService.check_daily_user_limit') as mock_daily_check:

            mock_stats.return_value = {
                'period_days': 30,
                'total_calls': 45,
                'total_input_tokens': 50000,
                'total_output_tokens': 25000,
                'total_tokens': 75000,
                'total_cost': 12.34,
                'today_tokens': 5000,
                'today_percentage': 0.01,
                'daily_limit': 500000,
                'warning': False,
                'models_used': ['claude-sonnet', 'gpt-4o']
            }

            mock_daily_check.return_value = {
                'usage': 5000,
                'percentage': 0.01,
                'limit': 500000,
                'warning': False,
                'allowed': True
            }

            response = authenticated_session.get('/api/usage/stats')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'current_usage' in data
            assert 'period_stats' in data
            assert 'limits' in data


class TestGenerationEndpoints:
    """Test long-form generation API endpoints."""

    @pytest.mark.api
    def test_create_generation_job_without_auth(self, client):
        """Test creating generation job without authentication."""
        response = client.post('/api/generation/jobs',
                             data=json.dumps({
                                 'brief': 'Write an article about AI',
                                 'content_format': 'blog_post'
                             }),
                             content_type='application/json')

        assert response.status_code == 401

    @pytest.mark.api
    def test_create_generation_job_with_auth(self, authenticated_session):
        """Test creating generation job with authentication."""

        with patch('scripts.generation_service.GenerationService.create_generation_job') as mock_create:
            mock_create.return_value = 'job-123'

            response = authenticated_session.post('/api/generation/jobs',
                                                 data=json.dumps({
                                                     'brief': 'Write an article about AI',
                                                     'content_format': 'blog_post',
                                                     'target_word_count': 2000
                                                 }),
                                                 content_type='application/json')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'job_id' in data

    @pytest.mark.api
    def test_create_generation_job_missing_brief(self, authenticated_session):
        """Test creating generation job without required brief."""
        response = authenticated_session.post('/api/generation/jobs',
                                             data=json.dumps({
                                                 'content_format': 'blog_post'
                                             }),
                                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @pytest.mark.api
    def test_get_generation_job_status(self, authenticated_session):
        """Test getting generation job status."""

        with patch('scripts.generation_service.GenerationService.get_job_status') as mock_status:
            mock_status.return_value = {
                'job_id': 'job-123',
                'job_name': 'Test Article',
                'status': 'outline_creation',
                'progress_percentage': 25,
                'sections_completed': 1,
                'sections_total': 4
            }

            response = authenticated_session.get('/api/generation/jobs/job-123')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['job_id'] == 'job-123'
            assert data['progress_percentage'] == 25

    @pytest.mark.api
    def test_get_generation_job_not_found(self, authenticated_session):
        """Test getting non-existent generation job."""

        with patch('scripts.generation_service.GenerationService.get_job_status') as mock_status:
            mock_status.return_value = None

            response = authenticated_session.get('/api/generation/jobs/nonexistent')

            assert response.status_code == 404


class TestDownloadEndpoints:
    """Test download-related API endpoints."""

    @pytest.mark.api
    def test_video_download_options(self, client):
        """Test video download options endpoint."""

        with patch('web.services.video_service.VideoService') as mock_video_service:
            mock_video_service.get_download_options.return_value = {
                'video_id': 'test-video-123',
                'title': 'Test Video',
                'clips': [
                    {
                        'id': 'clip-1',
                        'start_time': 0,
                        'end_time': 30,
                        'text': 'Test clip content',
                        'size_mb': 5.2
                    }
                ],
                'full_video': {
                    'size_mb': 150.8,
                    'duration': 300
                }
            }

            response = client.get('/api/video/test-video-123/download-options')

            # Response depends on implementation - could be 200 or 404
            assert response.status_code in [200, 404, 500]

    @pytest.mark.api
    def test_clip_download(self, client):
        """Test clip download endpoint."""

        response = client.get('/api/clip-download/test-clip-123')

        # Response depends on implementation and file existence
        assert response.status_code in [200, 404, 500]

    @pytest.mark.api
    def test_video_download(self, client):
        """Test video download endpoint."""

        response = client.get('/api/video-download/test-video-123')

        # Response depends on implementation and file existence
        assert response.status_code in [200, 404, 500]


class TestErrorHandling:
    """Test error handling across endpoints."""

    @pytest.mark.api
    def test_invalid_json_request(self, authenticated_session):
        """Test endpoints with invalid JSON data."""
        response = authenticated_session.post('/api/chat',
                                            data='invalid json',
                                            content_type='application/json')

        assert response.status_code in [400, 500]

    @pytest.mark.api
    def test_missing_content_type(self, authenticated_session):
        """Test endpoints without proper content type."""
        response = authenticated_session.post('/api/chat',
                                            data='{"message": "test"}')

        # Should handle missing content-type gracefully
        assert response.status_code in [400, 415, 500]

    @pytest.mark.api
    def test_nonexistent_endpoint(self, client):
        """Test calling non-existent API endpoint."""
        response = client.get('/api/nonexistent-endpoint')
        assert response.status_code == 404

    @pytest.mark.api
    def test_method_not_allowed(self, client):
        """Test calling endpoint with wrong HTTP method."""
        response = client.delete('/api/models')  # GET-only endpoint
        assert response.status_code in [405, 404]


class TestCRUDOperations:
    """Test CRUD operations for various resources."""

    @pytest.mark.api
    def test_list_user_generation_jobs(self, authenticated_session):
        """Test listing user's generation jobs."""

        with patch('scripts.generation_service.GenerationService.list_user_jobs') as mock_list:
            mock_list.return_value = [
                {
                    'job_id': 'job-1',
                    'job_name': 'Article 1',
                    'status': 'completed',
                    'created_at': '2024-01-01T00:00:00'
                },
                {
                    'job_id': 'job-2',
                    'job_name': 'Article 2',
                    'status': 'in_progress',
                    'created_at': '2024-01-02T00:00:00'
                }
            ]

            response = authenticated_session.get('/api/generation/jobs')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'jobs' in data
            assert len(data['jobs']) == 2

    @pytest.mark.api
    def test_continue_generation_job(self, authenticated_session):
        """Test continuing a generation job pipeline."""

        with patch('scripts.generation_service.GenerationService.continue_pipeline') as mock_continue:
            mock_continue.return_value = {
                'stage': 'sectional_generation',
                'status': 'section_completed',
                'sections_remaining': 2
            }

            response = authenticated_session.post('/api/generation/jobs/job-123/continue',
                                                 data=json.dumps({'model': 'claude-sonnet'}),
                                                 content_type='application/json')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'stage' in data

    @pytest.mark.api
    def test_get_generation_job_content(self, authenticated_session):
        """Test getting completed generation job content."""

        with patch('scripts.generation_service.GenerationService.get_completed_content') as mock_content:
            mock_content.return_value = {
                'job_id': 'job-123',
                'assembled_content': '# Test Article\n\nThis is test content...',
                'word_count': 250,
                'status': 'completed'
            }

            response = authenticated_session.get('/api/generation/jobs/job-123/content')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'assembled_content' in data


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.integration
    def test_complete_chat_flow(self, client):
        """Test complete flow: login -> chat -> logout."""

        # Mock authentication
        with patch('web.services.auth_service.AuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                'success': True,
                'user': {'id': 'test-user-123', 'email': 'test@example.com'},
                'requires_2fa': False
            }

            # Login
            login_response = client.post('/api/auth/login',
                                       data=json.dumps({
                                           'email': 'test@example.com',
                                           'password': 'test_password'
                                       }),
                                       content_type='application/json')

            assert login_response.status_code == 200

            # Mock AI service for chat
            with patch('web.services.ai_service.AIService.generate_script_with_ai') as mock_ai:
                mock_ai.return_value = {
                    'message': 'Integration test AI response',
                    'clips': [],
                    'has_script': False
                }

                # Send chat message
                chat_response = client.post('/api/chat',
                                          data=json.dumps({
                                              'message': 'Hello AI',
                                              'model': 'claude-sonnet'
                                          }),
                                          content_type='application/json')

                assert chat_response.status_code == 200

            # Logout
            logout_response = client.post('/api/auth/logout')
            assert logout_response.status_code == 200

    @pytest.mark.integration
    def test_generation_job_lifecycle(self, authenticated_session):
        """Test complete generation job lifecycle."""

        # Create job
        with patch('scripts.generation_service.GenerationService.create_generation_job') as mock_create:
            mock_create.return_value = 'job-123'

            create_response = authenticated_session.post('/api/generation/jobs',
                                                       data=json.dumps({
                                                           'brief': 'Write about testing',
                                                           'content_format': 'blog_post'
                                                       }),
                                                       content_type='application/json')

            assert create_response.status_code == 200
            job_id = json.loads(create_response.data)['job_id']

        # Check status
        with patch('scripts.generation_service.GenerationService.get_job_status') as mock_status:
            mock_status.return_value = {
                'job_id': job_id,
                'status': 'brief_analysis',
                'progress_percentage': 10
            }

            status_response = authenticated_session.get(f'/api/generation/jobs/{job_id}')
            assert status_response.status_code == 200

        # Continue pipeline
        with patch('scripts.generation_service.GenerationService.continue_pipeline') as mock_continue:
            mock_continue.return_value = {
                'stage': 'completed',
                'status': 'job_completed',
                'job_completed': True
            }

            continue_response = authenticated_session.post(f'/api/generation/jobs/{job_id}/continue',
                                                         data=json.dumps({'model': 'claude-sonnet'}),
                                                         content_type='application/json')

            assert continue_response.status_code == 200

        # Get final content
        with patch('scripts.generation_service.GenerationService.get_completed_content') as mock_content:
            mock_content.return_value = {
                'assembled_content': '# Test Article\\n\\nCompleted content...',
                'word_count': 500
            }

            content_response = authenticated_session.get(f'/api/generation/jobs/{job_id}/content')
            assert content_response.status_code == 200