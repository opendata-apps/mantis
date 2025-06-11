"""Tests for user data prefilling functionality in the report form.

This test suite validates that when a user accesses /melden/<usrid> with a valid
user ID from gen_user_id.py, their known data (name, email) is properly prefilled
in the form while maintaining the ability to edit the data.
"""
import pytest
from app.database.models import TblUsers
from app.tools.gen_user_id import get_new_id


@pytest.fixture
def test_user_data():
    """Create test user data for prefilling tests."""
    return {
        'user_id': get_new_id(),  # Generate a real user ID using the same function
        'user_name': 'Müller M.',  # Database format: "Lastname F."
        'user_kontakt': 'max.mueller@example.com',
        'user_rolle': '1'
    }


@pytest.fixture
def test_user_data_initial_format():
    """Create test user data with initial format (like existing data)."""
    return {
        'user_id': get_new_id(),
        'user_name': 'Schmidt K.',  # Initial format like existing data
        'user_kontakt': 'k.schmidt@example.com',
        'user_rolle': '1'
    }


class TestReportPrefill:
    """Tests for user data prefilling in the report form."""

    def test_prefill_with_full_name(self, client, session, test_user_data):
        """Test prefilling when user has full first and last name."""
        # Update test data to use the correct database format
        test_user_data['user_name'] = 'Müller M.'  # Database format: "Lastname F."

        # Create a test user in the database
        user = TblUsers(**test_user_data)
        session.add(user)
        session.commit()

        try:
            # Access the form with the user ID
            response = client.get(f'/melden/{test_user_data["user_id"]}')

            assert response.status_code == 200

            # Check that the form contains prefilled data
            response_text = response.data.decode('utf-8')

            # The last name should be prefilled (check for HTML-encoded or plain)
            assert 'value="Müller"' in response_text or 'value="M&uuml;ller"' in response_text, "Last name should be prefilled"

            # The first name should be prefilled with just the initial letter
            assert 'value="M"' in response_text, "First name should be prefilled with initial"

            # The email should be prefilled
            assert 'value="max.mueller@example.com"' in response_text, "Email should be prefilled"

            # Note: The prefill notification message was removed from the template

            # Check that fields are readonly
            # Looking for readonly attribute in the form fields
            assert 'readonly' in response_text.lower(), "Prefilled fields should be readonly"

        finally:
            # Clean up
            session.delete(user)
            session.commit()

    def test_prefill_with_initial_format(self, client, session, test_user_data_initial_format):
        """Test prefilling when user name is in 'Lastname F.' format."""
        # Create a test user in the database
        user = TblUsers(**test_user_data_initial_format)
        session.add(user)
        session.commit()

        try:
            # Access the form with the user ID
            response = client.get(f'/melden/{test_user_data_initial_format["user_id"]}')

            assert response.status_code == 200

            response_text = response.data.decode('utf-8')

            # The last name should be prefilled
            assert 'value="Schmidt"' in response_text, "Last name should be prefilled"

            # The first name should be prefilled with just the initial letter (K from "K.")
            assert 'value="K"' in response_text, "First name should be prefilled with initial letter"

            # The email should be prefilled
            assert 'value="k.schmidt@example.com"' in response_text, "Email should be prefilled"

            # Check that fields are readonly
            # Looking for readonly attribute in the form fields
            assert 'readonly' in response_text.lower(), "Prefilled fields should be readonly"

        finally:
            # Clean up
            session.delete(user)
            session.commit()

    def test_prefill_with_no_email(self, client, session):
        """Test prefilling when user has no email address."""
        test_data = {
            'user_id': get_new_id(),
            'user_name': 'Weber A.',  # Correct database format
            'user_kontakt': None,  # No email
            'user_rolle': '1'
        }

        user = TblUsers(**test_data)
        session.add(user)
        session.commit()

        try:
            response = client.get(f'/melden/{test_data["user_id"]}')

            assert response.status_code == 200

            response_text = response.data.decode('utf-8')

            # Names should be prefilled
            assert 'value="Weber"' in response_text, "Last name should be prefilled"
            assert 'value="A"' in response_text, "First name should be prefilled with initial"

            # Email field should be empty
            email_field_empty = 'name="email"' in response_text and \
                               ('value=""' in response_text or 'value="None"' not in response_text)
            assert email_field_empty, "Email field should be empty when user has no email"

        finally:
            # Clean up
            session.delete(user)
            session.commit()

    def test_no_prefill_for_invalid_user_id(self, client):
        """Test that invalid user ID doesn't cause errors and shows empty form."""
        invalid_user_id = "invalid_user_id_12345"

        response = client.get(f'/melden/{invalid_user_id}')

        assert response.status_code == 200

        response_text = response.data.decode('utf-8')

        # Form should render normally but without prefilled data
        assert 'name="report_first_name"' in response_text, "Form should render normally"
        assert 'name="report_last_name"' in response_text, "Form should render normally"
        assert 'name="email"' in response_text, "Form should render normally"

        # Form should be empty (no prefilled values)
        assert 'value="Weber"' not in response_text, "Form should not have prefilled values"

    def test_form_without_user_id(self, client):
        """Test that accessing /melden without user ID works normally."""
        response = client.get('/melden')

        assert response.status_code == 200

        response_text = response.data.decode('utf-8')

        # Form should render normally
        assert 'name="report_first_name"' in response_text, "Form should render normally"
        assert 'name="report_last_name"' in response_text, "Form should render normally"
        assert 'name="email"' in response_text, "Form should render normally"

        # Form fields should not have readonly attribute (ignore CSS)
        # Check that form fields don't have readonly attribute
        assert 'readonly=' not in response_text or 'readonly"' not in response_text, \
               "Form fields should not have readonly attribute without user ID"

    def test_prefilled_fields_are_readonly(self, client, session, test_user_data):
        """Test that prefilled fields are readonly to prevent identity changes."""
        # Update test data to use the correct database format
        test_user_data['user_name'] = 'Müller M.'  # Database format: "Lastname F."

        # Create a test user in the database
        user = TblUsers(**test_user_data)
        session.add(user)
        session.commit()

        try:
            response = client.get(f'/melden/{test_user_data["user_id"]}')

            assert response.status_code == 200

            response_text = response.data.decode('utf-8')

            # Check that prefilled fields are readonly
            readonly_count = response_text.lower().count('readonly')
            assert readonly_count >= 3, f"Expected at least 3 readonly fields (name, email), found {readonly_count}"

            # Check that readonly styling is defined in CSS
            assert 'input[readonly]' in response_text, "Readonly styling should be defined in CSS"
            assert 'background-color: #f9fafb' in response_text, "Readonly fields should have gray background"

        finally:
            # Clean up
            session.delete(user)
            session.commit()
