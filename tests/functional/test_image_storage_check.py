import pytest
from sqlalchemy import select

from app.database.models import TblFundorte


@pytest.mark.parametrize("condition", ["present", "missing", "outside"])
def test_image_check_requires_every_referenced_photo_inside_the_upload_root(
    app, session, tmp_path, condition
):
    upload_root = tmp_path / "uploads"
    upload_root.mkdir()
    app.config["UPLOAD_FOLDER"] = str(upload_root)
    locations = session.scalars(select(TblFundorte).order_by(TblFundorte.id)).all()
    assert locations
    for index, location in enumerate(locations):
        location.ablage = f"photo-{index}.webp"
        (upload_root / location.ablage).write_bytes(b"photo")
    if condition == "missing":
        locations[0].ablage = "missing-private-reporter-token.webp"
    elif condition == "outside":
        (tmp_path / "private-reporter-token.webp").write_bytes(b"private")
        locations[0].ablage = "../private-reporter-token.webp"
    session.commit()

    result = app.test_cli_runner().invoke(args=["check-images"])

    assert result.exit_code == (0 if condition == "present" else 1)
    assert "Checked" in result.output
    assert "private-reporter-token" not in result.output
    assert session.scalars(
        select(TblFundorte.ablage).order_by(TblFundorte.id)
    ).all() == [location.ablage for location in locations]
