# Test Plan for New Entry Point and Modular System

## Overview
This document outlines the testing strategy for the new root `main.py` entry point and the modular system architecture.

## Test Objectives

1. **Verify root `main.py` functionality** - Ensure the entry point works correctly
2. **Test modular system initialization** - Verify modules load and initialize properly
3. **Validate file migration** - Confirm all files are in correct locations
4. **Check backward compatibility** - Ensure existing functionality still works
5. **Test event-based communication** - Verify modules can communicate via events
6. **Validate import architecture** - Ensure no circular dependencies or rule violations

## Test Environment

### Prerequisites
- Python 3.8+
- All dependencies installed (`pip install -r requirements.txt`)
- Existing database (`thesentient.db`) available
- Frontend build available (for integration tests)

### Test Directory Structure
```
tests/
├── unit/                  # Unit tests
├── integration/          # Integration tests
├── functional/          # Functional tests
└── e2e/                 # End-to-end tests
```

## Test Cases

### 1. Root main.py Tests

#### TC-001: Basic Execution
**Description**: Test that main.py runs without errors
**Steps**:
1. Execute `python main.py --help`
2. Verify help text is displayed
3. Execute `python main.py`
4. Verify system information is displayed

**Expected Results**:
- Help text shows available options
- System runs without errors
- Appropriate output is displayed

#### TC-002: Modular System Startup
**Description**: Test modular system initialization
**Steps**:
1. Execute `python main.py --modular`
2. Verify modular system initializes
3. Check that modules are discovered
4. Verify event bus is created

**Expected Results**:
- Modular system starts without errors
- Modules are loaded from `src/modular/modules/`
- Event bus is operational

#### TC-003: Legacy System Fallback
**Description**: Test legacy system fallback when modular is unavailable
**Steps**:
1. Temporarily rename `src/modular/` directory
2. Execute `python main.py`
3. Verify system falls back to legacy backend
4. Restore directory

**Expected Results**:
- System detects modular system unavailable
- Falls back to legacy backend
- Legacy system starts without errors

### 2. File Migration Tests

#### TC-010: File Location Validation
**Description**: Verify all files are in correct locations
**Steps**:
1. Run file location validation script
2. Check for files in wrong locations
3. Verify directory structure matches plan

**Expected Results**:
- No Python files in root directory (except main.py)
- All scripts in appropriate `scripts/` subdirectories
- All source code in `src/` directory
- All data in `data/` directory

#### TC-011: Import Path Validation
**Description**: Test that all imports work with new paths
**Steps**:
1. Run import validation script
2. Check for broken imports
3. Verify relative imports work correctly

**Expected Results**:
- All Python imports succeed
- No `ModuleNotFoundError` exceptions
- Relative paths resolve correctly

### 3. Modular System Tests

#### TC-020: Module Discovery
**Description**: Test module discovery mechanism
**Steps**:
1. Create test module in `src/modular/modules/`
2. Run module registry discovery
3. Verify test module is discovered
4. Remove test module

**Expected Results**:
- Module registry discovers all `.py` files in modules directory
- Test module is loaded successfully
- Module implements `ModuleInterface`

#### TC-021: Module Initialization
**Description**: Test module initialization lifecycle
**Steps**:
1. Load a module via module registry
2. Call `initialize()` method
3. Verify module initializes successfully
4. Call `shutdown()` method

**Expected Results**:
- Module initializes without errors
- `initialize()` returns `True`
- `shutdown()` cleans up resources
- No resource leaks

#### TC-022: Event Communication
**Description**: Test event-based communication between modules
**Steps**:
1. Create two test modules
2. Module A publishes an event
3. Module B subscribes to the event
4. Verify event is received

**Expected Results**:
- Event is published successfully
- Subscribing module receives event
- Event data is preserved
- No events are lost

#### TC-023: Dependency Injection
**Description**: Test dependency injection container
**Steps**:
1. Register services in DI container
2. Request service instances
3. Verify correct instances are returned
4. Test circular dependency detection

**Expected Results**:
- Services are registered successfully
- Correct instances are returned
- Circular dependencies are detected and prevented
- Container handles missing services gracefully

