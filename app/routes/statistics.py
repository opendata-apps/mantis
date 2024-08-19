from flask import Blueprint
from flask import render_template, request
from flask import session, abort
from sqlalchemy import func, text, or_
from app import db
from app.database.models import TblUsers
from app.tools.check_reviewer import login_required
from app.tools.gen_messtisch_svg import create_measure_sheet
from app.database.models import TblFundorte, TblMeldungen
from datetime import datetime, timedelta
from collections import defaultdict

stats = Blueprint("statistics", __name__)

list_of_stats = {
    "xxx": "Bitte eine Wahl treffen ...",
    "start": "Startseite/Filter",
    "geschlecht": "Entwicklungsstadium/Geschlecht",
    "meldungen_funddatum": "Meldungen: Funddatum",
    "meldungen_meldedatum": "Meldungen: Meldedatum",
    "meldungen_meld_fund": "Meldungen: Fund- und Meldedatum",
    "meldungen_mtb": "Grafik: Messtischblatt",
    "meldungen_amt": "Auswertung Amt/Gemeinde",
    "meldungen_laender": "Meldungen Bundesländer",
    "meldungen_brb": "Meldungen Brandenburg",
    "meldungen_berlin": "Meldungen Berlin",
    "meldungen_gesamt": "Alle Summen (Tabelle)"
}


def get_date_interval(request=None):
    "Calculate and format start and end date"

    now = datetime.now().isoformat()
    last_year = datetime.now() - timedelta(weeks=52)
    last_year = last_year.isoformat()

    if request:
        start_date = request.form.get("dateFrom", last_year)
        end_date = request.form.get("dateTo", now)
    if not end_date:
        end_date = now
    if not start_date:
        start_date = last_year
    return (start_date[:10], end_date[:10])


@stats.route("/statistik", methods=["POST", "GET"])
@stats.route("/statistik/<usrid>", methods=["POST", "GET"])
@login_required
def stats_start(usrid=None):
    "Startseite für alle Statistiken"
    date_from, date_to = get_date_interval(request)
    user_id = session["user_id"]
    user = TblUsers.query.filter_by(user_id=user_id).first()

    # If the user doesn't exist or the role isn't 9, return 404
    if not user or user.user_rolle != "9":
        abort(403)
    """[
    ('statusInput', 'all'),
    ('typeInput', 'all'),
    ('dateFrom', ''),
    ('dateTo', ''),
    ('userId', '9999'),
    ('stats', 'geschlecht')]
    """
    start_date, end_date = get_date_interval(request)
    value = request.form.get("stats", "start")

    if value == "geschlecht":
        return stats_geschlecht(request)
    elif value == "meldungen_meldedatum":
        return stats_bardiagram_datum(
            request,
            dbfields=['dat_meld'],
            page='stats-meldedatum.html',
            marker="meldungen_meldedatum",
            dateFrom=start_date,
            dateTo=end_date)
    elif value == "meldungen_funddatum":
        return stats_bardiagram_datum(
            request,
            dbfields=['dat_fund_von'],
            page='stats-funddatum.html',
            marker="meldungen_funddatum",
            dateFrom=start_date,
            dateTo=end_date)
    elif value == "meldungen_meld_fund":
        return stats_bardiagram_datum(
            request,
            dbfields=['dat_fund_von', 'dat_meld'],
            page='stats-meld-fund.html',
            marker="meldungen_meld_fund",
            dateFrom=start_date,
            dateTo=end_date)
    elif value == "meldungen_mtb":
        return stats_mtb(request,
                         dateFrom=start_date,
                         dateTo=end_date,
                         marker="meldungen_mtb")
    elif value == "meldungen_amt":
        return stats_amt(request,
                         dateFrom=start_date,
                         dateTo=end_date,
                         marker="meldungen_amt")
    elif value == "meldungen_laender":
        return stats_laender(request,
                             dateFrom=start_date,
                             dateTo=end_date,
                             marker="meldungen_laender")
    elif value == "meldungen_brb":
        return stats_brb(request,
                         dateFrom=start_date,
                         dateTo=end_date,
                         marker="meldungen_brb")
    elif value == "meldungen_berlin":
        return stats_berlin(request,
                            dateFrom=start_date,
                            dateTo=end_date,
                            marker="meldungen_berlin")
    elif value == "meldungen_gesamt":
        return stats_gesamt(request,
                            dateFrom=start_date,
                            dateTo=end_date,
                            marker="meldungen_gesamt")
    elif value == "start":
        return render_template(
            "statistics/statistiken.html",
            user_id=session["user_id"],
            menu=list_of_stats,
            marker="start",
            dateFrom=start_date,
            dateTo=end_date
        )
    else:
        return render_template(
            "statistics/statistiken.html",
            user_id=session["user_id"],
            menu=list_of_stats,
            marker="start",
            dateFrom=start_date,
            dateTo=end_date
        )


