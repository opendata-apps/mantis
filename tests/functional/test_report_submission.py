"""Tests for the mantis report submission process including form validation and database operations.

This test suite validates the complete report submission functionality including:
1. Form rendering
2. Form validation (all field types)
3. File upload handling
4. Security features (honeypot, rate limiting)
5. Database integration
6. Gender field mapping
"""

import datetime
import io
import json
from unittest.mock import patch
from PIL import Image
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database.models import TblFundorte, TblMeldungen, TblUsers, TblMeldungUser
from app.database.fundortbeschreibung import TblFundortBeschreibung
from app.tools.coordinate_validation import LAT_RANGE, LON_RANGE
from tests.helpers import build_valid_report_form_data, make_test_image


def create_test_image():
    """Create a test image file in memory."""
    return make_test_image(
        fmt="jpeg",
        name="test_image.jpg",
        size=(100, 100),
        color="red",
    )


@pytest.fixture
def report_form_data():
    """Creates valid data for the mantis sighting report form."""
    return build_valid_report_form_data(
        sighting_days_ago=7,
        userid="",
        report_first_name="Test",
        report_last_name="Reporter",
        email="test@example.com",
        contact="test@example.com",
        fund_street="Alexanderplatz",
        gender="Männlich",
        location_description="1",
        description="Spotted on a plant",
        identical_finder_reporter=True,
    )


@pytest.fixture
def location_test_data():
    """Provides test data for TblFundorte model.

    Used for database integration tests to create location records.

    Returns:
        dict: Default values for a test location record
    """
    return {
        "mtb": "3644",
        "longitude": "13.404954",
        "latitude": "52.520008",
        "ort": "Berlin",
        "land": "Berlin",
        "kreis": "Berlin",
        "strasse": "Alexanderplatz",
        "plz": 10178,  # Integer, not string
        "amt": "Berlin",
        "ablage": "test_image.jpg",
    }


@pytest.fixture
def user_test_data():
    """Provides test data for TblUsers model.

    Used for database integration tests to create user records.

    Returns:
        dict: Default values for a test user record
    """
    return {
        "user_id": "TEST123",
        "user_name": "Reporter T.",
        "user_kontakt": "test@example.com",
        "user_rolle": "1",  # String, not integer
    }


