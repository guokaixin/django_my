def get_client_agent(request):
    if 'HTTP_USER_AGENT' in request.META.keys():
        return request.META['HTTP_USER_AGENT']
    return u''


def get_client_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META.keys():
        client_ip = request.META['HTTP_X_FORWARDED_FOR']
    elif 'REMOTE_ADDR' in request.META.keys():
        client_ip = request.META['REMOTE_ADDR']
    else:
        client_ip = ""
    return client_ip