### 4. Backward Compatibility Tests

#### TC-030: API Endpoint Compatibility
**Description**: Test that existing API endpoints still work
**Steps**:
1. Start legacy backend
2. Test key API endpoints:
   - `GET /api/debug/build`
   - `GET /api/news`
   - `GET /api/bots`
   - `POST /api/auth/login`
3. Verify responses match expected format

**Expected Results**:
- All tested endpoints return successful responses
- Response format matches existing API
- No regression in functionality

#### TC-031: Database Connectivity
**Description**: Test database connections with new paths
**Steps**:
1. Test connection to `data/databases/thesentient.db`
2. Execute sample queries
3. Verify data integrity
4. Test transaction support

**Expected Results**:
- Database connections succeed
- Queries return expected results
- Data integrity maintained
- Transactions work correctly

#### TC-032: Script Compatibility
**Description**: Test that utility scripts still work
**Steps**:
1. Run key scripts from new locations:
   - `scripts/check/bot_api.py`
   - `scripts/debug/bot.py`
   - `scripts/management/reactivate_bot.py`
2. Verify scripts execute without errors
3. Check script output matches expectations

**Expected Results**:
- Scripts run successfully from new locations
- Output matches previous behavior
- No path-related errors

### 5. Integration Tests

#### TC-040: Module-to-Adapter Integration
**Description**: Test integration between modules and adapters
**Steps**:
1. Create module that depends on adapter
2. Inject adapter via DI
3. Test module functionality using adapter
4. Verify communication works

**Expected Results**:
- Module successfully uses adapter
- Adapter provides expected functionality
- No integration issues

#### TC-041: API-to-Module Integration
**Description**: Test API endpoints calling modules
**Steps**:
1. Start modular system with API layer
2. Call API endpoints
3. Verify modules handle requests
4. Check response format

**Expected Results**:
- API endpoints route to correct modules
- Modules process requests successfully
- Responses are properly formatted

#### TC-042: Frontend-Backend Integration
**Description**: Test frontend integration with new backend
**Steps**:
1. Start modular backend
2. Start frontend development server
3. Load frontend in browser (or simulate)
4. Verify frontend can connect to backend

**Expected Results**:
- Frontend successfully connects to backend
- API calls return expected data
- WebSocket connections work
- CORS configured correctly

### 6. Performance Tests

#### TC-050: Module Loading Performance
**Description**: Test performance of module loading
**Steps**:
1. Time module discovery process
2. Time module initialization
3. Compare with legacy system startup
4. Profile memory usage

**Expected Results**:
- Module loading completes within acceptable time
- Memory usage is reasonable
- No significant performance regression vs legacy

#### TC-051: Event Bus Performance
**Description**: Test event bus throughput
**Steps**:
1. Publish large number of events
2. Measure event delivery latency
3. Test with multiple subscribers
4. Profile memory usage under load

**Expected Results**:
- Event bus handles expected load
- Latency is acceptable
- No memory leaks with high event volume

### 7. Security Tests

#### TC-060: Module Isolation
**Description**: Test module security boundaries
**Steps**:
1. Create malicious test module
2. Attempt to access other module's data
3. Test privilege escalation attempts
4. Verify module sandboxing

**Expected Results**:
- Modules cannot access each other's private data
- Security boundaries are enforced
- No privilege escalation possible

#### TC-061: API Security
**Description**: Test API security with new architecture
**Steps**:
1. Test authentication endpoints
2. Verify authorization checks
3. Test input validation
4. Check for common vulnerabilities

**Expected Results**:
- Authentication works correctly
- Authorization is enforced
- Input is properly validated
- No security regressions

## Test Automation

### 1. Unit Test Framework
```python
# tests/unit/test_main.py
import pytest
from main import main

def test_main_help():
    """Test main.py help output"""
    # Test implementation

def test_modular_system():
    """Test modular system initialization"""
    # Test implementation
```