def stats_mtb(request, dateFrom, dateTo, marker):
    "Results as MTB (Messtischblatt-Raster)"

    art = request.form.get('typeInput', 'all')
    typeInput = ['mtb', 'maennlich', 'weiblich', 'oothek',
                 'nymphe', 'andere', 'all']
    conn = db.session
    dbanswers = []
    query = conn.query(
        TblFundorte.mtb,
        func.sum(func.COALESCE(TblMeldungen.art_m, 0)).label('maennlich'),
        func.sum(func.COALESCE(TblMeldungen.art_w, 0)).label('weiblich'),
        func.sum(func.COALESCE(TblMeldungen.art_o, 0)).label('oothek'),
        func.sum(func.COALESCE(TblMeldungen.art_n, 0)).label('nymphe'),
        func.sum(func.COALESCE(TblMeldungen.art_f, 0)).label('andere'),
        func.sum(func.COALESCE(TblMeldungen.art_m, 0) +
                 func.COALESCE(TblMeldungen.art_w, 0) +
                 func.COALESCE(TblMeldungen.art_o, 0) +
                 func.COALESCE(TblMeldungen.art_n, 0) +
                 func.COALESCE(TblMeldungen.art_f, 0)).label('gesamt')
    ).join(TblMeldungen).filter(
        func.age(TblMeldungen.dat_meld, dateFrom) >= '0 days',
        func.age(TblMeldungen.dat_meld, dateTo) < '1 day'
    ).group_by(
        TblFundorte.mtb
    )
    results = query.all()

    idx = typeInput.index(art)

    for row in results[1:]:
        if row[idx] > 0 and row[0] is not None:
            try:
                mtb = int(row[0])
                dbanswers.append((mtb, row[idx]))
            except ValueError as e:
                print(e)

    xml = create_measure_sheet(dataset=dbanswers)
    return render_template(
        "statistics/stats-messtischblatt.html",
        user_id=session["user_id"],
        menu=list_of_stats,
        marker=marker,
        svg=xml,
        dateFrom=dateFrom,
        dateTo=dateTo
    )


def stats_bardiagram_datum(request, dbfields,
                           page, marker,
                           dateFrom, dateTo):
    "Calculate statistics by date"
    results = {0: '', 1: ''}
    for idx, dbfield in enumerate(dbfields):
        stm = f"""
           SELECT {dbfield} as Tag,
           count({dbfield}) as Anzahl
           FROM (select {dbfield}
                from meldungen
                where {dbfield} BETWEEN '{dateFrom}'::date
                                AND ('{dateTo}'::date)
                and (deleted IS NULL or deleted != 'f')) as filtered
           GROUP BY filtered.{dbfield}
           ORDER by Tag;
        """
        sql = text(stm)
        with db.engine.connect() as conn:
            result = conn.execute(sql)

        trace = {"x": [], "y": []}

        if result:
            for record in result:
                trace["x"].append(str(record[0]))
                trace["y"].append(record[1])
        results[idx] = trace

    return render_template(
        "statistics/" + page,
        menu=list_of_stats,
        marker=marker,
        user_id=session["user_id"],
        trace1=results[0],
        trace2=results[1],
        dateFrom=dateFrom,
        dateTo=dateTo
    )


