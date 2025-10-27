# Testing Guide

This document provides comprehensive information about the testing infrastructure for the AI Concierge Platform.

## Table of Contents

- [Overview](#overview)
- [Backend Testing (Python/FastAPI)](#backend-testing-pythonfastapi)
- [Frontend Testing (Next.js/React)](#frontend-testing-nextjsreact)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Best Practices](#best-practices)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

## Overview

Our testing infrastructure consists of:

- **Backend**: pytest with async support, coverage tracking, and mocked external services
- **Frontend**: Jest + React Testing Library with MSW for API mocking
- **Coverage**: Coverage reporting enabled (set thresholds as needed)
- **Integration**: Tests run via Replit workflows

## Backend Testing (Python/FastAPI)

### Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configuration files**:
   - `pytest.ini` - pytest configuration
   - `.env.test` - test environment variables
   - `tests/conftest.py` - shared fixtures

### Test Structure

```
backend/tests/
├── conftest.py           # Shared fixtures and mocks
├── unit/                 # Unit tests
│   └── test_config.py    # Example config tests
├── integration/          # API integration tests (add as needed)
└── fixtures/             # Test data and fixtures
```

### Running Backend Tests

```bash
# Run all tests
cd backend && pytest

# Run with coverage
pytest -v --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_config.py

# Run tests by marker
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests

# Run with HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html to view
```

### Available Fixtures

- `client` - Synchronous FastAPI test client (automatically mocks database and settings)
- `async_client` - Asynchronous FastAPI test client (automatically mocks database and settings)
- `mock_supabase_client` - Mocked Supabase client for individual tests
- `mock_person_data` - Sample person data
- `mock_household_data` - Sample household data
- `faker_seed` - Seeded Faker instance for consistent test data

### Example Backend Test

```python
import pytest

@pytest.mark.unit
def test_get_settings():
    """Test configuration loading"""
    from app.config import get_settings

    settings = get_settings()
    assert settings is not None
    assert hasattr(settings, "app_name")
    assert hasattr(settings, "app_version")
```

### Testing with Mocked Supabase

```python
import pytest
from unittest.mock import patch

@pytest.mark.unit
@patch("app.database.get_supabase_client")
def test_database_operation(mock_supabase):
    """Test database operations with mocked Supabase"""
    # Configure mock response
    mock_client = mock_supabase.return_value
    mock_client.table.return_value.select.return_value.execute.return_value.data = [
        {"id": 1, "name": "Test"}
    ]

    # Your test code here
    from app.database import get_supabase_client
    client = get_supabase_client()
    result = client.table("test").select("*").execute()

    assert len(result.data) == 1
    assert result.data[0]["name"] == "Test"
```

## Frontend Testing (Next.js/React)

### Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configuration files**:
   - `jest.config.js` - Jest configuration for Next.js
   - `jest.setup.js` - Global test setup and mocks
   - `__mocks__/handlers.ts` - MSW API mocks

### Test Structure

```
frontend/
├── __tests__/
│   ├── components/           # Component tests
│   │   ├── HomePage.test.tsx
│   │   └── ExampleComponent.test.tsx
│   └── integration/          # Integration tests
│       └── api.test.ts
├── __mocks__/                # Mock files
│   ├── handlers.ts           # MSW handlers
│   ├── server.ts             # MSW server setup
│   └── next-router.js        # Next.js router mock
└── jest.config.js
```

### Running Frontend Tests

```bash
# Run all tests
cd frontend && npm test

# Run in watch mode (for development)
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test HomePage.test.tsx

# Update snapshots
npm test -- -u
```

### Available Test Utilities

- `render()` - Render React components
- `screen` - Query rendered output
- `fireEvent` - Trigger DOM events
- `userEvent` - Simulate user interactions
- `waitFor()` - Wait for async operations
- MSW handlers for API mocking

### Example Frontend Test

```tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const user = userEvent.setup()
    render(<MyComponent />)

    await user.click(screen.getByRole('button'))

    await waitFor(() => {
      expect(screen.getByText('Clicked')).toBeInTheDocument()
    })
  })
})
```

## Running Tests

### Via Command Line

```bash
# Backend tests
cd backend && pytest -v --cov=app --cov-report=term-missing

# Frontend tests
cd frontend && npm test

# Both in parallel (from project root)
(cd backend && pytest) & (cd frontend && npm test) & wait
```

### Via Replit Workflows

Replit provides convenient workflows for running tests:

1. **Test Backend** - Runs backend tests with coverage
2. **Test Frontend** - Runs frontend tests
3. **Test All** - Runs both test suites in parallel
4. **Test Coverage** - Generates HTML coverage reports for both

To run a workflow:
1. Click the workflow button in Replit
2. Select the desired test workflow
3. View results in the console

## Writing Tests

### Backend Test Guidelines

1. **Use appropriate markers**:
   ```python
   @pytest.mark.unit
   @pytest.mark.integration
   @pytest.mark.slow
   ```

2. **Mock external services** - Always mock Supabase, Anthropic, Slack, etc.

3. **Use fixtures** - Leverage shared fixtures from conftest.py

4. **Test async code** properly:
   ```python
   @pytest.mark.asyncio
   async def test_async_function():
       result = await my_async_function()
       assert result is not None
   ```

5. **Organize tests** by function - One test file per module/class

### Frontend Test Guidelines

1. **Test user behavior**, not implementation details

2. **Use semantic queries**:
   ```tsx
   // Good
   screen.getByRole('button', { name: 'Submit' })
   screen.getByLabelText('Email')

   // Avoid
   screen.getByClassName('submit-btn')
   ```

3. **Mock API calls** with MSW - Add handlers to `__mocks__/handlers.ts`

4. **Test accessibility** - Use role-based queries and keyboard navigation

5. **Async operations** - Always use `waitFor()` for async state changes

## Best Practices

### General

- ✅ Write tests before fixing bugs
- ✅ Keep tests simple and focused
- ✅ Test one thing per test
- ✅ Use descriptive test names
- ✅ Maintain 80%+ code coverage
- ❌ Don't test third-party libraries
- ❌ Don't test implementation details
- ❌ Don't use production credentials

### Backend Specific

- Mock all external API calls (Anthropic, Slack, AWS)
- Use test database or fully mock database operations
- Test error handling and edge cases
- Validate input/output schemas
- Test authentication and authorization

### Frontend Specific

- Test component rendering and user interactions
- Mock API responses with MSW
- Test loading and error states
- Test form validation
- Verify accessibility (a11y)

## Continuous Integration

### GitHub Actions (Recommended)

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd frontend && npm install
      - run: cd frontend && npm test -- --coverage
```

## Troubleshooting

### Backend Issues

**Problem**: `ImportError` when running tests
- **Solution**: Ensure you're in the `backend` directory and virtual environment is activated

**Problem**: Database connection errors
- **Solution**: Check that `.env.test` is properly configured with mock values

**Problem**: Tests failing due to external API calls
- **Solution**: Verify mocks in `conftest.py` are properly configured

### Frontend Issues

**Problem**: Module resolution errors
- **Solution**: Check `jest.config.js` moduleNameMapper matches `tsconfig.json` paths

**Problem**: "Cannot find module '@testing-library/jest-dom'"
- **Solution**: Run `npm install` to ensure all dependencies are installed

**Problem**: Tests timeout
- **Solution**: Increase timeout in jest.config.js or use `waitFor` with longer timeout

### Common Issues

**Problem**: Coverage below threshold
- **Solution**: Write tests for uncovered code or adjust threshold in config files

**Problem**: Flaky tests
- **Solution**: Add proper `await` statements, use `waitFor()`, avoid race conditions

**Problem**: Slow test execution
- **Solution**: Mark slow tests with `@pytest.mark.slow` and run them separately

## Coverage Reports

### Backend Coverage

HTML reports are generated in `backend/htmlcov/`:
```bash
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html  # or use your browser
```

### Frontend Coverage

HTML reports are generated in `frontend/coverage/`:
```bash
cd frontend
npm run test:coverage
open coverage/lcov-report/index.html
```

## Test Data Management

### Backend

- Use `faker` for generating test data
- Create reusable fixtures in `tests/fixtures/`
- Mock external data sources in `conftest.py`

### Frontend

- Define mock data in MSW handlers (`__mocks__/handlers.ts`)
- Use factory functions for complex test data
- Keep test data close to tests when possible

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/react)
- [MSW Documentation](https://mswjs.io/)

## Questions?

For questions or issues with the testing infrastructure, please create an issue in the project repository or contact the development team.
