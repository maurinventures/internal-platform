#!/bin/bash
# Local Smoke Test Runner (Prompt 26)
# Run this script to execute smoke tests against any environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Default values
DEFAULT_URL="http://localhost:5001"
DEFAULT_TIMEOUT="30"

# Parse command line arguments
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Run smoke tests against the application."
    echo ""
    echo "Options:"
    echo "  -u, --url URL          Target URL to test (default: $DEFAULT_URL)"
    echo "  -t, --timeout SECONDS  Request timeout in seconds (default: $DEFAULT_TIMEOUT)"
    echo "  -f, --fail-fast        Exit on first failure"
    echo "  -o, --output FILE      Save results to JSON file"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Test localhost"
    echo "  $0 -u https://maurinventuresinternal.com    # Test production"
    echo "  $0 -u http://localhost:3000 -f             # Test dev server, fail fast"
    echo "  $0 -u https://staging.example.com -o results.json  # Save results"
}

# Parse arguments
URL="$DEFAULT_URL"
TIMEOUT="$DEFAULT_TIMEOUT"
FAIL_FAST=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            URL="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -f|--fail-fast)
            FAIL_FAST="--fail-fast"
            shift
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

print_status "Running smoke tests..."
echo "Target URL: $URL"
echo "Timeout: ${TIMEOUT}s"
if [ ! -z "$FAIL_FAST" ]; then
    echo "Fail fast: enabled"
fi
if [ ! -z "$OUTPUT_FILE" ]; then
    echo "Output file: $OUTPUT_FILE"
fi
echo ""

# Check if we're in the right directory
if [ ! -f "tests/smoke_tests.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python to run smoke tests."
    exit 1
fi

# Check if requests library is available
if ! $PYTHON_CMD -c "import requests" &> /dev/null; then
    print_warning "requests library not found. Installing..."
    $PYTHON_CMD -m pip install requests || {
        print_error "Failed to install requests library"
        exit 1
    }
fi

# Build the command
CMD="$PYTHON_CMD tests/smoke_tests.py --url \"$URL\" --timeout $TIMEOUT"

if [ ! -z "$FAIL_FAST" ]; then
    CMD="$CMD $FAIL_FAST"
fi

if [ ! -z "$OUTPUT_FILE" ]; then
    CMD="$CMD --output \"$OUTPUT_FILE\""
fi

# Run the smoke tests
print_status "Executing: $CMD"
echo ""

if eval $CMD; then
    print_success "Smoke tests completed successfully!"

    # If output file was created, show where it is
    if [ ! -z "$OUTPUT_FILE" ] && [ -f "$OUTPUT_FILE" ]; then
        print_status "Results saved to: $OUTPUT_FILE"

        # Show quick summary if jq is available
        if command -v jq &> /dev/null; then
            echo ""
            print_status "Quick Summary:"
            echo "  Total Tests: $(jq -r '.total_tests' "$OUTPUT_FILE")"
            echo "  Passed: $(jq -r '.passed' "$OUTPUT_FILE")"
            echo "  Failed: $(jq -r '.failed' "$OUTPUT_FILE")"
            echo "  Success Rate: $(jq -r '.success_rate' "$OUTPUT_FILE")%"
        fi
    fi

    exit 0
else
    print_error "Smoke tests failed!"

    if [ ! -z "$OUTPUT_FILE" ] && [ -f "$OUTPUT_FILE" ]; then
        print_status "Check $OUTPUT_FILE for detailed results"
    fi

    exit 1
fi