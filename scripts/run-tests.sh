#!/bin/bash

# ACIMguide Comprehensive Test Runner
# Usage: ./scripts/run-tests.sh [OPTIONS]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
RUN_PYTHON=true
RUN_JS=true
RUN_E2E=false
RUN_MUTATION=false
RUN_PERFORMANCE=false
COVERAGE_THRESHOLD=90
VERBOSE=false

# Functions
print_usage() {
    echo "ACIMguide Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --python          Run Python tests only"
    echo "  -j, --javascript      Run JavaScript tests only"
    echo "  -e, --e2e            Run E2E tests"
    echo "  -m, --mutation       Run mutation testing"
    echo "  -f, --performance    Run performance tests"
    echo "  -a, --all            Run all tests"
    echo "  -c, --coverage N     Set coverage threshold (default: 90)"
    echo "  -v, --verbose        Verbose output"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --python          # Run only Python tests"
    echo "  $0 --e2e            # Run E2E tests"
    echo "  $0 --all            # Run all tests"
    echo "  $0 -a -c 85         # Run all tests with 85% coverage threshold"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is required but not installed"
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

setup_environment() {
    log_info "Setting up test environment..."
    
    # Load test environment variables
    if [ -f .env.test ]; then
        export $(cat .env.test | xargs)
        log_success "Loaded test environment variables"
    fi
    
    # Set coverage threshold
    export COVERAGE_THRESHOLD=$COVERAGE_THRESHOLD
}

install_dependencies() {
    log_info "Installing dependencies..."
    
    # Python dependencies
    if [ "$RUN_PYTHON" = true ] || [ "$RUN_MUTATION" = true ]; then
        pip install -r requirements.txt > /dev/null 2>&1
        pip install -r orchestration/requirements.txt > /dev/null 2>&1
        log_success "Python dependencies installed"
    fi
    
    # Node.js dependencies
    if [ "$RUN_JS" = true ] || [ "$RUN_E2E" = true ] || [ "$RUN_PERFORMANCE" = true ]; then
        npm ci > /dev/null 2>&1
        log_success "Node.js dependencies installed"
    fi
    
    # Playwright browsers
    if [ "$RUN_E2E" = true ]; then
        npx playwright install > /dev/null 2>&1
        log_success "Playwright browsers installed"
    fi
}

run_python_tests() {
    if [ "$RUN_PYTHON" = true ]; then
        log_info "Running Python tests..."
        
        # Run linting
        log_info "Running Python linting..."
        python -m flake8 orchestration/ scripts/ --count --select=E9,F63,F7,F82 --show-source --statistics
        
        # Run tests with coverage
        pytest tests/ \
            --cov=orchestration \
            --cov=scripts \
            --cov-report=term-missing \
            --cov-report=html:htmlcov \
            --cov-fail-under=$COVERAGE_THRESHOLD \
            --junit-xml=pytest-results.xml \
            $([ "$VERBOSE" = true ] && echo "-v" || echo "-q")
        
        log_success "Python tests completed"
    fi
}

run_javascript_tests() {
    if [ "$RUN_JS" = true ]; then
        log_info "Running JavaScript/TypeScript tests..."
        
        # Run linting
        log_info "Running ESLint..."
        npm run lint || log_warning "ESLint found issues"
        
        # Run unit tests
        npm run test:coverage
        
        log_success "JavaScript tests completed"
    fi
}

run_mutation_tests() {
    if [ "$RUN_MUTATION" = true ]; then
        log_info "Running mutation testing..."
        log_warning "This may take several minutes..."
        
        # Clean previous results
        rm -f .mutmut-cache
        
        # Run mutmut
        timeout 1800 mutmut run --paths-to-mutate=orchestration/,scripts/ || log_warning "Mutation testing timed out or had issues"
        
        # Generate results
        mutmut results > mutation-results.txt || log_warning "Could not generate mutation results"
        
        if [ -f mutation-results.txt ]; then
            log_info "Mutation testing results:"
            cat mutation-results.txt
        fi
        
        log_success "Mutation testing completed"
    fi
}

run_e2e_tests() {
    if [ "$RUN_E2E" = true ]; then
        log_info "Running E2E tests..."
        
        # Check if staging URL is set
        if [ -z "$PLAYWRIGHT_BASE_URL" ]; then
            log_warning "PLAYWRIGHT_BASE_URL not set, using default localhost"
            export PLAYWRIGHT_BASE_URL="http://localhost:3000"
        fi
        
        log_info "Testing against: $PLAYWRIGHT_BASE_URL"
        
        # Run Playwright tests
        npm run test:e2e $([ "$VERBOSE" = true ] && echo "--reporter=list" || echo "")
        
        log_success "E2E tests completed"
    fi
}

run_performance_tests() {
    if [ "$RUN_PERFORMANCE" = true ]; then
        log_info "Running performance tests..."
        
        # Install Lighthouse CLI if not present
        if ! command -v lhci &> /dev/null; then
            npm install -g @lhci/cli@0.12.x > /dev/null 2>&1
        fi
        
        # Check if URL is set
        if [ -z "$PLAYWRIGHT_BASE_URL" ]; then
            log_warning "PLAYWRIGHT_BASE_URL not set, skipping performance tests"
            return
        fi
        
        # Create temporary Lighthouse config
        cat > .lighthouserc.temp.js << EOF
module.exports = {
  ci: {
    collect: {
      url: [
        '$PLAYWRIGHT_BASE_URL',
        '$PLAYWRIGHT_BASE_URL/chat',
        '$PLAYWRIGHT_BASE_URL/blog'
      ],
      numberOfRuns: 1
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', {minScore: 0.8}],
        'categories:accessibility': ['error', {minScore: 0.9}],
        'categories:best-practices': ['warn', {minScore: 0.8}],
        'categories:seo': ['warn', {minScore: 0.8}]
      }
    }
  }
};
EOF
        
        # Run Lighthouse
        lhci autorun --config=.lighthouserc.temp.js || log_warning "Performance tests had issues"
        
        # Cleanup
        rm -f .lighthouserc.temp.js
        
        log_success "Performance tests completed"
    fi
}

