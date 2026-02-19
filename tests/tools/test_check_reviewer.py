"""Tests for the authentication decorators (login_required, reviewer_required)."""

from unittest.mock import MagicMock, patch

from flask import Flask, g
from app.tools.check_reviewer import login_required, reviewer_required


def _make_mock_user(user_id="9999", user_rolle="9"):
    """Create a mock user object for testing."""
    user = MagicMock()
    user.user_id = user_id
    user.user_rolle = user_rolle
    return user


class TestLoginRequired:
    """Test the login_required decorator functionality."""

    @patch("app.tools.check_reviewer.db")
    def test_authenticated_user_gets_200(self, mock_db):
        """Test that authenticated users can access protected routes."""
        mock_db.session.scalar.return_value = _make_mock_user()

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-protected")
        @login_required
        def protected_route():
            return "Success"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "9999"

            response = client.get("/test-protected")
            assert response.status_code == 200
            assert response.data == b"Success"

    def test_unauthenticated_user_gets_401(self):
        """Test that unauthenticated users get 401 (session expired)."""
        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-protected-401")
        @login_required
        def protected_route():
            return "Success"

        with test_app.test_client() as client:
            response = client.get("/test-protected-401")
            assert response.status_code == 401

    def test_preserves_function_attributes(self):
        """Test that the decorator preserves the original function's attributes."""

        def original_function():
            """Original function docstring."""
            return "result"

        original_function.custom_attr = "custom_value"

        decorated_function = login_required(original_function)

        assert decorated_function.__name__ == "original_function"
        assert decorated_function.__doc__ == "Original function docstring."

    @patch("app.tools.check_reviewer.db")
    def test_passes_through_function_arguments(self, mock_db):
        """Test that the decorator passes through function arguments correctly."""
        mock_db.session.scalar.return_value = _make_mock_user()

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-args/<arg1>/<arg2>")
        @login_required
        def route_with_args(arg1, arg2):
            return f"{arg1},{arg2}"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "9999"

            response = client.get("/test-args/hello/world")
            assert response.status_code == 200
            assert response.data == b"hello,world"

    @patch("app.tools.check_reviewer.db")
    def test_handles_keyword_arguments(self, mock_db):
        """Test that the decorator handles keyword arguments."""
        mock_db.session.scalar.return_value = _make_mock_user()

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-kwargs")
        @login_required
        def route_with_kwargs():
            from flask import request

            name = request.args.get("name", "default")
            return f"Hello {name}"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "9999"

            response = client.get("/test-kwargs?name=TestUser")
            assert response.status_code == 200
            assert response.data == b"Hello TestUser"

    @patch("app.tools.check_reviewer.db")
    def test_works_with_stacked_decorators(self, mock_db):
        """Test that login_required works with other decorators."""
        mock_db.session.scalar.return_value = _make_mock_user()

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        def another_decorator(f):
            from functools import wraps

            @wraps(f)
            def decorated(*args, **kwargs):
                result = f(*args, **kwargs)
                return f"Modified: {result}"

            return decorated

        @test_app.route("/test-multi-decorator")
        @login_required
        @another_decorator
        def multi_decorated_route():
            return "Original"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "9999"

            response = client.get("/test-multi-decorator")
            assert response.status_code == 200
            assert response.data == b"Modified: Original"

    @patch("app.tools.check_reviewer.db")
    def test_cleared_session_denies_access(self, mock_db):
        """Test that clearing session prevents access to protected routes."""
        mock_db.session.scalar.return_value = _make_mock_user()

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-logout")
        @login_required
        def protected_route():
            return "Success"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "9999"

            response = client.get("/test-logout")
            assert response.status_code == 200

            with client.session_transaction() as sess:
                sess.clear()

            response = client.get("/test-logout")
            assert response.status_code == 401

    @patch("app.tools.check_reviewer.db")
    def test_deleted_user_gets_401(self, mock_db):
        """Test that a session referencing a deleted user gets 401."""
        mock_db.session.scalar.return_value = None

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-deleted-user")
        @login_required
        def protected_route():
            return "Success"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "deleted-user-id"

            response = client.get("/test-deleted-user")
            assert response.status_code == 401

    @patch("app.tools.check_reviewer.db")
    def test_deleted_user_session_is_cleared(self, mock_db):
        """Stale session should be purged so subsequent requests don't hit DB."""
        mock_db.session.scalar.return_value = None

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-stale-session")
        @login_required
        def protected_route():
            return "Success"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "deleted-user-id"

            client.get("/test-stale-session")

            # Session should have been cleared by the decorator
            with client.session_transaction() as sess:
                assert "user_id" not in sess

    @patch("app.tools.check_reviewer.db")
    def test_sets_g_current_user(self, mock_db):
        """Decorator must populate g.current_user for downstream route code."""
        mock_user = _make_mock_user()
        mock_db.session.scalar.return_value = mock_user

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-g-user")
        @login_required
        def check_g_user():
            return g.current_user.user_id

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "9999"

            response = client.get("/test-g-user")
            assert response.status_code == 200
            assert response.data == b"9999"


