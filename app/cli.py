import os
import shutil

import click
from flask import current_app
from flask.cli import with_appcontext


def register_commands(app):
    """Register all CLI commands with the Flask app."""
    app.cli.add_command(create_all_data_view)
    app.cli.add_command(seed_command)
    app.cli.add_command(seed_ags_command)
    app.cli.add_command(validate_coordinates_command)


@click.command("create_all_data_view")
@with_appcontext
def create_all_data_view():
    """Create the materialized view."""
    import app.database.alldata as ad

    from app import db

    ad.create_materialized_view(db.engine, session=db.session)
    click.echo("Materialized view created.")


@click.command("seed")
@click.option("--demo", is_flag=True, help="Include demo reports and images")
@with_appcontext
def seed_command(demo):
    """Seed database with base data. Use --demo to include sample reports."""
    import app.database.alldata as ad
    from app.database.populate import populate_all

    from app import db

    # Load AGS data from fallback JSON file
    fallback_path = os.path.join(
        os.path.dirname(__file__), "data", "ags_gemeinden.json"
    )
    if os.path.exists(fallback_path):
        with open(fallback_path, "r", encoding="utf-8") as f:
            jsondata = f.read()
    else:
        click.echo(
            "Warning: No AGS fallback data found at app/data/ags_gemeinden.json\n"
            "Run 'flask seed-ags' first to fetch administrative area data.",
            err=True,
        )
        jsondata = None

    # Always populate base data (idempotent)
    populate_all(db.engine, db.session, jsondata)
    click.echo("Base data seeded.")

    if demo:
        from app.demodata.filldb import insert_data_reports

        insert_data_reports(db.session)
        _copy_demo_images()
        click.echo("Demo data seeded.")

    # Refresh views
    ad.refresh_materialized_view(db)
    click.echo("Done.")


@click.command("seed-ags")
@with_appcontext
def seed_ags_command():
    """Fetch administrative area data from official WFS services and seed the database.

    Fetches Gemeinden + Kreise from BKG and Berlin Bezirke from Geoportal Berlin,
    merges them, and upserts into the aemter table. Saves a local JSON fallback
    for offline use by 'flask seed'.
    """
    from sqlalchemy import select

    from app import db
    from app.tools.fetch_ags import (
        fetch_gemeinden,
        fetch_kreise,
        fetch_berlin_bezirke,
        merge_gemeinden_with_berlin,
        build_kreise_lookup,
        save_fallback,
        save_kreise_lookup,
    )

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    fallback_path = os.path.join(data_dir, "ags_gemeinden.json")
    kreise_path = os.path.join(data_dir, "ags_kreise.json")

    try:
        # Fetch from WFS
        click.echo("Fetching Gemeinden from BKG WFS...")
        gemeinden = fetch_gemeinden()

        click.echo("Fetching Kreise from BKG WFS...")
        kreise_data = fetch_kreise()

        click.echo("Fetching Berlin Bezirke from ALKIS WFS...")
        berlin = fetch_berlin_bezirke()

        # Merge: replace Berlin whole-city with 12 Bezirke
        click.echo("Merging datasets...")
        merged = merge_gemeinden_with_berlin(gemeinden, berlin)
        click.echo(f"Merged dataset: {len(merged['features'])} features")

        # Build Kreise lookup
        kreise_lookup = build_kreise_lookup(kreise_data)
        click.echo(f"Built Kreise lookup: {len(kreise_lookup)} entries")

        # Save fallback files
        save_fallback(merged, fallback_path)
        save_kreise_lookup(kreise_lookup, kreise_path)
        click.echo(f"Saved fallback to {fallback_path}")
        click.echo(f"Saved Kreise lookup to {kreise_path}")

        # Sync database: replace all rows with fresh dataset
        click.echo("Syncing aemter table...")
        from app.database.aemter_koordinaten import TblAemterCoordinaten

        # Build set of AGS codes in the fresh dataset
        fresh_ags = set()
        for feat in merged["features"]:
            ags = int(feat["properties"]["AGS"])
            fresh_ags.add(ags)

            existing = db.session.get(TblAemterCoordinaten, ags)
            if existing:
                # Update geometry and name in case they changed
                existing.gen = feat["properties"]["GEN"]
                existing.properties = feat["geometry"]
            else:
                db.session.add(
                    TblAemterCoordinaten(
                        ags=ags,
                        gen=feat["properties"]["GEN"],
                        properties=feat["geometry"],
                    )
                )

        # Remove stale records not in fresh dataset (e.g. Berlin whole-city)
        all_rows = db.session.scalars(select(TblAemterCoordinaten)).all()
        removed = 0
        for row in all_rows:
            if row.ags not in fresh_ags:
                db.session.delete(row)
                removed += 1

        db.session.commit()
        if removed:
            click.echo(f"Removed {removed} stale record(s)")
        click.echo(
            f"Synced {len(fresh_ags)} records. Administrative area data is up to date."
        )

    except Exception as e:
        click.echo(f"Error fetching AGS data: {e}", err=True)
        raise click.Abort()