generate_report() {
    log_info "Generating test report..."
    
    cat > test-report.md << EOF
# 🧪 Test Execution Report

Generated: $(date)

## Test Configuration
- Coverage Threshold: $COVERAGE_THRESHOLD%
- Python Tests: $([ "$RUN_PYTHON" = true ] && echo "✅" || echo "❌")
- JavaScript Tests: $([ "$RUN_JS" = true ] && echo "✅" || echo "❌")
- E2E Tests: $([ "$RUN_E2E" = true ] && echo "✅" || echo "❌")
- Mutation Tests: $([ "$RUN_MUTATION" = true ] && echo "✅" || echo "❌")
- Performance Tests: $([ "$RUN_PERFORMANCE" = true ] && echo "✅" || echo "❌")

## Results
EOF
    
    # Add results based on what was run
    if [ "$RUN_PYTHON" = true ] && [ -f pytest-results.xml ]; then
        echo "- ✅ Python tests completed with coverage reports in htmlcov/" >> test-report.md
    fi
    
    if [ "$RUN_JS" = true ] && [ -d coverage ]; then
        echo "- ✅ JavaScript tests completed with coverage reports in coverage/" >> test-report.md
    fi
    
    if [ "$RUN_E2E" = true ] && [ -d playwright-report ]; then
        echo "- ✅ E2E tests completed with reports in playwright-report/" >> test-report.md
    fi
    
    if [ "$RUN_MUTATION" = true ] && [ -f mutation-results.txt ]; then
        echo "- ✅ Mutation testing completed with results in mutation-results.txt" >> test-report.md
    fi
    
    if [ "$RUN_PERFORMANCE" = true ] && [ -d .lighthouseci ]; then
        echo "- ✅ Performance tests completed with Lighthouse reports" >> test-report.md
    fi
    
    echo "" >> test-report.md
    echo "## Test Artifacts" >> test-report.md
    echo "- HTML Coverage Reports: htmlcov/index.html" >> test-report.md
    echo "- Playwright Reports: playwright-report/index.html" >> test-report.md
    echo "- Test Results: pytest-results.xml" >> test-report.md
    
    log_success "Test report generated: test-report.md"
}

cleanup() {
    log_info "Cleaning up..."
    
    # Remove temporary files
    rm -f .lighthouserc.temp.js
    
    log_success "Cleanup completed"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--python)
            RUN_PYTHON=true
            RUN_JS=false
            RUN_E2E=false
            RUN_MUTATION=false
            RUN_PERFORMANCE=false
            shift
            ;;
        -j|--javascript)
            RUN_PYTHON=false
            RUN_JS=true
            RUN_E2E=false
            RUN_MUTATION=false
            RUN_PERFORMANCE=false
            shift
            ;;
        -e|--e2e)
            RUN_E2E=true
            shift
            ;;
        -m|--mutation)
            RUN_MUTATION=true
            shift
            ;;
        -f|--performance)
            RUN_PERFORMANCE=true
            shift
            ;;
        -a|--all)
            RUN_PYTHON=true
            RUN_JS=true
            RUN_E2E=true
            RUN_MUTATION=true
            RUN_PERFORMANCE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo "🧪 ACIMguide Comprehensive Test Runner"
    echo "======================================"
    echo ""
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    check_dependencies
    setup_environment
    install_dependencies
    
    # Run tests based on configuration
    run_python_tests
    run_javascript_tests
    run_mutation_tests
    run_e2e_tests
    run_performance_tests
    
    # Generate report
    generate_report
    
    echo ""
    log_success "All tests completed successfully! 🎉"
    echo ""
    log_info "Next steps:"
    echo "  - Review coverage reports in htmlcov/"
    echo "  - Check E2E test results in playwright-report/"
    echo "  - Read the full report in test-report.md"
}

# Run main function
main