class TestReviewerRequired:
    """Test the reviewer_required decorator functionality."""

    @patch("app.tools.check_reviewer.db")
    def test_reviewer_gets_200(self, mock_db):
        """Test that a user with role '9' can access reviewer routes."""
        mock_db.session.scalar.return_value = _make_mock_user(user_rolle="9")

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-reviewer")
        @reviewer_required
        def reviewer_route():
            return "Reviewer Content"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "9999"

            response = client.get("/test-reviewer")
            assert response.status_code == 200
            assert response.data == b"Reviewer Content"

    @patch("app.tools.check_reviewer.db")
    def test_non_reviewer_gets_403(self, mock_db):
        """Test that a user with role != '9' is rejected."""
        mock_db.session.scalar.return_value = _make_mock_user(user_rolle="1")

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-non-reviewer")
        @reviewer_required
        def reviewer_route():
            return "Reviewer Content"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "9999"

            response = client.get("/test-non-reviewer")
            assert response.status_code == 403

    def test_unauthenticated_gets_401(self):
        """Test that unauthenticated users get 401 (delegated to login_required)."""
        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-reviewer-noauth")
        @reviewer_required
        def reviewer_route():
            return "Reviewer Content"

        with test_app.test_client() as client:
            response = client.get("/test-reviewer-noauth")
            assert response.status_code == 401

    @patch("app.tools.check_reviewer.db")
    def test_deleted_user_gets_401(self, mock_db):
        """Test that a deleted user is rejected (delegated to login_required)."""
        mock_db.session.scalar.return_value = None

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-reviewer-deleted")
        @reviewer_required
        def reviewer_route():
            return "Reviewer Content"

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "deleted-user"

            response = client.get("/test-reviewer-deleted")
            assert response.status_code == 401

    @patch("app.tools.check_reviewer.db")
    def test_sets_g_current_user(self, mock_db):
        """Reviewer decorator must also populate g.current_user."""
        mock_user = _make_mock_user(user_rolle="9")
        mock_db.session.scalar.return_value = mock_user

        test_app = Flask(__name__)
        test_app.config["SECRET_KEY"] = "test-secret-key"

        @test_app.route("/test-reviewer-g")
        @reviewer_required
        def check_g_user():
            return g.current_user.user_id

        with test_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = "9999"

            response = client.get("/test-reviewer-g")
            assert response.status_code == 200
            assert response.data == b"9999"

    def test_preserves_function_attributes(self):
        """Test that reviewer_required preserves the original function's metadata."""

        @reviewer_required
        def my_view():
            """My view docstring."""
            return "result"

        assert my_view.__name__ == "my_view"
        assert my_view.__doc__ == "My view docstring."
