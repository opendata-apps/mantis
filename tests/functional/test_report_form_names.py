"""Names and unknown sighting details survive the public submission form."""

import pytest
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.database.models import TblMeldungen, TblMeldungUser, TblUsers
from tests.helpers import build_valid_report_form_data, make_test_image


def test_unknown_location_description_is_rejected_before_saving(client, session):
    before = set(session.scalars(select(TblMeldungen.id)))

    response = client.post(
        "/melden",
        data=build_valid_report_form_data(
            location_description="12", photo=make_test_image()
        ),
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "location_description" in response.get_json()["errors"]
    assert set(session.scalars(select(TblMeldungen.id))) == before


@pytest.mark.parametrize("gender", [None, "", "Unbekannt"])
def test_full_names_and_unknown_gender_are_saved(client, session, gender):
    data = build_valid_report_form_data(
        report_name="  Anne-Marie   O’Neill  ",
        finder_name="李 小龍",
        identical_finder_reporter="",
        email="",
        location_description="2",
        photo=make_test_image(),
    )
    if gender is None:
        data.pop("gender")
    else:
        data["gender"] = gender

    response = client.post("/melden", data=data, content_type="multipart/form-data")

    assert response.status_code == 200, response.get_data(as_text=True)
    saved = session.scalar(select(TblMeldungen).order_by(TblMeldungen.id.desc()))
    link = session.scalar(
        select(TblMeldungUser).where(TblMeldungUser.id_meldung == saved.id)
    )
    assert session.get(TblUsers, link.id_user).user_name == "Anne-Marie O’Neill"
    assert session.get(TblUsers, link.id_finder).user_name == "李 小龍"
    assert saved.fundort.beschreibung == 2
    assert (saved.art_m, saved.art_w, saved.art_n, saved.art_o, saved.art_f) == (
        0,
        0,
        0,
        0,
        0,
    )


@pytest.mark.parametrize("name", ["李", "N" * 100])
def test_reporter_name_accepts_one_to_one_hundred_characters(client, session, name):
    response = client.post(
        "/melden",
        data=build_valid_report_form_data(report_name=name, photo=make_test_image()),
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    report = session.scalar(select(TblMeldungen).order_by(TblMeldungen.id.desc()))
    assert report.reporter_link.reporter.user_name == name


@pytest.mark.parametrize("name", ["   ", "N" * 101, "Anna\x00Test", "Anna\u202eTest"])
def test_invalid_reporter_name_is_rejected_before_saving(client, session, name):
    before = set(session.scalars(select(TblMeldungen.id)))
    response = client.post(
        "/melden",
        data=build_valid_report_form_data(report_name=name, photo=make_test_image()),
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "report_name" in response.get_json()["errors"]
    assert set(session.scalars(select(TblMeldungen.id))) == before


def test_new_name_is_prefilled_without_splitting(client, session):
    user = TblUsers(
        user_id="full-name-prefill",
        user_name="Noa van der Meer",
        user_rolle="1",
        user_kontakt="",
    )
    session.add(user)
    session.commit()

    response = client.get("/melden/full-name-prefill")

    field = BeautifulSoup(response.data, "html.parser").find("input", id="report_name")
    assert field is not None
    assert field["value"] == "Noa van der Meer"
    assert field.has_attr("readonly")
