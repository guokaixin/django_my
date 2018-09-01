from __future__ import absolute_import
from rest_framework.throttling import UserRateThrottle


class UserPostRateThrottle(UserRateThrottle):
    scope = 'user'
    THROTTLE_RATES = {'user': '5/min'}

    def get_cache_key(self, request, view):
        if request.user.is_authenticated() and request.method in ['POST', 'PUT', 'PATCH']:
            ident = '%s_%s_%s' % (
                    request.user.pk,
                    request.method,
                    view.get_view_name(),
                    )
            ident = ident.replace(' ', '')
            return self.cache_format % {
                'scope': self.scope,
                'ident': ident,
                }
        else:
            return None

    def allow_request(self, request, view):
        if request.method in ['POST', 'PUT', 'PATCH']:
            return super(UserPostRateThrottle, self).allow_request(request, view)
        else:
            return True
