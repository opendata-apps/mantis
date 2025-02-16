import sqlalchemy as sa
import sqlalchemy.schema
import sqlalchemy.ext.compiler
import sqlalchemy.orm as orm
from sqlalchemy import text
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import types
from sqlalchemy.dialects.postgresql import TSVECTOR


meta = sa.MetaData()

Base = sa.orm.declarative_base()

class FullTextSearch(Base):
    __tablename__ = 'full_text_search'
    __table_args__ = {'schema': 'public'}

    meldungen_id = Column(Integer, primary_key=True)
    doc = Column(TSVECTOR)
  


class Drop(sa.schema.DDLElement):
    def __init__(self, name, schema):
        self.name = name
        self.schema = schema


class Create(sa.schema.DDLElement):
    def __init__(self, name, select, schema='public'):
        self.name = name
        self.schema = schema
        self.select = select

        sa.event.listen(meta, 'after_create', self)
        sa.event.listen(meta, 'before_drop', Drop(name, schema))


@sa.ext.compiler.compiles(Create)
def createGen(element, compiler, **kwargs):
    return 'CREATE MATERIALIZED VIEW {schema}."{name}" AS {select}'.format(
        name=element.name,
        schema=element.schema,
        select=compiler.sql_compiler.process(
            element.select,
            literal_binds=True
        ),
    )


@sa.ext.compiler.compiles(Drop)
def dropGen(element, compiler, **kwargs):
    # Den SQL-Ausdruck mit text() umschließen,
    # damit SQLAlchemy ihn korrekt behandelt
    sql = 'DROP MATERIALIZED VIEW {schema}."{name}"'.format(
        name=element.name,
        schema=element.schema
    )
    return text(sql)  # text() um den SQL-Ausdruck


def create_materialized_view(db, session=None):
    'create a materialized view for global search activities '
    if not db:
        db = sa.create_engine(
            'postgresql://mantis_user:mantis@localhost/mantis_tracker'
        )

        Session = orm.sessionmaker(bind=db)
        session = Session()

    #try:
        #session.execute(text('drop table melduser cascade'))
        #drop = Drop(name='full_text_search', schema='public')
        # You can call dropGen directly with the `drop` object
        #session.execute(dropGen(drop, None))
        #session.commit()
    #except Exception as e:
    #    print('Nix zu löschen')
    # Table Aliases
    meldungen = sa.table('meldungen', sa.column('id'), sa.column('bearb_id'),
                         sa.column('anm_melder'), sa.column('anm_bearbeiter'),
                         sa.column('fo_zuordnung'))
    fundorte = sa.table('fundorte', sa.column('id'),
                        sa.column('ort'), sa.column('strasse'),
                        sa.column('kreis'), sa.column('land'),
                        sa.column('amt'), sa.column('plz'),
                        sa.column('mtb'), sa.column('beschreibung'))
    beschreibung = sa.table('beschreibung', sa.column('id'),
                            sa.column('beschreibung'))
    melduser = sa.table('melduser', sa.column('id_meldung'),
                        sa.column('id_user'), sa.column('id_finder'))
    users = sa.table('users', sa.column('id'), sa.column('user_id'),
                     sa.column('user_name'), sa.column('user_kontakt'))
    # Full-Text Vector
    fts_vector = sa.func.to_tsvector(
        text("'german'"),
        sa.func.coalesce(meldungen.c.bearb_id, '') + ' ' +
        sa.func.coalesce(meldungen.c.anm_melder, '') + ' ' +
        sa.func.coalesce(meldungen.c.anm_bearbeiter, '') + ' ' +
        sa.func.coalesce(fundorte.c.ort, '') + ' ' +
        sa.func.coalesce(fundorte.c.strasse, '') + ' ' +
        sa.func.coalesce(fundorte.c.kreis, '') + ' ' +
        sa.func.coalesce(fundorte.c.land, '') + ' ' +
        sa.func.coalesce(fundorte.c.amt, '') + ' ' +
        sa.func.coalesce(fundorte.c.plz.cast(sa.String), '') + ' ' +
        sa.func.coalesce(fundorte.c.mtb, '') + ' ' +
        sa.func.coalesce(beschreibung.c.beschreibung, '') + ' ' +
        sa.func.coalesce(melduser.c.id_user.cast(sa.String), '') + ' ' +
        sa.func.coalesce(melduser.c.id_finder.cast(sa.String), '') + ' ' +
        sa.func.coalesce(users.c.user_id, '') + ' ' +
        sa.func.coalesce(users.c.user_name, '') + ' ' +
        sa.func.coalesce(users.c.user_kontakt, '')
    ).label('doc')

    # Query Definition
    view_query = sa.select(
        meldungen.c.id.label('meldungen_id'),
        fts_vector
    ).select_from(
        meldungen
        .outerjoin(fundorte, meldungen.c.fo_zuordnung == fundorte.c.id)
        .outerjoin(beschreibung, fundorte.c.beschreibung == beschreibung.c.id)
        .outerjoin(melduser, meldungen.c.id == melduser.c.id_meldung)
        .outerjoin(users, melduser.c.id_user == users.c.id)
    )

    # Create View
    Create(
        name='full_text_search',
        select=view_query
    )
    meta.create_all(bind=db, checkfirst=True)
    session.commit()
    session.close()

if __name__ == '__main__':
    #try:
    #    drop = Drop(name='full_text_search', schema='public')
    #    # You can call dropGen directly with the `drop` object
    #    session.execute(dropGen(drop, None))
    #    session.commit()
    #except:
    #    print('No view to drop.')
    create_materialized_view()
