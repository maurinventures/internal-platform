#!/bin/bash
# Local CI Testing Script (Prompt 25)
# Run this script to test CI pipeline components locally before pushing

set -e  # Exit on any error

echo "🔧 Local CI Testing Script"
echo "=========================="

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

# Check if we're in the right directory
if [ ! -f "web/app.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

echo ""
print_status "Testing Frontend Components..."

# Frontend Tests
if [ -d "frontend" ]; then
    cd frontend

    print_status "Installing frontend dependencies..."
    if npm ci --legacy-peer-deps; then
        print_success "Frontend dependencies installed"
    else
        print_warning "Frontend dependencies installation failed (will work in CI)"
    fi

    print_status "Running TypeScript check..."
    if npm run type-check; then
        print_success "TypeScript check passed"
    else
        print_warning "TypeScript check failed (may work in CI with proper setup)"
    fi

    print_status "Checking if test scripts exist..."
    if npm run test -- --watchAll=false --passWithNoTests; then
        print_success "Frontend tests completed"
    else
        print_warning "Frontend tests failed (may work in CI environment)"
    fi

    cd ..
else
    print_warning "Frontend directory not found, skipping frontend tests"
fi

echo ""
print_status "Testing Backend Components..."

# Backend Tests
print_status "Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_warning "Python not found, skipping Python tests"
    PYTHON_CMD=""
fi

if [ ! -z "$PYTHON_CMD" ]; then
    print_status "Installing Python dependencies..."
    if $PYTHON_CMD -m pip install -r requirements.txt; then
        print_success "Python dependencies installed"

        print_status "Running Python linting checks..."

        # Install linting tools
        $PYTHON_CMD -m pip install flake8 black isort pytest safety bandit

        # Run flake8
        if flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; then
            print_success "Flake8 syntax check passed"
        else
            print_error "Flake8 found syntax errors"
        fi

        # Check if files can be formatted by black
        if black --check --diff . ; then
            print_success "Black formatting check passed"
        else
            print_warning "Black formatting check failed (run 'black .' to fix)"
        fi

        # Check import sorting
        if isort --check-only --diff . ; then
            print_success "Import sorting check passed"
        else
            print_warning "Import sorting check failed (run 'isort .' to fix)"
        fi

        # Run safety check
        if safety check; then
            print_success "Safety check passed"
        else
            print_warning "Safety check found known vulnerabilities"
        fi

        # Run basic pytest
        if pytest tests/ --maxfail=5 -q; then
            print_success "Backend tests passed"
        else
            print_warning "Some backend tests failed"
        fi

    else
        print_warning "Failed to install Python dependencies"
    fi
else
    print_warning "Skipping Python tests - Python not available"
fi

echo ""
print_status "Checking CI Configuration Files..."

# Check if CI files exist
CI_FILES=(
    ".github/workflows/ci.yml"
    ".github/pull_request_template.md"
    "frontend/.eslintrc.js"
    "frontend/.prettierrc"
    "frontend/.prettierignore"
    ".flake8"
    "pyproject.toml"
    "docs/CI_SETUP.md"
)

for file in "${CI_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "✓ $file exists"
    else
        print_error "✗ $file missing"
    fi
done

echo ""
print_status "Checking package.json scripts..."
if [ -f "frontend/package.json" ]; then
    REQUIRED_SCRIPTS=("test:ci" "lint" "prettier:check" "type-check")
    for script in "${REQUIRED_SCRIPTS[@]}"; do
        if grep -q "\"$script\":" frontend/package.json; then
            print_success "✓ npm script '$script' defined"
        else
            print_warning "✗ npm script '$script' missing"
        fi
    done
else
    print_warning "frontend/package.json not found"
fi

echo ""
print_success "Local CI testing completed!"
echo ""
print_status "Next Steps:"
echo "1. Fix any errors shown above"
echo "2. Commit and push changes to trigger CI pipeline"
echo "3. Create a pull request to test the full CI workflow"
echo "4. Check GitHub Actions tab to see pipeline results"
echo ""
print_status "For detailed setup instructions, see docs/CI_SETUP.md"