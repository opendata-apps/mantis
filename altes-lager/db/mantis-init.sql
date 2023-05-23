-- -----------------------------------------------------
-- Table public.TblFundmeldungen
-- -----------------------------------------------------
DROP TABLE IF EXISTS TblFundmeldungen;

CREATE TABLE  TblFundmeldungen (
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
DROP TABLE IF EXISTS TblFundorte ;

CREATE TABLE  TblFundorte (
  id INT NOT NULL,
  plz INT NOT NULL,
  ort VARCHAR(100) NOT NULL,
  strasse VARCHAR(100) NULL,
  land INT NOT NULL,
  kreis INT NULL,
  beschreibung varchar(100) NULL,
  longitude VARCHAR(45) NOT NULL,
  latitude VARCHAR(45) NOT NULL,
  
  PRIMARY KEY (id));

-- -----------------------------------------------------
-- Table TblPlzOrt
-- -----------------------------------------------------
DROP TABLE IF EXISTS TblPlzOrt ;

CREATE TABLE  TblPlzOrt (
  osm_id INT NOT NULL,
  ags INT NULL,
  ort VARCHAR(100) NULL,
  plz VARCHAR(5) NULL,
  landkreis VARCHAR(100) NULL,
  bundesland VARCHAR(45) NULL,
  PRIMARY KEY (osm_id));


-- -----------------------------------------------------
-- Table TblTiere
-- -----------------------------------------------------
DROP TABLE IF EXISTS TblTiere ;

DROP type art;

create type art as enum
  ('m', 'w', 'n', 'o');

CREATE TABLE  TblTiere (
  id INT NOT NULL,
  art art NULL,
  PRIMARY KEY (id));


-- -----------------------------------------------------
-- Table TblmelderUndFinder
-- -----------------------------------------------------
DROP TABLE IF EXISTS TblmelderUndFinder;

CREATE TABLE  TblmelderUndFinder (
  id INT NOT NULL,
  user_id varchar(40) NOT NULL,
  finder VARCHAR(45) NULL,
  finder_mail VARCHAR(45) NULL,
  melder VARCHAR(45) NULL,
  melder_mail VARCHAR(45) NULL,
  PRIMARY KEY (id));

-- Table: public.tblplzort

-- DROP TABLE IF EXISTS public.tblplzort;

CREATE TABLE public.tblplzort
(
    osm integer NOT NULL,
    ags integer,
    ort character varying(100) COLLATE pg_catalog."default" NOT NULL,
    plz character varying(5) COLLATE pg_catalog."default" NOT NULL,
    landkreis character varying(100) COLLATE pg_catalog."default",
    bundesland character varying(45) COLLATE pg_catalog."default",
    CONSTRAINT osm_plz_pk PRIMARY KEY (osm, plz)
);

-- Table: public.tblplzort

-- DROP TABLE IF EXISTS public.tblplzort;

CREATE TABLE IF NOT EXISTS public.tblfundortbeschreibung
(
    id integer NOT NULL,
    beschreibung varchar(45) NOT NULL,
    CONSTRAINT fundort_pk PRIMARY KEY (id)
);

insert into tblfundortbeschreibung values (1,'Haus');
insert into tblfundortbeschreibung values (2,'Garten');
insert into tblfundortbeschreibung values (3,'Straßenrand');
