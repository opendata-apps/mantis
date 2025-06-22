# Mantis Testing Guide

This guide explains testing patterns and fixtures available in the Mantis project.

## Available Fixtures

### Flask App Fixtures

- `app`: Session-scoped Flask application instance with test configuration
- `client`: Flask test client for making HTTP requests
- `request_context`: Flask request context to access Flask globals (request, session, g)
- `session_with_user`: Provides an authenticated session with user_id set to '9999'
- `mock_request`: Creates a mock request object with session data
- `authenticated_client`: Test client with an authenticated session
- `mock_render_template`: Mock for Flask's render_template function

### Database Fixtures

- `_db`: Session-scoped database instance for all tests
- `session`: Function-scoped database session that rolls back after each test

## Testing Examples

### Testing Routes

```python
def test_home_page(client):
    """Test that the home page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to Mantis' in response.data
```

### Testing Templates

```python
def test_home_template(client, mock_render_template):
    """Test that home page uses the correct template."""
    client.get('/')
    mock_render_template.assert_called_once_with('home.html')
```

### Testing Authenticated Routes

```python
def test_profile_page(authenticated_client):
    """Test that profile page loads when authenticated."""
    response = authenticated_client.get('/provider/melder')
    assert response.status_code == 200
```

### Testing Functions That Need Session

```python
@pytest.mark.usefixtures("session_with_user")
def test_user_function(request_context):
    """Test a function that needs the Flask session."""
    # Function will have access to flask.session with user_id set
    result = some_function_that_uses_session()
    assert result == expected_value
```

### Parameterized Tests

```python
@pytest.mark.parametrize("route,expected_status", [
    ('/', 200),
    ('/about', 200),
    ('/nonexistent', 404),
    ('/admin', 403)  # Assuming unauthorized access gives 403
])
def test_route_status_codes(client, route, expected_status):
    """Test multiple routes with different expected status codes."""
    response = client.get(route)
    assert response.status_code == expected_status
```

### Custom Form Data Fixtures

```python
@pytest.fixture
def form_data_request(mock_request):
    """Fixture for mocking a request with specific form data."""
    mock_request.form = {
        'field1': 'value1',
        'field2': 'value2'
    }
    return mock_request
```

## Best Practices

1. Use the provided fixtures instead of creating your own
2. Use a separate test function for each test case
3. Keep tests atomic and focused on a single aspect
4. Use meaningful test names that describe what you're testing
5. Use context managers for temporary state/mock changes
6. Clean up any test data or mocks after your test
7. Test both success and failure cases
8. Use parameterized tests for testing similar behaviors with different inputs
9. Place shared fixtures in conftest.py, test-specific fixtures in test files
10. Use transaction rollbacks instead of creating/deleting data
11. Maintain test isolation - tests should not depend on each other