def stats_geschlecht(request=None):
    """Count sum of all kategories"""

    start_date, end_date = get_date_interval(request)
    stm = f"""
      select sum(art_m) as "Männchen"
            , sum(art_w) as "Weibchen"
            , sum(art_n) as "Nymphen"
            , sum(art_o) as "Ootheken"
            , sum(art_f) as "Andere"
      from (select art_m, art_w, art_n, art_o, art_f
            from meldungen
            where dat_fund_von >= to_date('{start_date}', 'YYYY-MM-DD')
            and dat_fund_von <= to_date('{end_date}', 'YYYY-MM-DD')
            and deleted is NULL or 'f') as filtered;"""

    sql = text(stm)

    with db.engine.connect() as conn:
        result = conn.execute(sql)
        res = []
        for row in result:
            row = row._mapping
            res = dict((name, val) for name, val in row.items())

    return render_template(
        "statistics/stats-geschlecht.html",
        menu=list_of_stats,
        user_id=session["user_id"],
        marker="geschlecht",
        dateFrom=start_date,
        dateTo=end_date,
        values=res,
    )


def stats_amt(request, dateFrom, dateTo, marker):
    "Statistics pro Gemeinden (AGS))"

    gem = request.form.get('gemeinde', '000')
    gem.split(' ')[0]
    typeInput = ['amt', 'maennlich', 'weiblich',
                 'oothek', 'nymphe', 'andere', 'all']
    conn = db.session
    dbanswers = ['', 0, 0, 0, 0, 0, 0]
    search = f"{gem}%"
    fehler = False

    query = conn.query(
        TblFundorte.amt,
        func.sum(func.COALESCE(TblMeldungen.art_m, 0)).label('maennlich'),
        func.sum(func.COALESCE(TblMeldungen.art_w, 0)).label('weiblich'),
        func.sum(func.COALESCE(TblMeldungen.art_o, 0)).label('oothek'),
        func.sum(func.COALESCE(TblMeldungen.art_n, 0)).label('nymphe'),
        func.sum(func.COALESCE(TblMeldungen.art_f, 0)).label('andere'),
        func.sum(func.COALESCE(TblMeldungen.art_m, 0) +
                 func.COALESCE(TblMeldungen.art_w, 0) +
                 func.COALESCE(TblMeldungen.art_o, 0) +
                 func.COALESCE(TblMeldungen.art_n, 0) +
                 func.COALESCE(TblMeldungen.art_f, 0)).label('gesamt')
    ).join(TblMeldungen).filter(
        func.age(TblMeldungen.dat_meld, dateFrom) >= '0 days',
        func.age(TblMeldungen.dat_meld, dateTo) < '1 day',

    ).filter(
        TblFundorte.amt.like(search)
    ).group_by(
        TblFundorte.amt
    )
    results = query.all()

    if results:
        gemeinde = results[0][0]
    else:
        gemeinde = ""
        fehler = True
    for row in results:
        dbanswers[0] = row[0]
        for idx, val in enumerate(typeInput):
            if idx > 0:
                try:
                    dbanswers[idx] += row[idx]
                except ValueError as e:
                    print(e)

    return render_template(
        "statistics/stats-gemeinde.html",
        user_id=session["user_id"],
        menu=list_of_stats,
        marker=marker,
        result=dbanswers,
        dateFrom=dateFrom,
        dateTo=dateTo,
        gemeinde=gemeinde,
        fehler=fehler
    )


