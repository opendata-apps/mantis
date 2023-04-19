from pyramid.view import view_config
#from pyramid.response import Response

'''
@view_config(route_name='empfangen_mit_get',
             renderer='mantis:templates/handle-data-with-get.jinja2')
def get_params(request):

    matchdict = request.matchdict
#    parameter = request.params.get('gesendet')
    #print(parameter)

    return {'parameter': matchdict['gesendet']}


@view_config(route_name='empfangen_mit_querystring',
             renderer='mantis:templates/handle-data-with-querystring.jinja2')
def get_query_string(request):
    "/senden-mit/querystring/wert?gesendet=HalloBallo"

    parameter = request.GET.get('gesendet')

    return {'parameter': parameter}

@view_config(route_name='empfangen_mit_post',
             renderer='mantis:templates/handle-data-with-post.jinja2')
def get_formdata(request):
    "/senden-mit/formular/nummer1"
    
    geliefert = request.POST.get("text", "Nix eingegeben!")
    #matchdict = request.matchdict
#    parameter = request.params.get('gesendet')
    #print(parameter)

    return {'parameter': geliefert}
'''
