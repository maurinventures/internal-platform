"""
Smoke Tests for Production Health Checks (Prompt 26)

Basic tests to verify the application is working correctly after deployment.
These tests run against the live production environment to ensure critical
functionality is operational.
"""

import os
import sys
import time
import json
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin


class SmokeTestRunner:
    """
    Smoke test runner for production health checks.

    Tests critical user flows and API endpoints to ensure the application
    is functioning correctly after deployment.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the smoke test runner.

        Args:
            base_url: Base URL of the application (e.g., https://maurinventuresinternal.com)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
        self.test_results: List[Dict[str, Any]] = []

    def log_result(self, test_name: str, success: bool, message: str,
                   response_time: Optional[float] = None, status_code: Optional[int] = None):
        """Log test result for reporting."""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'response_time': response_time,
            'status_code': status_code,
            'timestamp': time.time()
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        timing = f" ({response_time:.2f}s)" if response_time else ""
        code = f" [{status_code}]" if status_code else ""
        print(f"{status}: {test_name}{timing}{code} - {message}")

    def test_homepage_loads(self) -> bool:
        """Test that the homepage loads successfully."""
        test_name = "Homepage Load"
        start_time = time.time()

        try:
            response = self.session.get(self.base_url)
            response_time = time.time() - start_time

            if response.status_code == 200:
                if 'html' in response.headers.get('content-type', '').lower():
                    self.log_result(test_name, True, "Homepage loaded successfully",
                                  response_time, response.status_code)
                    return True
                else:
                    self.log_result(test_name, False, "Homepage returned non-HTML content",
                                  response_time, response.status_code)
                    return False
            else:
                self.log_result(test_name, False, f"Homepage returned error status",
                              response_time, response.status_code)
                return False

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            self.log_result(test_name, False, f"Request failed: {str(e)}", response_time)
            return False

    def test_api_health(self) -> bool:
        """Test that the API health endpoint is responding."""
        test_name = "API Health Check"
        start_time = time.time()

        try:
            url = urljoin(self.base_url, '/api/health')
            response = self.session.get(url)
            response_time = time.time() - start_time

            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        self.log_result(test_name, True, "API health check passed",
                                      response_time, response.status_code)
                        return True
                    else:
                        self.log_result(test_name, False, f"API reports unhealthy status: {data}",
                                      response_time, response.status_code)
                        return False
                except json.JSONDecodeError:
                    self.log_result(test_name, False, "API health endpoint returned invalid JSON",
                                  response_time, response.status_code)
                    return False
            else:
                self.log_result(test_name, False, "API health endpoint returned error",
                              response_time, response.status_code)
                return False

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            self.log_result(test_name, False, f"API health request failed: {str(e)}", response_time)
            return False

    def test_auth_endpoint_reachable(self) -> bool:
        """Test that auth endpoints are reachable (should return 401 for unauthenticated requests)."""
        test_name = "Auth Endpoint Reachable"
        start_time = time.time()

        try:
            url = urljoin(self.base_url, '/api/auth/me')
            response = self.session.get(url)
            response_time = time.time() - start_time

            # We expect 401 for unauthenticated requests
            if response.status_code == 401:
                self.log_result(test_name, True, "Auth endpoint responding correctly (401 for unauthenticated)",
                              response_time, response.status_code)
                return True
            else:
                self.log_result(test_name, False, f"Auth endpoint returned unexpected status",
                              response_time, response.status_code)
                return False

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            self.log_result(test_name, False, f"Auth endpoint request failed: {str(e)}", response_time)
            return False

    def test_models_endpoint(self) -> bool:
        """Test that the models endpoint is reachable."""
        test_name = "Models Endpoint"
        start_time = time.time()

        try:
            url = urljoin(self.base_url, '/api/models')
            response = self.session.get(url)
            response_time = time.time() - start_time

            if response.status_code in [200, 401]:  # 200 if public, 401 if auth required
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            self.log_result(test_name, True, f"Models endpoint returned {len(data)} models",
                                          response_time, response.status_code)
                            return True
                        else:
                            self.log_result(test_name, False, "Models endpoint returned empty or invalid data",
                                          response_time, response.status_code)
                            return False
                    except json.JSONDecodeError:
                        self.log_result(test_name, False, "Models endpoint returned invalid JSON",
                                      response_time, response.status_code)
                        return False
                else:  # 401 - auth required
                    self.log_result(test_name, True, "Models endpoint requires authentication (as expected)",
                                  response_time, response.status_code)
                    return True
            else:
                self.log_result(test_name, False, "Models endpoint returned error status",
                              response_time, response.status_code)
                return False

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            self.log_result(test_name, False, f"Models endpoint request failed: {str(e)}", response_time)
            return False

    def test_static_assets(self) -> bool:
        """Test that static assets (CSS, JS) are loading."""
        test_name = "Static Assets"

        # Test common static file paths
        static_paths = [
            '/static/css/main.css',
            '/static/js/main.js',
            '/favicon.ico'
        ]

        success_count = 0
        total_tests = len(static_paths)

        for path in static_paths:
            start_time = time.time()
            try:
                url = urljoin(self.base_url, path)
                response = self.session.head(url)  # Use HEAD to avoid downloading large files
                response_time = time.time() - start_time

                if response.status_code == 200:
                    success_count += 1
                    print(f"  ✓ {path} ({response_time:.2f}s) [{response.status_code}]")
                else:
                    print(f"  ✗ {path} ({response_time:.2f}s) [{response.status_code}] - Not found")

            except requests.exceptions.RequestException as e:
                response_time = time.time() - start_time
                print(f"  ✗ {path} ({response_time:.2f}s) - Request failed: {str(e)}")

        # Consider success if at least one static asset loads (some may not exist)
        if success_count > 0:
            self.log_result(test_name, True, f"{success_count}/{total_tests} static assets loaded")
            return True
        else:
            self.log_result(test_name, False, "No static assets could be loaded")
            return False

    def test_database_connectivity(self) -> bool:
        """Test database connectivity through a simple API call."""
        test_name = "Database Connectivity"
        start_time = time.time()

        try:
            # Use a simple endpoint that requires database access
            url = urljoin(self.base_url, '/api/conversations')
            response = self.session.get(url)
            response_time = time.time() - start_time

            # We expect either 200 (if public) or 401 (if auth required)
            # Database errors typically return 500
            if response.status_code in [200, 401]:
                self.log_result(test_name, True, "Database appears to be accessible",
                              response_time, response.status_code)
                return True
            elif response.status_code == 500:
                self.log_result(test_name, False, "Possible database connectivity issue",
                              response_time, response.status_code)
                return False
            else:
                self.log_result(test_name, True, "Endpoint reachable (database likely accessible)",
                              response_time, response.status_code)
                return True

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            self.log_result(test_name, False, f"Database connectivity test failed: {str(e)}", response_time)
            return False

    def test_login_form_loads(self) -> bool:
        """Test that the login form loads correctly."""
        test_name = "Login Form Load"
        start_time = time.time()

        try:
            url = urljoin(self.base_url, '/login')
            response = self.session.get(url)
            response_time = time.time() - start_time

            if response.status_code == 200:
                # Check for common login form elements
                content = response.text.lower()
                has_form_elements = (
                    'email' in content and
                    'password' in content and
                    ('form' in content or 'login' in content)
                )

                if has_form_elements:
                    self.log_result(test_name, True, "Login form loaded with expected elements",
                                  response_time, response.status_code)
                    return True
                else:
                    self.log_result(test_name, False, "Login form missing expected elements",
                                  response_time, response.status_code)
                    return False
            else:
                # Some apps redirect to login, which might return 302/redirects
                if response.status_code in [302, 301]:
                    self.log_result(test_name, True, "Login endpoint returns redirect (normal behavior)",
                                  response_time, response.status_code)
                    return True
                else:
                    self.log_result(test_name, False, "Login form page returned error",
                                  response_time, response.status_code)
                    return False

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            self.log_result(test_name, False, f"Login form request failed: {str(e)}", response_time)
            return False

    def run_all_smoke_tests(self) -> Dict[str, Any]:
        """
        Run all smoke tests and return results.

        Returns:
            Dict with test results and summary statistics
        """
        print(f"🔍 Running Smoke Tests for {self.base_url}")
        print("=" * 50)

        start_time = time.time()

        # Define all smoke tests
        tests = [
            self.test_homepage_loads,
            self.test_api_health,
            self.test_auth_endpoint_reachable,
            self.test_models_endpoint,
            self.test_static_assets,
            self.test_database_connectivity,
            self.test_login_form_loads
        ]

        # Run all tests
        passed = 0
        failed = 0

        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self.log_result(test_func.__name__, False, f"Test crashed: {str(e)}")

        total_time = time.time() - start_time

        # Generate summary
        summary = {
            'total_tests': len(tests),
            'passed': passed,
            'failed': failed,
            'success_rate': (passed / len(tests)) * 100 if tests else 0,
            'total_time': total_time,
            'timestamp': time.time(),
            'base_url': self.base_url,
            'test_results': self.test_results
        }

        print("\n" + "=" * 50)
        print(f"📊 Smoke Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']} ✅")
        print(f"   Failed: {summary['failed']} ❌")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Total Time: {summary['total_time']:.2f}s")

        if failed == 0:
            print(f"🎉 All smoke tests passed! Application appears healthy.")
        else:
            print(f"⚠️  {failed} smoke test(s) failed. Check the application.")

        return summary


def main():
    """
    Main entry point for smoke tests.
    Can be run from command line or CI/CD pipeline.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Run smoke tests against the application')
    parser.add_argument('--url', required=True, help='Base URL to test (e.g., https://maurinventuresinternal.com)')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
    parser.add_argument('--output', help='Output file for JSON results (optional)')
    parser.add_argument('--fail-fast', action='store_true', help='Exit on first failure')

    args = parser.parse_args()

    # Run smoke tests
    runner = SmokeTestRunner(args.url, args.timeout)

    if args.fail_fast:
        # Run tests one by one and exit on first failure
        tests = [
            runner.test_homepage_loads,
            runner.test_api_health,
            runner.test_auth_endpoint_reachable,
            runner.test_models_endpoint,
            runner.test_static_assets,
            runner.test_database_connectivity,
            runner.test_login_form_loads
        ]

        for test_func in tests:
            if not test_func():
                print(f"\n💥 Smoke test failed: {test_func.__name__}")
                sys.exit(1)

        print("\n✅ All smoke tests passed!")
        sys.exit(0)
    else:
        # Run all tests and report summary
        results = runner.run_all_smoke_tests()

        # Save results to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to {args.output}")

        # Exit with error code if any tests failed
        if results['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == '__main__':
    main()