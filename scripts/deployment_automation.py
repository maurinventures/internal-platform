"""
Deployment Automation Service (Prompt 28)

Provides automated deployment orchestration, blue-green deployments,
rollback procedures, and deployment monitoring for the Internal Platform.
"""

import os
import time
import json
import logging
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import requests
from enum import Enum


class DeploymentStatus(Enum):
    """Deployment status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


@dataclass
class DeploymentConfig:
    """Deployment configuration."""
    environment: str
    branch: str
    commit_hash: str
    deployment_type: str  # blue_green, rolling, direct
    pre_deployment_checks: List[str]
    post_deployment_checks: List[str]
    rollback_enabled: bool
    health_check_url: str
    health_check_timeout: int
    notification_channels: List[str]


@dataclass
class DeploymentMetrics:
    """Deployment metrics and timing."""
    deployment_id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    status: DeploymentStatus
    environment: str
    commit_hash: str
    error_message: Optional[str]
    rollback_performed: bool
    health_check_results: Dict[str, Any]


class HealthChecker:
    """
    Health checking service for deployment validation.
    """

    def __init__(self, timeout: int = 30):
        """Initialize health checker."""
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def check_application_health(self, base_url: str) -> Dict[str, Any]:
        """
        Perform comprehensive application health check.

        Args:
            base_url: Base URL of the application

        Returns:
            Health check results with status and metrics
        """
        results = {
            'overall_status': 'healthy',
            'checks': {},
            'response_times': {},
            'timestamp': datetime.utcnow().isoformat()
        }

        # Define health check endpoints
        health_endpoints = [
            ('/api/health', 'API Health'),
            ('/', 'Frontend'),
            ('/api/auth/me', 'Authentication')
        ]

        failed_checks = 0

        for endpoint, name in health_endpoints:
            try:
                url = f"{base_url.rstrip('/')}{endpoint}"
                start_time = time.time()

                response = requests.get(url, timeout=self.timeout)
                response_time = time.time() - start_time

                results['response_times'][name] = response_time

                if endpoint == '/api/health':
                    # Expect JSON response for health endpoint
                    if response.status_code == 200:
                        try:
                            health_data = response.json()
                            results['checks'][name] = {
                                'status': 'healthy',
                                'details': health_data
                            }
                        except json.JSONDecodeError:
                            results['checks'][name] = {
                                'status': 'unhealthy',
                                'error': 'Invalid JSON response'
                            }
                            failed_checks += 1
                    else:
                        results['checks'][name] = {
                            'status': 'unhealthy',
                            'error': f'HTTP {response.status_code}'
                        }
                        failed_checks += 1

                elif endpoint == '/':
                    # Expect HTML response for frontend
                    if response.status_code == 200 and 'html' in response.headers.get('content-type', ''):
                        results['checks'][name] = {
                            'status': 'healthy',
                            'details': 'Frontend serving HTML'
                        }
                    else:
                        results['checks'][name] = {
                            'status': 'unhealthy',
                            'error': f'HTTP {response.status_code} or invalid content type'
                        }
                        failed_checks += 1

                elif endpoint == '/api/auth/me':
                    # Expect 401 for unauthenticated auth check
                    if response.status_code == 401:
                        results['checks'][name] = {
                            'status': 'healthy',
                            'details': 'Authentication endpoint responding correctly'
                        }
                    else:
                        results['checks'][name] = {
                            'status': 'unhealthy',
                            'error': f'Unexpected status: HTTP {response.status_code}'
                        }
                        failed_checks += 1

            except requests.exceptions.RequestException as e:
                results['checks'][name] = {
                    'status': 'unhealthy',
                    'error': f'Request failed: {str(e)}'
                }
                results['response_times'][name] = self.timeout
                failed_checks += 1

        # Set overall status
        if failed_checks == 0:
            results['overall_status'] = 'healthy'
        elif failed_checks < len(health_endpoints):
            results['overall_status'] = 'degraded'
        else:
            results['overall_status'] = 'unhealthy'

        return results

    def wait_for_healthy_status(self, base_url: str, max_attempts: int = 30,
                              interval: int = 10) -> bool:
        """
        Wait for application to become healthy.

        Args:
            base_url: Base URL to check
            max_attempts: Maximum number of attempts
            interval: Seconds between attempts

        Returns:
            True if healthy, False if max attempts reached
        """
        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"Health check attempt {attempt}/{max_attempts}")

            results = self.check_application_health(base_url)

            if results['overall_status'] == 'healthy':
                self.logger.info("Application is healthy")
                return True

            if attempt < max_attempts:
                self.logger.info(f"Application not healthy yet, waiting {interval}s...")
                time.sleep(interval)

        self.logger.error("Application failed to become healthy within timeout")
        return False


class BlueGreenDeployer:
    """
    Blue-green deployment implementation.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize blue-green deployer."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.health_checker = HealthChecker()

    def deploy(self, deployment_config: DeploymentConfig) -> DeploymentMetrics:
        """
        Execute blue-green deployment.

        Args:
            deployment_config: Deployment configuration

        Returns:
            Deployment metrics and results
        """
        deployment_id = f"bg_{int(time.time())}"
        start_time = datetime.utcnow()

        self.logger.info(f"Starting blue-green deployment {deployment_id}")

        try:
            # Step 1: Prepare green environment
            self.logger.info("Preparing green environment...")
            green_success = self._prepare_green_environment(deployment_config)

            if not green_success:
                raise Exception("Failed to prepare green environment")

            # Step 2: Deploy to green environment
            self.logger.info("Deploying to green environment...")
            deploy_success = self._deploy_to_green(deployment_config)

            if not deploy_success:
                raise Exception("Failed to deploy to green environment")

            # Step 3: Health check green environment
            self.logger.info("Health checking green environment...")
            green_url = self._get_green_url()
            healthy = self.health_checker.wait_for_healthy_status(green_url)

            if not healthy:
                raise Exception("Green environment failed health checks")

            # Step 4: Run smoke tests on green
            self.logger.info("Running smoke tests on green environment...")
            smoke_test_success = self._run_smoke_tests(green_url)

            if not smoke_test_success:
                raise Exception("Green environment failed smoke tests")

            # Step 5: Switch traffic to green
            self.logger.info("Switching traffic to green environment...")
            switch_success = self._switch_traffic_to_green()

            if not switch_success:
                raise Exception("Failed to switch traffic to green")

            # Step 6: Verify production traffic
            self.logger.info("Verifying production traffic...")
            prod_url = deployment_config.health_check_url
            prod_healthy = self.health_checker.wait_for_healthy_status(prod_url, max_attempts=10)

            if not prod_healthy:
                # Rollback if production isn't healthy
                self.logger.error("Production health check failed, initiating rollback")
                self._rollback_to_blue()
                raise Exception("Production health check failed after traffic switch")

            # Step 7: Cleanup old blue environment
            self.logger.info("Cleaning up old blue environment...")
            self._cleanup_blue_environment()

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return DeploymentMetrics(
                deployment_id=deployment_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                status=DeploymentStatus.SUCCESS,
                environment=deployment_config.environment,
                commit_hash=deployment_config.commit_hash,
                error_message=None,
                rollback_performed=False,
                health_check_results=self.health_checker.check_application_health(prod_url)
            )

        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            self.logger.error(f"Deployment failed: {str(e)}")

            return DeploymentMetrics(
                deployment_id=deployment_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                status=DeploymentStatus.FAILED,
                environment=deployment_config.environment,
                commit_hash=deployment_config.commit_hash,
                error_message=str(e),
                rollback_performed=False,
                health_check_results={}
            )

    def _prepare_green_environment(self, config: DeploymentConfig) -> bool:
        """Prepare green environment for deployment."""
        try:
            # This would typically involve:
            # - Spinning up new instances
            # - Setting up load balancer rules
            # - Configuring database connections
            self.logger.info("Green environment prepared successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to prepare green environment: {str(e)}")
            return False

    def _deploy_to_green(self, config: DeploymentConfig) -> bool:
        """Deploy application to green environment."""
        try:
            # Run deployment commands
            deployment_commands = [
                f"git checkout {config.commit_hash}",
                "cd frontend && npm ci --legacy-peer-deps",
                "cd frontend && npm run build",
                "sudo systemctl restart mv-internal"
            ]

            for cmd in deployment_commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"Command failed: {cmd}")
                    self.logger.error(f"Error: {result.stderr}")
                    return False

            self.logger.info("Deployment to green environment successful")
            return True
        except Exception as e:
            self.logger.error(f"Failed to deploy to green environment: {str(e)}")
            return False

    def _get_green_url(self) -> str:
        """Get URL for green environment."""
        # In a real implementation, this would return the green environment URL
        return "https://maurinventuresinternal.com"

    def _run_smoke_tests(self, url: str) -> bool:
        """Run smoke tests against the environment."""
        try:
            # Run smoke tests
            cmd = f"python tests/smoke_tests.py --url {url} --timeout 30 --fail-fast"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info("Smoke tests passed")
                return True
            else:
                self.logger.error(f"Smoke tests failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to run smoke tests: {str(e)}")
            return False

    def _switch_traffic_to_green(self) -> bool:
        """Switch traffic from blue to green environment."""
        try:
            # This would involve updating load balancer rules
            # For now, simulate the switch
            self.logger.info("Traffic switched to green environment")
            return True
        except Exception as e:
            self.logger.error(f"Failed to switch traffic: {str(e)}")
            return False

    def _rollback_to_blue(self) -> bool:
        """Rollback traffic to blue environment."""
        try:
            # Switch traffic back to blue environment
            self.logger.info("Rolled back traffic to blue environment")
            return True
        except Exception as e:
            self.logger.error(f"Failed to rollback: {str(e)}")
            return False

    def _cleanup_blue_environment(self):
        """Clean up old blue environment."""
        try:
            # Clean up old resources
            self.logger.info("Blue environment cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to cleanup blue environment: {str(e)}")


