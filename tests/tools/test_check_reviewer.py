"""Tests for the authentication decorator."""
import pytest
from flask import session, abort, Flask
from app.tools.check_reviewer import login_required
from werkzeug.exceptions import Forbidden


class TestLoginRequired:
    """Test the login_required decorator functionality."""

    def test_login_required_with_authenticated_user(self):
        """Test that authenticated users can access protected routes."""
        # Create a fresh Flask app for this test
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Create a test route with the decorator
        @test_app.route('/test-protected')
        @login_required
        def protected_route():
            return 'Success'
        
        # Test with authenticated session
        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = '9999'
            
            response = client.get('/test-protected')
            assert response.status_code == 200
            assert response.data == b'Success'
    
    def test_login_required_without_authentication(self):
        """Test that unauthenticated users get 403 error."""
        # Create a fresh Flask app for this test
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Create a test route with the decorator
        @test_app.route('/test-protected-403')
        @login_required
        def protected_route():
            return 'Success'
        
        # Test without authenticated session
        with test_app.test_client() as client:
            response = client.get('/test-protected-403')
            assert response.status_code == 403
    
    def test_login_required_preserves_function_attributes(self):
        """Test that the decorator preserves the original function's attributes."""
        # Define a function with attributes
        def original_function():
            """Original function docstring."""
            return 'result'
        
        original_function.custom_attr = 'custom_value'
        
        # Apply decorator
        decorated_function = login_required(original_function)
        
        # Check that functools.wraps preserves attributes
        assert decorated_function.__name__ == 'original_function'
        assert decorated_function.__doc__ == 'Original function docstring.'
    
    def test_login_required_with_function_arguments(self):
        """Test that the decorator passes through function arguments correctly."""
        # Create a fresh Flask app for this test
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Create a test route with arguments
        @test_app.route('/test-args/<arg1>/<arg2>')
        @login_required
        def route_with_args(arg1, arg2):
            return f'{arg1},{arg2}'
        
        # Test with authenticated session
        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = '9999'
            
            response = client.get('/test-args/hello/world')
            assert response.status_code == 200
            assert response.data == b'hello,world'
    
    def test_login_required_with_keyword_arguments(self):
        """Test that the decorator handles keyword arguments."""
        # Create a fresh Flask app for this test
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Create a test route that uses request args
        @test_app.route('/test-kwargs')
        @login_required
        def route_with_kwargs():
            from flask import request
            name = request.args.get('name', 'default')
            return f'Hello {name}'
        
        # Test with authenticated session
        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = '9999'
            
            response = client.get('/test-kwargs?name=TestUser')
            assert response.status_code == 200
            assert response.data == b'Hello TestUser'
    
    def test_login_required_multiple_decorators(self):
        """Test that login_required works with other decorators."""
        # Create a fresh Flask app for this test
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret-key'
        
        def another_decorator(f):
            from functools import wraps
            @wraps(f)
            def decorated(*args, **kwargs):
                result = f(*args, **kwargs)
                return f'Modified: {result}'
            return decorated
        
        # Create a route with multiple decorators
        @test_app.route('/test-multi-decorator')
        @login_required
        @another_decorator
        def multi_decorated_route():
            return 'Original'
        
        # Test with authenticated session
        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = '9999'
            
            response = client.get('/test-multi-decorator')
            assert response.status_code == 200
            assert response.data == b'Modified: Original'
    
    def test_session_cleared_after_logout(self):
        """Test that clearing session prevents access to protected routes."""
        # Create a fresh Flask app for this test
        test_app = Flask(__name__)
        test_app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Create a test route with the decorator
        @test_app.route('/test-logout')
        @login_required
        def protected_route():
            return 'Success'
        
        with test_app.test_client() as client:
            # First, login
            with client.session_transaction() as sess:
                sess['user_id'] = '9999'
            
            # Verify access works
            response = client.get('/test-logout')
            assert response.status_code == 200
            
            # Clear session (logout)
            with client.session_transaction() as sess:
                sess.clear()
            
            # Verify access is now denied
            response = client.get('/test-logout')
            assert response.status_code == 403