#!/bin/bash
# Manual Deployment Script (Prompt 28)
# Wrapper script for deployment automation with user-friendly interface

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Default values
DEFAULT_ENVIRONMENT="staging"
DEFAULT_BRANCH="main"
DEFAULT_TYPE="direct"
CONFIG_FILE="config/deployment.yaml"

# Show help
show_help() {
    echo "Usage: $0 [OPTIONS] COMMAND"
    echo ""
    echo "Deployment automation script for Internal Platform"
    echo ""
    echo "Commands:"
    echo "  deploy              Deploy application to environment"
    echo "  rollback            Rollback last deployment"
    echo "  status              Show deployment status"
    echo "  health              Run health check"
    echo "  logs                Show recent deployment logs"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Target environment (staging, production)"
    echo "  -b, --branch BRANCH      Git branch to deploy (default: $DEFAULT_BRANCH)"
    echo "  -c, --commit HASH        Specific commit hash to deploy"
    echo "  -t, --type TYPE          Deployment type (direct, blue_green)"
    echo "  -f, --force              Skip confirmations"
    echo "  -v, --verbose            Enable verbose output"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy -e staging                           # Deploy main to staging"
    echo "  $0 deploy -e production -t blue_green          # Blue-green deploy to production"
    echo "  $0 deploy -e production -c abc1234 -f          # Deploy specific commit"
    echo "  $0 rollback -e production                      # Rollback production"
    echo "  $0 status -e staging                           # Show staging status"
}

# Parse command line arguments
ENVIRONMENT="$DEFAULT_ENVIRONMENT"
BRANCH="$DEFAULT_BRANCH"
COMMIT=""
DEPLOYMENT_TYPE="$DEFAULT_TYPE"
FORCE=false
VERBOSE=false

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -c|--commit)
            COMMIT="$2"
            shift 2
            ;;
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        deploy|rollback|status|health|logs)
            COMMAND="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if command was provided
if [ -z "${COMMAND:-}" ]; then
    print_error "No command specified"
    show_help
    exit 1
fi

# Validate environment
case $ENVIRONMENT in
    staging|production|development)
        ;;
    *)
        print_error "Invalid environment: $ENVIRONMENT"
        echo "Valid environments: staging, production, development"
        exit 1
        ;;
esac

# Validate deployment type
case $DEPLOYMENT_TYPE in
    direct|blue_green|rolling)
        ;;
    *)
        print_error "Invalid deployment type: $DEPLOYMENT_TYPE"
        echo "Valid types: direct, blue_green, rolling"
        exit 1
        ;;
esac

# Check if we're in the project root
if [ ! -f "scripts/deployment_automation.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if deployment automation script exists
if [ ! -f "scripts/deployment_automation.py" ]; then
    print_error "Deployment automation script not found"
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Deployment configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Set verbose flag for Python script
PYTHON_VERBOSE_FLAG=""
if [ "$VERBOSE" = true ]; then
    PYTHON_VERBOSE_FLAG="--verbose"
fi

# Function to show deployment summary
show_deployment_summary() {
    echo ""
    print_header "=== DEPLOYMENT SUMMARY ==="
    echo "Environment: $ENVIRONMENT"
    echo "Branch: $BRANCH"
    if [ -n "$COMMIT" ]; then
        echo "Commit: $COMMIT"
    else
        echo "Commit: Latest from $BRANCH"
    fi
    echo "Type: $DEPLOYMENT_TYPE"
    echo "Config: $CONFIG_FILE"
    echo ""
}

# Function to confirm deployment
confirm_deployment() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    if [ "$ENVIRONMENT" = "production" ]; then
        print_warning "You are about to deploy to PRODUCTION environment!"
        echo ""
        show_deployment_summary
        read -p "Are you sure you want to proceed? (type 'yes' to confirm): " confirm
        if [ "$confirm" != "yes" ]; then
            print_error "Deployment cancelled"
            exit 1
        fi
    else
        show_deployment_summary
        read -p "Proceed with deployment? [Y/n]: " confirm
        if [[ $confirm =~ ^[Nn]$ ]]; then
            print_error "Deployment cancelled"
            exit 1
        fi
    fi
}

