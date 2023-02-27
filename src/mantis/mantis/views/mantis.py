from pyramid.view import view_config
from pyramid.response import Response
from sqlalchemy.exc import SQLAlchemyError

from .. import models


@view_config(route_name='faq', renderer='mantis:templates/faq.jinja2')
@view_config(route_name='impressum', renderer='mantis:templates/impressum.jinja2')
@view_config(route_name='about', renderer='mantis:templates/about.jinja2')
@view_config(route_name='mantis', renderer='mantis:templates/mantis.jinja2')
@view_config(route_name='reportAnIssue', renderer='mantis:templates/reportAnIssue.jinja2')
@view_config(route_name='newItem', renderer='mantis:templates/newItem.jinja2')
@view_config(route_name='admin', renderer='mantis:templates/admin.jinja2')
@view_config(route_name='home', renderer='mantis:templates/home.jinja2')
@view_config(route_name='einsendungen', renderer='mantis:templates/adminSubsites/submissions.jinja2')
@view_config(route_name='auswertungen', renderer='mantis:templates/adminSubsites/statistics.jinja2')
@view_config(route_name='benutzerverwaltung', renderer='mantis:templates/adminSubsites/userAdministration.jinja2')
@view_config(route_name='letzteAenderungen', renderer='mantis:templates/adminSubsites/log.jinja2')
def my_view(request):
    # try:
    #     query = request.dbsession.query(models.MyModel)
    #     one = query.filter(models.MyModel.name == 'one').one()
    # except SQLAlchemyError:
    #     return Response(db_err_msg, content_type='text/plain', status=500)
    return {'project': 'mantis'}


# db_err_msg = """\
# Pyramid is having a problem using your SQL database.  The problem
# might be caused by one of the following things:

# 1.  You may need to initialize your database tables with `alembic`.
#     Check your README.txt for descriptions and try to run it.

# 2.  Your database server may not be running.  Check that the
#     database server referred to by the "sqlalchemy.url" setting in
#     your "development.ini" file is running.

# After you fix the problem, please restart the Pyramid application to
# try it again.
# """
