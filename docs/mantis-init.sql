-- -----------------------------------------------------
-- Table TblFundmeldungen
-- -----------------------------------------------------
--DROP TABLE IF EXISTS TblFundmeldungen ;

CREATE TABLE IF NOT EXISTS TblFundmeldungen (
  id INT NOT NULL,
  funddatum DATE NOT NULL,
  meldedatum DATE NOT NULL,
  erstbearbeiter VARCHAR(45) NULL,
  bearbeitungsdatum DATE NULL,
  bildpfad VARCHAR(100) NOT NULL,
  PRIMARY KEY (id));


-- -----------------------------------------------------
-- Table TblFundorte
-- -----------------------------------------------------
--DROP TABLE IF EXISTS TblFundorte ;

CREATE TABLE IF NOT EXISTS TblFundorte (
  id INT NOT NULL,
  plz INT NOT NULL,
  ort VARCHAR(100) NOT NULL,
  strasse VARCHAR(100) NULL,
  land INT NOT NULL,
  kreis INT NULL,
  beschreibung VARCHAR(100) NULL,
  longitude VARCHAR(45) NOT NULL,
  latitude VARCHAR(45) NOT NULL,
  PRIMARY KEY (id));

-- -----------------------------------------------------
-- Table TblTiere
-- -----------------------------------------------------
--DROP TABLE IF EXISTS TblTiere ;
CREATE type art as enum ('m', 'w', 'n', 'o');

CREATE TABLE IF NOT EXISTS TblTiere (
  id INT NOT NULL,
  art art NULL,
  PRIMARY KEY (id));


-- -----------------------------------------------------
-- Table TblmelderUndFinder
-- -----------------------------------------------------
--DROP TABLE IF EXISTS TblmelderUndFinder ;

CREATE TABLE IF NOT EXISTS TblmelderUndFinder (
  id INT NOT NULL,
  user_id VARCHAR(40) NOT NULL,
  finder VARCHAR(45) NULL,
  finder_mail VARCHAR(45) NULL,
  melder VARCHAR(45) NULL,
  melder_mail VARCHAR(45) NULL,
  PRIMARY KEY (id));


CREATE TABLE IF NOT EXISTS tblplzort (
    osm_id integer NOT NULL,
    ags integer NULL,
    ort VARCHAR(100) NOT NULL,
    plz VARCHAR(5) NOT NULL,
    landkreis VARCHAR(100) Null,
    bundesland VARCHAR(45) Null,
    PRIMARY KEY (osm_id, plz));


CREATE TABLE IF NOT EXISTS tblfundortbeschreibung (
  id integer NOT NULL,
  beschreibung VARCHAR(45) NOT NULL,
  PRIMARY KEY (id)
);


insert into tblfundortbeschreibung values (1, 'Haus');
insert into tblfundortbeschreibung values (2, 'Garten');
insert into tblfundortbeschreibung values (3, 'Wald');
insert into tblfundortbeschreibung values (4, 'Straßenrand');