def stats_laender(request, dateFrom, dateTo, marker):
    "Statistics pro Bundesland (AGS))"

    conn = db.session

    # Abfrage erstellen
    query = conn.query(
        func.substring(TblFundorte.amt, 1, 2).label('amt_group'),
        func.sum(func.COALESCE(TblMeldungen.art_m, 0)).label('maennlich'),
        func.sum(func.COALESCE(TblMeldungen.art_w, 0)).label('weiblich'),
        func.sum(func.COALESCE(TblMeldungen.art_o, 0)).label('oothek'),
        func.sum(func.COALESCE(TblMeldungen.art_n, 0)).label('nymphe'),
        func.sum(func.COALESCE(TblMeldungen.art_f, 0)).label('andere'),
        func.sum(func.COALESCE(TblMeldungen.art_m, 0) +
                 func.COALESCE(TblMeldungen.art_w, 0) +
                 func.COALESCE(TblMeldungen.art_o, 0) +
                 func.COALESCE(TblMeldungen.art_n, 0) +
                 func.COALESCE(TblMeldungen.art_f, 0)).label('gesamt')
    ).join(TblMeldungen).filter(
        TblMeldungen.dat_meld >= dateFrom,
        TblMeldungen.dat_meld <= dateTo,
        or_(TblMeldungen.deleted.is_(None), TblMeldungen.deleted == False)
    ).group_by(
        func.substring(TblFundorte.amt, 1, 2)
    )

    # Die Abfrage ausführen
    results = query.all()

    laender = {'01': 'Schleswig-Holstein',
               '02': 'Freie und Hansestadt Hamburg',
               '03': 'Niedersachsen',
               '04': 'Freie Hansestadt Bremen',
               '05': 'Nordrhein-Westfalen',
               '06': 'Hessen',
               '07': 'Rheinland-Pfalz',
               '08': 'Baden-Württemberg',
               '09': 'Freistaat Bayern',
               '10': 'Saarland⁠',
               '11': 'Berlin⁠',
               '12': 'Brandenburg',
               '13': 'Mecklenburg-Vorpommern',
               '14': 'Freistaat Sachsen',
               '15': 'Sachsen-Anhalt',
               '16': 'Freistaat Thüringen'
               }

    # Ergebnisse in einem Dictionary speichern
    result_dict = defaultdict(dict)
    for result in results:
        if result.amt_group:
            result_dict[
                f"{result.amt_group} --  {laender[result.amt_group]}"
            ] = {
                'maennlich': result.maennlich,
                'weiblich': result.weiblich,
                'oothek': result.oothek,
                'nymphe': result.nymphe,
                'andere': result.andere,
                'gesamt': result.gesamt
            }
    return render_template(
        "statistics/stats-laender.html",
        user_id=session["user_id"],
        menu=list_of_stats,
        marker=marker,
        result=result_dict,
        dateFrom=dateFrom,
        dateTo=dateTo
    )


def stats_brb(request, dateFrom, dateTo, marker):
    "Statistics pro Landkreis Brandenburg (AGS))"

    conn = db.session

    # Abfrage erstellen
    query = conn.query(
        func.substring(TblFundorte.amt, 1, 5).label('amt_group'),
        func.sum(func.COALESCE(TblMeldungen.art_m, 0)).label('maennlich'),
        func.sum(func.COALESCE(TblMeldungen.art_w, 0)).label('weiblich'),
        func.sum(func.COALESCE(TblMeldungen.art_o, 0)).label('oothek'),
        func.sum(func.COALESCE(TblMeldungen.art_n, 0)).label('nymphe'),
        func.sum(func.COALESCE(TblMeldungen.art_f, 0)).label('andere'),
        func.sum(func.COALESCE(TblMeldungen.art_m, 0) +
                 func.COALESCE(TblMeldungen.art_w, 0) +
                 func.COALESCE(TblMeldungen.art_o, 0) +
                 func.COALESCE(TblMeldungen.art_n, 0) +
                 func.COALESCE(TblMeldungen.art_f, 0)).label('gesamt')
    ).join(TblMeldungen).filter(
        TblMeldungen.dat_meld >= dateFrom,
        TblMeldungen.dat_meld <= dateTo,
        func.substring(TblFundorte.amt, 1, 2) == '12',
        or_(TblMeldungen.deleted.is_(None), TblMeldungen.deleted == False)
    ).group_by(
        func.substring(TblFundorte.amt, 1, 5)
    )

    # Die Abfrage ausführen
    results = query.all()

    laender = {'12060': 'Landkreis Barnim',
               '12061': 'Landkreis Dahme-Spreewald',
               '12062': 'Landkreis Elbe-Elster',
               '12063': 'Landkreis Havelland',
               '12064': 'Landkreis Märkisch-Oderland',
               '12065': 'Landkreis Oberhavel',
               '12066': 'Landkreis Oberspreewald-Lausitz',
               '12067': 'Landkreis Oder-Spree',
               '12068': 'Landkreis Ostprignitz-Ruppin',
               '12069': 'Landkreis Potsdam-Mittelmark',
               '12070': 'Landkreis Prignitz',
               '12071': 'Landkreis Spree-Neiße',
               '12072': 'Landkreis Teltow-Fläming',
               '12073': 'Landkreis Uckermark',
               '12051': 'Brandenburg an der Havel',
               '12052': 'Cottbus',
               '12053': 'Frankfurt (Oder)',
               '12054': 'Potsdam'
               }

    # Ergebnisse in einem Dictionary speichern
    result_dict = defaultdict(dict)
    for result in results:
        if result.amt_group:
            result_dict[
                f"{result.amt_group} -- {laender[result.amt_group]}"
            ] = {
                'maennlich': result.maennlich,
                'weiblich': result.weiblich,
                'oothek': result.oothek,
                'nymphe': result.nymphe,
                'andere': result.andere,
                'gesamt': result.gesamt
            }

    return render_template(
        "statistics/stats-brb.html",
        user_id=session["user_id"],
        menu=list_of_stats,
        marker=marker,
        result=result_dict,
        dateFrom=dateFrom,
        dateTo=dateTo
    )