class TestReportSubmission:
    """Tests for the mantis report submission route.

    This test class covers form rendering, validation, file upload,
    database integration, and security features of the submission process.

    The database fixture rebuilds and seeds the schema before each test.
    """

    def test_report_form_renders(self, client):
        """Test that the report form page renders correctly.

        Verifies:
        - The route responds with 200 status code
        - The page contains the correct heading text
        """

        response = client.get("/melden")

        assert response.status_code == 200
        assert b"Melden Sie Ihre Beobachtung" in response.data

    def test_coordinate_range_is_exposed_to_the_frontend(self, client):
        """The map and reviewer modal read the accepted range off <body>."""
        response = client.get("/melden")

        expected = json.dumps(
            {"latitude": list(LAT_RANGE), "longitude": list(LON_RANGE)}
        )
        assert f"data-coord-range='{expected}'" in response.data.decode("utf-8")

    #########################
    # Database Model Tests #
    #########################

    def test_database_models_integration(
        self, session, location_test_data, user_test_data
    ):
        """Test direct database model interaction for the report flow.

        This test verifies that all database models used in the report
        submission process can be properly created and linked together,
        mimicking what happens during an actual form submission.

        Verifies:
        - Location records can be created
        - Sighting records can be created and linked to locations
        - User records can be created
        - User-sighting relations can be created
        - All relationships between records work correctly
        """
        # Test data
        heute = datetime.datetime.now().date()
        user_id = user_test_data["user_id"]

        # First, we need to find a valid beschreibung ID from the database
        valid_description = session.scalar(select(TblFundortBeschreibung))
        if not valid_description:
            # Create a new description if none exists
            valid_description = TblFundortBeschreibung(
                beschreibung="Im Garten, auf einer Wiese"
            )
            session.add(valid_description)
            session.flush()

        # 1. Create location record
        location = TblFundorte(
            **location_test_data,
            beschreibung=valid_description.id,  # ID, not string
        )
        session.add(location)
        session.flush()  # Get the ID without committing
        # 2. Create sighting record
        sighting = TblMeldungen(
            dat_fund_von=heute - datetime.timedelta(days=7),
            dat_meld=heute,
            fo_zuordnung=location.id,
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
            anm_melder="Spotted on a plant TEST RECORD",  # Mark as test record in comment
        )
        session.add(sighting)
        session.flush()
        # 3. Create user record
        user = TblUsers(**user_test_data)
        session.add(user)
        session.flush()
        # 4. Create user-sighting relation
        relation = TblMeldungUser(id_meldung=sighting.id, id_user=user.id)
        session.add(relation)
        session.commit()
        # Verify database entries
        location_db = session.scalar(
            select(TblFundorte).where(TblFundorte.id == location.id)
        )
        assert location_db is not None
        assert location_db.ort == "Berlin"
        assert location_db.beschreibung == valid_description.id

        sighting_db = session.scalar(
            select(TblMeldungen).where(TblMeldungen.id == sighting.id)
        )
        assert sighting_db is not None
        assert sighting_db.art_m == 1
        assert sighting_db.fo_zuordnung == location.id

        user_db = session.scalar(select(TblUsers).where(TblUsers.user_id == user_id))
        assert user_db is not None
        assert user_db.user_name == "Reporter T."

        relation_db = session.scalar(
            select(TblMeldungUser).where(
                TblMeldungUser.id_meldung == sighting.id,
                TblMeldungUser.id_user == user.id,
            )
        )
        assert relation_db is not None

    def test_negative_validation_missing_required_fields(self, session):
        """Test that database models enforce required fields.

        This test verifies that the database schema correctly
        enforces required field constraints by attempting to
        save a record with a missing required field.

        Verifies:
        - IntegrityError is raised when required fields are missing
        - Transaction is rolled back properly on error
        """
        # Create sighting without required date field (dat_fund_von is nullable=False)
        invalid_sighting = TblMeldungen(
            # Missing dat_fund_von (which is nullable=False)
            dat_meld=datetime.datetime.now().date(),
            fo_zuordnung=1,  # Provide a value for fo_zuordnung
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
            anm_melder="Spotted on a plant",
        )

        session.add(invalid_sighting)

        # The dat_fund_von column is marked as nullable=False
        # so this should raise an IntegrityError when we try to commit
        with pytest.raises(IntegrityError):
            session.commit()

        # Roll back the failed transaction
        session.rollback()

    # Gender field mapping is tested in tests/unit/test_report_helpers.py::TestSetGenderFields
    # using the actual _set_gender_fields function from app/routes/report.py.

    ############################
    # Form Submission Tests #
    ############################

    def test_image_upload_integration(
        self, app, client, report_form_data, session, tmp_path, monkeypatch
    ):
        monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))
        before = set(session.scalars(select(TblMeldungen.id)))
        response = client.post(
            "/melden",
            data={**report_form_data, "photo": create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert response.json["success"] is True

        report = session.scalars(
            select(TblMeldungen).where(TblMeldungen.id.not_in(before))
        ).one()
        assert report.dat_meld == datetime.date.today()
        assert report.dat_fund_von.isoformat() == report_form_data["sighting_date"]
        assert report.anm_melder == report_form_data["description"]
        assert (
            report.tiere,
            report.art_m,
            report.art_w,
            report.art_n,
            report.art_o,
        ) == (1, 1, 0, 0, 0)
        location = report.fundort
        assert location is not None
        assert location.ort == report_form_data["fund_city"]
        assert location.strasse == report_form_data["fund_street"]
        assert location.plz == report_form_data["fund_zip_code"]
        assert float(location.latitude) == float(report_form_data["latitude"])
        assert float(location.longitude) == float(report_form_data["longitude"])
        assert location.beschreibung == 1
        with Image.open(tmp_path / location.ablage) as saved:
            saved.load()
            assert saved.format == "WEBP"
            assert saved.size == (100, 100)
        assert report.reporter_link is not None
        user = report.reporter_link.reporter
        assert user.user_name == "Reporter T."
        assert user.user_kontakt == report_form_data["email"]
        assert user.user_rolle == "1"

    @patch("app.routes.report._process_uploaded_image")
    def test_submission_outside_germany_is_allowed(
        self, mock_process_image, client, report_form_data, session
    ):
        """Reports outside Germany must still be accepted without AGS/MTB enrichment."""
        mock_process_image.return_value = "dummy/path/outside_germany.webp"

        form_data = report_form_data.copy()
        form_data.update(
            {
                "latitude": "48.8566",
                "longitude": "2.3522",
                "fund_city": "Paris",
                "fund_state": "Île-de-France",
                "fund_district": "Paris",
                "fund_street": "Rue de Rivoli",
                "fund_zip_code": "75001",
                "location_description": "1",
            }
        )

        response = client.post(
            "/melden",
            data={**form_data, "photo": create_test_image()},
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload is not None
        assert payload["success"] is True
        mock_process_image.assert_called_once()

        sighting = session.scalar(
            select(TblMeldungen)
            .where(TblMeldungen.anm_melder == form_data["description"])
            .order_by(TblMeldungen.id.desc())
        )
        assert sighting is not None

        location = session.get(TblFundorte, sighting.fo_zuordnung)
        assert location is not None
        assert location.latitude == float(form_data["latitude"])
        assert location.longitude == float(form_data["longitude"])
        assert location.ort == form_data["fund_city"]
        assert location.land == form_data["fund_state"]
        assert location.kreis == form_data["fund_district"]
        assert location.amt == ""
        assert location.mtb == ""

    ############################
    # Form Validation Tests #
    ############################

    @pytest.mark.parametrize(
        "field,invalid_value,error_message",
        [
            (
                "sighting_date",
                lambda: (
                    datetime.datetime.now() + datetime.timedelta(days=10)
                ).strftime("%Y-%m-%d"),
                "Datum darf nicht in der Zukunft liegen",
            ),
            ("longitude", "200.0", "Längengrad muss zwischen -20 und 44,83 liegen"),
            (
                "longitude",
                "-23.552937",
                "Längengrad muss zwischen -20 und 44,83 liegen",
            ),
            ("latitude", "100.0", "Breitengrad muss zwischen 24,6 und 60 liegen"),
            ("latitude", "69.224997", "Breitengrad muss zwischen 24,6 und 60 liegen"),
            (
                "email",
                "invalid-email",
                "Bitte geben Sie eine gültige E-Mail-Adresse ein",
            ),
        ],
    )
    def test_field_validation_errors_parameterized(
        self, client, report_form_data, field, invalid_value, error_message
    ):
        """Test validation errors for various form fields using parameterization.

        This parameterized test validates various field validation rules by
        submitting forms with invalid data and checking for appropriate error messages.

        Parameters:
            field: The form field to test
            invalid_value: The invalid value to use (can be a function for dynamic values)
            error_message: Expected error message
        """
        # Create form data with invalid value for the specified field
        form_data = report_form_data.copy()
        form_data["location_description"] = "1"

        # If invalid_value is a function (for dynamic values like dates), call it
        if callable(invalid_value):
            form_data[field] = invalid_value()
        else:
            form_data[field] = invalid_value

        # Submit form with invalid data
        response = client.post(
            "/melden",
            data={**form_data, "photo": create_test_image()},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        # Invalid submissions are answered with the field errors as JSON
        assert response.status_code == 400
        messages = response.get_json()["errors"].get(field, [])
        assert any(error_message in msg for msg in messages), (
            f"Expected error message '{error_message}' not found in {messages}"
        )

    def test_swapped_coordinates_rejected(self, client, report_form_data, session):
        """Reversed latitude/longitude must be rejected instead of stored."""
        form_data = report_form_data.copy()
        form_data["location_description"] = "1"
        # Berlin with the two values transposed
        form_data["latitude"] = "13.404954"
        form_data["longitude"] = "52.520008"

        response = client.post(
            "/melden",
            data={**form_data, "photo": create_test_image()},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        assert response.status_code == 400
        payload = response.get_json()
        assert payload["success"] is False
        assert any("vertauscht" in msg for msg in payload["errors"]["longitude"])

        location = session.scalar(
            select(TblFundorte).where(TblFundorte.latitude == 13.404954)
        )
        assert location is None

    @pytest.mark.parametrize("upload", ["missing", "text", "oversized"])
    def test_file_upload_validation(self, client, report_form_data, session, upload):
        before = set(session.scalars(select(TblMeldungen.id)))
        data = report_form_data.copy()
        if upload == "text":
            data["photo"] = (io.BytesIO(b"not an image"), "test.txt")
        elif upload == "oversized":
            data["photo"] = (io.BytesIO(b"x" * (13 * 1024 * 1024)), "large.jpg")
        response = client.post("/melden", data=data, content_type="multipart/form-data")
        assert response.status_code == 400
        assert set(response.json["errors"]) == {"photo"}
        assert set(session.scalars(select(TblMeldungen.id))) == before

    ############################
    # Security Feature Tests #
    ############################

    def test_honeypot_spam_protection(self, client, report_form_data, session):
        before = set(session.scalars(select(TblMeldungen.id)))
        response = client.post(
            "/melden",
            data={**report_form_data, "honeypot": "x", "photo": create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 403
        assert set(session.scalars(select(TblMeldungen.id))) == before