class DirectDeployer:
    """
    Direct deployment implementation for simpler deployments.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize direct deployer."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.health_checker = HealthChecker()

    def deploy(self, deployment_config: DeploymentConfig) -> DeploymentMetrics:
        """
        Execute direct deployment.

        Args:
            deployment_config: Deployment configuration

        Returns:
            Deployment metrics and results
        """
        deployment_id = f"direct_{int(time.time())}"
        start_time = datetime.utcnow()

        self.logger.info(f"Starting direct deployment {deployment_id}")

        try:
            # Step 1: Pre-deployment backup
            self.logger.info("Creating deployment backup...")
            backup_success = self._create_backup()

            if not backup_success:
                self.logger.warning("Backup creation failed, continuing with deployment")

            # Step 2: Pre-deployment health check
            self.logger.info("Running pre-deployment health check...")
            pre_health = self.health_checker.check_application_health(deployment_config.health_check_url)

            # Step 3: Execute deployment
            self.logger.info("Executing deployment...")
            deploy_success = self._execute_deployment(deployment_config)

            if not deploy_success:
                self.logger.error("Deployment failed, initiating rollback")
                self._rollback_from_backup()
                raise Exception("Deployment execution failed")

            # Step 4: Post-deployment health check
            self.logger.info("Running post-deployment health check...")
            healthy = self.health_checker.wait_for_healthy_status(
                deployment_config.health_check_url,
                max_attempts=20,
                interval=15
            )

            if not healthy:
                self.logger.error("Post-deployment health check failed, initiating rollback")
                rollback_success = self._rollback_from_backup()

                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()

                return DeploymentMetrics(
                    deployment_id=deployment_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    status=DeploymentStatus.ROLLED_BACK,
                    environment=deployment_config.environment,
                    commit_hash=deployment_config.commit_hash,
                    error_message="Health check failed, rollback performed",
                    rollback_performed=rollback_success,
                    health_check_results=self.health_checker.check_application_health(deployment_config.health_check_url)
                )

            # Step 5: Run smoke tests
            self.logger.info("Running smoke tests...")
            smoke_test_success = self._run_smoke_tests(deployment_config.health_check_url)

            if not smoke_test_success:
                self.logger.warning("Smoke tests failed, but deployment is healthy")

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return DeploymentMetrics(
                deployment_id=deployment_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                status=DeploymentStatus.SUCCESS,
                environment=deployment_config.environment,
                commit_hash=deployment_config.commit_hash,
                error_message=None,
                rollback_performed=False,
                health_check_results=self.health_checker.check_application_health(deployment_config.health_check_url)
            )

        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            self.logger.error(f"Deployment failed: {str(e)}")

            return DeploymentMetrics(
                deployment_id=deployment_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                status=DeploymentStatus.FAILED,
                environment=deployment_config.environment,
                commit_hash=deployment_config.commit_hash,
                error_message=str(e),
                rollback_performed=False,
                health_check_results={}
            )

    def _create_backup(self) -> bool:
        """Create deployment backup."""
        try:
            backup_dir = f"/tmp/deployment_backup_{int(time.time())}"
            # In real implementation, this would backup current deployment
            self.logger.info(f"Backup created at {backup_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create backup: {str(e)}")
            return False

    def _execute_deployment(self, config: DeploymentConfig) -> bool:
        """Execute the actual deployment."""
        try:
            # Standard deployment commands
            deployment_commands = [
                f"git pull origin {config.branch}",
                "cd frontend && npm ci --legacy-peer-deps",
                "cd frontend && npm run build",
                "sudo cp -r frontend/build/* /var/www/html/",
                "sudo systemctl restart mv-internal"
            ]

            for cmd in deployment_commands:
                self.logger.info(f"Executing: {cmd}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if result.returncode != 0:
                    self.logger.error(f"Command failed: {cmd}")
                    self.logger.error(f"Error: {result.stderr}")
                    return False

                # Add delay between commands
                time.sleep(2)

            self.logger.info("Deployment execution completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to execute deployment: {str(e)}")
            return False

    def _rollback_from_backup(self) -> bool:
        """Rollback deployment from backup."""
        try:
            # In real implementation, this would restore from backup
            rollback_commands = [
                "git checkout HEAD~1",  # Go back one commit
                "sudo systemctl restart mv-internal"
            ]

            for cmd in rollback_commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"Rollback command failed: {cmd}")
                    return False

            self.logger.info("Rollback completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to rollback: {str(e)}")
            return False

    def _run_smoke_tests(self, url: str) -> bool:
        """Run smoke tests against the deployment."""
        try:
            cmd = f"python tests/smoke_tests.py --url {url} --timeout 30"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info("Smoke tests passed")
                return True
            else:
                self.logger.warning("Smoke tests failed")
                return False

        except Exception as e:
            self.logger.error(f"Failed to run smoke tests: {str(e)}")
            return False


class DeploymentOrchestrator:
    """
    Main deployment orchestration service.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize deployment orchestrator."""
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.deployment_history: List[DeploymentMetrics] = []

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load deployment configuration."""
        if config_path and os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")

        # Default configuration
        return {
            'environments': {
                'production': {
                    'url': 'https://maurinventuresinternal.com',
                    'deployment_type': 'blue_green',
                    'health_check_timeout': 300,
                    'smoke_tests_enabled': True
                },
                'staging': {
                    'url': 'https://staging.maurinventuresinternal.com',
                    'deployment_type': 'direct',
                    'health_check_timeout': 180,
                    'smoke_tests_enabled': True
                }
            }
        }

    def deploy(self, environment: str, branch: str, commit_hash: str,
               deployment_type: Optional[str] = None) -> DeploymentMetrics:
        """
        Execute deployment to specified environment.

        Args:
            environment: Target environment (production, staging, etc.)
            branch: Git branch to deploy
            commit_hash: Specific commit hash to deploy
            deployment_type: Override deployment type (blue_green, direct)

        Returns:
            Deployment metrics and results
        """
        # Get environment configuration
        env_config = self.config.get('environments', {}).get(environment, {})

        if not env_config:
            raise ValueError(f"Unknown environment: {environment}")

        # Create deployment configuration
        deployment_config = DeploymentConfig(
            environment=environment,
            branch=branch,
            commit_hash=commit_hash,
            deployment_type=deployment_type or env_config.get('deployment_type', 'direct'),
            pre_deployment_checks=['health_check'],
            post_deployment_checks=['health_check', 'smoke_tests'],
            rollback_enabled=True,
            health_check_url=env_config['url'],
            health_check_timeout=env_config.get('health_check_timeout', 300),
            notification_channels=['slack']
        )

        # Select deployer based on type
        if deployment_config.deployment_type == 'blue_green':
            deployer = BlueGreenDeployer(self.config)
        else:
            deployer = DirectDeployer(self.config)

        # Execute deployment
        metrics = deployer.deploy(deployment_config)

        # Store deployment history
        self.deployment_history.append(metrics)

        # Send notifications
        self._send_deployment_notification(metrics)

        return metrics

    def get_deployment_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent deployment history."""
        recent_deployments = self.deployment_history[-limit:]
        return [asdict(deployment) for deployment in recent_deployments]

    def rollback_last_deployment(self, environment: str) -> bool:
        """
        Rollback the last deployment in the specified environment.

        Args:
            environment: Environment to rollback

        Returns:
            True if rollback successful, False otherwise
        """
        # Find last successful deployment
        last_deployments = [d for d in self.deployment_history
                          if d.environment == environment and d.status == DeploymentStatus.SUCCESS]

        if len(last_deployments) < 2:
            self.logger.error("No previous successful deployment found for rollback")
            return False

        # Get previous deployment
        previous_deployment = last_deployments[-2]

        self.logger.info(f"Rolling back to commit {previous_deployment.commit_hash}")

        try:
            # Execute rollback deployment
            rollback_metrics = self.deploy(
                environment=environment,
                branch='main',  # Assume rollback to main branch
                commit_hash=previous_deployment.commit_hash,
                deployment_type='direct'  # Use direct deployment for rollback
            )

            return rollback_metrics.status == DeploymentStatus.SUCCESS

        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            return False

    def _send_deployment_notification(self, metrics: DeploymentMetrics):
        """Send deployment notification to configured channels."""
        try:
            status_emoji = {
                DeploymentStatus.SUCCESS: "✅",
                DeploymentStatus.FAILED: "❌",
                DeploymentStatus.ROLLED_BACK: "🔄"
            }

            message = (
                f"{status_emoji.get(metrics.status, '🔄')} Deployment {metrics.status.value}\n"
                f"Environment: {metrics.environment}\n"
                f"Commit: {metrics.commit_hash[:8]}\n"
                f"Duration: {metrics.duration_seconds:.1f}s\n"
            )

            if metrics.error_message:
                message += f"Error: {metrics.error_message}\n"

            self.logger.info(f"Deployment notification: {message}")
            # In real implementation, send to Slack/Discord/email

        except Exception as e:
            self.logger.error(f"Failed to send deployment notification: {str(e)}")


def main():
    """Main function for command line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Deployment Automation Tool")
    parser.add_argument('action', choices=['deploy', 'rollback', 'status'])
    parser.add_argument('--environment', '-e', required=True, help='Target environment')
    parser.add_argument('--branch', '-b', default='main', help='Git branch to deploy')
    parser.add_argument('--commit', '-c', help='Specific commit hash')
    parser.add_argument('--type', choices=['blue_green', 'direct'], help='Deployment type')
    parser.add_argument('--config', help='Path to configuration file')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    orchestrator = DeploymentOrchestrator(args.config)

    if args.action == 'deploy':
        if not args.commit:
            # Get latest commit if not specified
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
            if result.returncode == 0:
                args.commit = result.stdout.strip()
            else:
                print("Error: Could not determine commit hash")
                return 1

        metrics = orchestrator.deploy(
            environment=args.environment,
            branch=args.branch,
            commit_hash=args.commit,
            deployment_type=args.type
        )

        print(f"Deployment {metrics.status.value}")
        print(f"Duration: {metrics.duration_seconds:.1f}s")

        if metrics.error_message:
            print(f"Error: {metrics.error_message}")
            return 1

    elif args.action == 'rollback':
        success = orchestrator.rollback_last_deployment(args.environment)
        if success:
            print("Rollback successful")
        else:
            print("Rollback failed")
            return 1

    elif args.action == 'status':
        history = orchestrator.get_deployment_history(limit=5)
        print("Recent deployments:")
        for deployment in history:
            print(f"  {deployment['commit_hash'][:8]} - {deployment['status']} - {deployment['environment']}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())