def stats_berlin(request, dateFrom, dateTo, marker):
    "Statistics Berlin nach Stadtbezirken (AGS))"

    conn = db.session

    query = conn.query(
        func.substring(TblFundorte.amt, 1, 8).label('amt_group'),
        func.sum(func.COALESCE(TblMeldungen.art_m, 0)).label('maennlich'),
        func.sum(func.COALESCE(TblMeldungen.art_w, 0)).label('weiblich'),
        func.sum(func.COALESCE(TblMeldungen.art_o, 0)).label('oothek'),
        func.sum(func.COALESCE(TblMeldungen.art_n, 0)).label('nymphe'),
        func.sum(func.COALESCE(TblMeldungen.art_f, 0)).label('andere'),
        func.sum(func.COALESCE(TblMeldungen.art_m, 0) +
                 func.COALESCE(TblMeldungen.art_w, 0) +
                 func.COALESCE(TblMeldungen.art_o, 0) +
                 func.COALESCE(TblMeldungen.art_n, 0) +
                 func.COALESCE(TblMeldungen.art_f, 0)).label('gesamt')
    ).join(TblMeldungen).filter(
        TblMeldungen.dat_meld >= dateFrom,
        TblMeldungen.dat_meld <= dateTo,
        func.substring(TblFundorte.amt, 1, 2) == '11',
        or_(TblMeldungen.deleted.is_(None), TblMeldungen.deleted == False)
    ).group_by(
        func.substring(TblFundorte.amt, 1, 8)
    )

    # Die Abfrage ausführen
    results = query.all()

    laender = {'11000000': 'Berlin (allgemein)',
               '11000001': 'Mitte',
               '11000002': 'Friedrichshain-Kreuzberg',
               '11000003': 'Pankow',
               '11000004': 'Charlottenburg-Wilmersdorf',
               '11000005': 'Spandau',
               '11000006': 'Steglitz-Zehlendorf',
               '11000007': 'Tempelhof-Schöneberg',
               '11000008': 'Neukölln',
               '11000009': 'Treptow-Köpenick',
               '11000010': 'Marzahn-Hellersdorf',
               '11000011': 'Lichtenberg',
               '11000012': 'Reinickendorf'
               }

    # Ergebnisse in einem Dictionary speichern
    result_dict = defaultdict(dict)
    for result in results:
        if result.amt_group:
            result_dict[
                f"{result.amt_group} -- {laender[result.amt_group]}"
            ] = {
                'maennlich': result.maennlich,
                'weiblich': result.weiblich,
                'oothek': result.oothek,
                'nymphe': result.nymphe,
                'andere': result.andere,
                'gesamt': result.gesamt
            }

    return render_template(
        "statistics/stats-brb.html",
        user_id=session["user_id"],
        menu=list_of_stats,
        marker=marker,
        result=result_dict,
        dateFrom=dateFrom,
        dateTo=dateTo
    )