@click.command("validate-coordinates")
@click.option("--csv", "csv_path", default=None, help="Write mismatches to a CSV file")
@click.option(
    "--verbose", is_flag=True, help="Show all checked fundorte, not just mismatches"
)
@with_appcontext
def validate_coordinates_command(csv_path, verbose):
    """Check that stored address fields match the coordinates on the map.

    Compares each Fundort's 'land' and 'ort' against what the GemeindeFinder
    resolves from its coordinates.  Reports mismatches without modifying any data.
    """
    from sqlalchemy import select, func

    from app import db
    from app.database.fundorte import TblFundorte
    from app.tools.gemeinde_finder import get_amt_enriched
    from app.tools.validate_coordinates import (
        validate_fundorte,
        format_report,
        format_csv,
    )

    count = db.session.scalar(select(func.count(TblFundorte.id)))
    click.echo(f"Loading {count} Fundorte...")

    fundorte = db.session.scalars(select(TblFundorte)).all()

    click.echo("Validating coordinates against address fields...")
    mismatches, checked, skipped = validate_fundorte(fundorte, get_amt_enriched)

    click.echo(format_report(mismatches, checked, skipped))

    if csv_path and mismatches:
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(format_csv(mismatches))
        click.echo(f"\nCSV written to {csv_path}")

    if mismatches:
        raise SystemExit(1)


def _copy_demo_images():
    """Copy demo images for sample reports."""
    # Source: demodata folder (tracked in git, not publicly served)
    src = os.path.join(os.path.dirname(__file__), "demodata", "images")
    # Target: user uploads folder for demo reports (use app config, not class directly)
    trg = os.path.join(current_app.config["UPLOAD_FOLDER"], "2025", "2025-01-19")
    os.makedirs(trg, exist_ok=True)
    mappings = [
        ("mantis1.webp", "Zossen-20250119100000-9999.webp"),
        (
            "mantis2.webp",
            "Ziesar-20250119101500-f04ad4e0b099b6404b1ccda0af0282cf49693b43.webp",
        ),
        (
            "mantis3.webp",
            "Cottbus-20250119103000-5843c1093f94be44442ff876cac6185a2d36310e.webp",
        ),
        (
            "mantis4.webp",
            "Treuenbrietzen-20250119104500-264aca7e20e15aa2401f042dceed384da6d7747a.webp",
        ),
        (
            "mantis5.webp",
            "Pritzwalk-20250119110000-2ab71517482f824f925d09b9aa6e387df99befa7.webp",
        ),
        (
            "mantis6.webp",
            "Halle_Saale-20250119111500-874208b1da349f20a88862f38a856bd711c2e165.webp",
        ),
        (
            "mantis1.webp",
            "Fichtwald-20250119113000-1fb0cfb0be3b0c75c537a50c57e0060ba8b6837e.webp",
        ),
        (
            "mantis2.webp",
            "Luckenwalde-20250119114500-c56fe0b6262dc626a5faf21c55b1f34f7babcfb1.webp",
        ),
        (
            "mantis3.webp",
            "Cottbus-20250119120000-2d7345fd039eaef8796047c61ab760cac52b67e4.webp",
        ),
        (
            "mantis4.webp",
            "Bad_Freienwalde_Oder-20250119121500-9b9d6a941dea27e46f4e5c79284f7df4c82fca49.webp",
        ),
        (
            "mantis5.webp",
            "Berlin-20250119123000-a88de66aa7976cb7990af54c16c0fd2c067515f9.webp",
        ),
        (
            "mantis6.webp",
            "Frankfurt_Oder-20250119124500-d2c830fd84ccabe149aff154c5e1ddcef662f052.webp",
        ),
        (
            "mantis5.webp",
            "Caputh-20250119130000-0c7571741c04d2365aa7816efd298e8df9091122.webp",
        ),
        (
            "mantis2.webp",
            "Seevetal-20250119131500-166bc2da77cb1d6e9a07f3d6fd61c841b394f3c6.webp",
        ),
        (
            "mantis3.webp",
            "Leipzig-20250119133000-6325e4e69ee6789a7aa0ebb9a0e0b63cdf67795a.webp",
        ),
        (
            "mantis4.webp",
            "Berlin-20250119134500-086cd63464247668799cc5a508235012b64a4bf9.webp",
        ),
        (
            "mantis5.webp",
            "Elsterwerda-20250119140000-a1a0c14a53b7bbd010fc48ab2ac42d35d959d2b8.webp",
        ),
        (
            "mantis6.webp",
            "Jueterbog-20250119141500-5f4a7fec84fb0801a5157cf1ce41835774a92704.webp",
        ),
        (
            "mantis1.webp",
            "Jessen_Elster-20250119143000-7228ef93c5b4347ffdcfe63d77bd8617fdb080e5.webp",
        ),
        (
            "mantis2.webp",
            "Friesack-20250119144500-c56782d029b8a62160175fd7112b74f573cd101f.webp",
        ),
    ]
    for src_file, target_file in mappings:
        src_path = os.path.join(src, src_file)
        if os.path.exists(src_path):
            shutil.copy2(src_path, os.path.join(trg, target_file))