### 2. Integration Test Framework
```python
# tests/integration/test_module_integration.py
import pytest
from modular.core.module_registry import ModuleRegistry

@pytest.fixture
def module_registry():
    """Fixture for module registry"""
    registry = ModuleRegistry()
    registry.discover_modules()
    return registry

def test_module_discovery(module_registry):
    """Test module discovery"""
    assert len(module_registry.modules) > 0
```

### 3. Functional Test Scripts
```bash
#!/bin/bash
# tests/functional/run_tests.sh

echo "Running functional tests..."
python -m pytest tests/functional/ -v
```

### 4. Continuous Integration
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: ./tests/run_all_tests.sh
```

## Test Data

### Sample Test Modules
Create test modules in `tests/fixtures/modules/`:
- `test_news.py` - Simple news module for testing
- `test_bot.py` - Simple bot module for testing
- `test_strategy.py` - Simple strategy module for testing

### Test Configuration
```yaml
# tests/fixtures/config/test_config.yaml
modules:
  test_news:
    enabled: true
    config:
      test_mode: true
  test_bot:
    enabled: true
    config:
      test_mode: true
```

### Mock Services
Create mock services for testing:
- `MockEventBus` - In-memory event bus for testing
- `MockDataProvider` - Mock data provider
- `MockConfigManager` - Mock configuration manager

## Test Execution Plan

### Phase 1: Pre-Migration Tests
1. Run existing test suite
2. Document current behavior
3. Create baseline metrics

### Phase 2: Unit Tests (During Migration)
1. Test individual components
2. Fix issues as they arise
3. Maintain test coverage

### Phase 3: Integration Tests (Post-Migration)
1. Test component integration
2. Verify system behavior
3. Fix integration issues

### Phase 4: System Tests (Final)
1. Test complete system
2. Performance testing
3. Security testing
4. User acceptance testing

## Success Criteria

### Must Have (Blocking Issues)
- [ ] Root `main.py` executes without errors
- [ ] All modules load successfully
- [ ] Event bus works correctly
- [ ] All existing API endpoints work
- [ ] Database connections work
- [ ] No Python files in root (except main.py)

### Should Have (Important)
- [ ] Performance within 10% of legacy system
- [ ] Memory usage stable
- [ ] All tests pass
- [ ] Documentation updated

### Nice to Have (Optional)
- [ ] Improved performance over legacy
- [ ] Additional test coverage
- [ ] Automated deployment
- [ ] Monitoring integration

## Rollback Criteria

If any of the following occur, roll back to previous state:
1. Critical functionality broken
2. Data loss or corruption
3. Security vulnerabilities introduced
4. Performance degradation > 50%
5. System instability

## Test Reporting

### Daily Test Reports
- Number of tests passed/failed
- Critical issues found
- Test coverage metrics
- Performance benchmarks

### Final Test Report
- Overall test results
- Performance comparison
- Security assessment
- Recommendation for production deployment

## Next Steps After Testing

1. **Fix Critical Issues** - Address blocking issues
2. **Optimize Performance** - Improve slow components
3. **Update Documentation** - Reflect changes
4. **Train Team** - On new architecture
5. **Deploy to Staging** - For further testing
6. **Monitor Production** - After deployment

## Appendix: Test Scripts

### Import Validation Script
```python
# scripts/validate_imports.py
import ast
import sys
from pathlib import Path

def validate_imports():
    """Validate all imports in the project"""
    issues = []
    for py_file in Path(".").rglob("*.py"):
        if "test" in str(py_file) or "venv" in str(py_file):
            continue
        issues.extend(validate_file_imports(py_file))
    
    if issues:
        print("Import validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("All imports validated successfully")

if __name__ == "__main__":
    validate_imports()
```

### File Location Validation Script
```python
# scripts/validate_locations.py
from pathlib import Path

def validate_file_locations():
    """Validate files are in correct locations"""
    root = Path(".")
    
    # Files that should NOT be in root
    forbidden_in_root = [
        "*.py",  # Except main.py
        "*.txt", "*.log", "*.db",
        "*.bat", "*.sh"
    ]
    
    issues = []
    for pattern in forbidden_in_root:
        for file in root.glob(pattern):
            if file.name != "main.py":  # main.py is allowed
                issues.append(f"File in root should be moved: {file}")
    
    return issues