def stats_gesamt(request, dateFrom, dateTo, marker):
    "Get sum for  Bundesland, Landkreis/Stadtbezirk and Amt"

    result_dict = {
        '12': ['Brandenburg', '', '', 0, []],
        '12060': ['', 'Landkreis Barnim', '', 0, []],
        '12061': ['', 'Landkreis Dahme-Spreewald', '', 0, []],
        '12062': ['', 'Landkreis Elbe-Elster', '', 0, []],
        '12063': ['', 'Landkreis Havelland', '', 0, []],
        '12064': ['', 'Landkreis Märkisch-Oderland', '', 0, []],
        '12065': ['', 'Landkreis Oberhavel', '', 0, []],
        '12066': ['', 'Landkreis Oberspreewald-Lausitz', '', 0, []],
        '12067': ['', 'Landkreis Oder-Spree', '', 0, []],
        '12068': ['', 'Landkreis Ostprignitz-Ruppin', '', 0, []],
        '12069': ['', 'Landkreis Potsdam-Mittelmark', '', 0, []],
        '12070': ['', 'Landkreis Prignitz', '', 0, []],
        '12071': ['', 'Landkreis Spree-Neiße', '', 0, []],
        '12072': ['', 'Landkreis Teltow-Fläming', '', 0, []],
        '12073': ['', 'Landkreis Uckermark', '', 0, []],
        '12051': ['', 'Brandenburg an der Havel', '', 0, []],
        '12052': ['', 'Cottbus', '', 0, []],
        '12053': ['', 'Frankfurt (Oder)', '', 0, []],
        '12054': ['', 'Potsdam', '', 0, []],
        '11': ['Berlin⁠', '', '', 0, []],
        '13': ['Mecklenburg-Vorpommern', '', '', 0, []],
        '14': ['Freistaat Sachsen', '', '',  0, []],
        '15': ['Sachsen-Anhalt', '', '', 0, []],
        '16': ['Freistaat Thüringen', '', '',  0, []],
        '01': ['Schleswig-Holstein', '', '',  0, []],
        '02': ['Freie und Hansestadt Hamburg', '', '', 0, []],
        '03': ['Niedersachsen', '', '',  0, []],
        '04': ['Freie Hansestadt Bremen', '', '', 0, []],
        '05': ['Nordrhein-Westfalen', '', '', 0, []],
        '06': ['Hessen', '', '', 0, []],
        '07': ['Rheinland-Pfalz', '', '', 0, []],
        '08': ['Baden-Württemberg', '', '', 0, []],
        '09': ['Freistaat Bayern', '', '', 0, []],
        '10': ['Saarland⁠', '', '', 0, []],
    }

    conn = db.session

    query = conn.query(
        TblFundorte.amt,
        func.sum(func.COALESCE(TblMeldungen.art_m, 0) +
                 func.COALESCE(TblMeldungen.art_w, 0) +
                 func.COALESCE(TblMeldungen.art_o, 0) +
                 func.COALESCE(TblMeldungen.art_n, 0) +
                 func.COALESCE(TblMeldungen.art_f, 0)).label('gesamt')
    ).join(TblMeldungen).filter(
        TblMeldungen.dat_meld >= dateFrom,
        TblMeldungen.dat_meld <= dateTo,
        or_(TblMeldungen.deleted.is_(None), TblMeldungen.deleted == False)
    ).group_by(
        TblFundorte.amt)

    # Die Abfrage ausführen
    results = query.all()
    keys = list(result_dict.keys())
    for result in results:
        try:
            if result[0]:
                # Länder
                result_dict[f"{result[0][:2]}"][3] += result[1]
                # Landkreise für Brandenburg
                if str(f"{result[0][:5]}") in keys:
                    result_dict[f"{result[0][:5]}"][3] += result[1]
                # Berlin
                if str(f"{result[0]}") in keys:
                    result_dict[f"{result[0]}"][3] += result[1]
                # Berliner Stadtbezirke
                if result[0].startswith('11'):
                    id, gemeinde = result[0].split(' -- ')
                    result_dict['11'][4].append(
                        [id, '', '', gemeinde, result[1]])

                # Ämter
                if result[0].startswith('12'):
                    id, gemeinde = result[0].split(' -- ')
                    result_dict[f"{result[0][:5]}"][4].append(
                        [id, '', '', gemeinde, result[1]])
        except:
            print(result)
                    
    return render_template(
        "statistics/stats-table-all.html",
        user_id=session["user_id"],
        menu=list_of_stats,
        marker=marker,
        result=result_dict,
        dateFrom=dateFrom,
        dateTo=dateTo
    )