# Function to get current commit if not specified
get_commit_hash() {
    if [ -z "$COMMIT" ]; then
        COMMIT=$(git rev-parse HEAD)
        if [ $? -ne 0 ]; then
            print_error "Failed to get current commit hash"
            exit 1
        fi
    fi
}

# Command implementations
case $COMMAND in
    deploy)
        print_header "🚀 Starting Deployment Process"

        # Get commit hash if not specified
        get_commit_hash

        # Show summary and get confirmation
        confirm_deployment

        print_status "Executing deployment..."

        # Build Python command
        PYTHON_CMD="python3 scripts/deployment_automation.py deploy"
        PYTHON_CMD="$PYTHON_CMD --environment $ENVIRONMENT"
        PYTHON_CMD="$PYTHON_CMD --branch $BRANCH"
        PYTHON_CMD="$PYTHON_CMD --commit $COMMIT"
        PYTHON_CMD="$PYTHON_CMD --type $DEPLOYMENT_TYPE"
        PYTHON_CMD="$PYTHON_CMD --config $CONFIG_FILE"

        if [ "$VERBOSE" = true ]; then
            print_status "Executing: $PYTHON_CMD"
        fi

        # Execute deployment
        if eval $PYTHON_CMD; then
            print_success "Deployment completed successfully!"

            # Show deployment info
            echo ""
            print_status "Deployment Details:"
            echo "  Environment: $ENVIRONMENT"
            echo "  Commit: $COMMIT"
            echo "  Type: $DEPLOYMENT_TYPE"

            # Suggest next steps
            echo ""
            print_status "Next Steps:"
            echo "  • Run health check: $0 health -e $ENVIRONMENT"
            echo "  • View logs: $0 logs -e $ENVIRONMENT"
            echo "  • Monitor application: https://$([ "$ENVIRONMENT" = "production" ] && echo "maurinventuresinternal.com" || echo "staging.maurinventuresinternal.com")"

        else
            print_error "Deployment failed!"
            echo ""
            print_status "Troubleshooting:"
            echo "  • Check deployment logs: $0 logs -e $ENVIRONMENT"
            echo "  • Run health check: $0 health -e $ENVIRONMENT"
            echo "  • Consider rollback: $0 rollback -e $ENVIRONMENT"
            exit 1
        fi
        ;;

    rollback)
        print_header "🔄 Starting Rollback Process"

        if [ "$ENVIRONMENT" = "production" ] && [ "$FORCE" != true ]; then
            print_warning "You are about to rollback PRODUCTION environment!"
            read -p "Are you sure you want to proceed? (type 'yes' to confirm): " confirm
            if [ "$confirm" != "yes" ]; then
                print_error "Rollback cancelled"
                exit 1
            fi
        fi

        print_status "Executing rollback..."

        if python3 scripts/deployment_automation.py rollback --environment $ENVIRONMENT --config $CONFIG_FILE; then
            print_success "Rollback completed successfully!"
        else
            print_error "Rollback failed!"
            exit 1
        fi
        ;;

    status)
        print_header "📊 Deployment Status"

        python3 scripts/deployment_automation.py status --environment $ENVIRONMENT --config $CONFIG_FILE
        ;;

    health)
        print_header "🏥 Health Check"

        # Determine URL based on environment
        case $ENVIRONMENT in
            production)
                URL="https://maurinventuresinternal.com"
                ;;
            staging)
                URL="https://staging.maurinventuresinternal.com"
                ;;
            development)
                URL="http://localhost:5001"
                ;;
        esac

        print_status "Running health check for $ENVIRONMENT ($URL)..."

        if python3 tests/smoke_tests.py --url "$URL" --timeout 30; then
            print_success "Health check passed!"
        else
            print_error "Health check failed!"
            exit 1
        fi
        ;;

    logs)
        print_header "📋 Deployment Logs"

        # Show recent deployment logs
        if [ -f "deployment_$(date +%Y%m%d).log" ]; then
            print_status "Showing today's deployment logs:"
            tail -n 50 "deployment_$(date +%Y%m%d).log"
        else
            print_warning "No deployment logs found for today"
        fi

        # Show system logs if available
        print_status "Checking system logs..."
        if command -v journalctl &> /dev/null; then
            sudo journalctl -u mv-internal -n 10 --no-pager 2>/dev/null || print_warning "Cannot access system logs"
        fi
        ;;

    *)
        print_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac

exit 0