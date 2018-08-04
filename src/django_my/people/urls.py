from django.conf.urls import url
from django.conf.urls import include

from rest_framework import routers
from .viewsets import CustomUserViewSet
from .viewsets import user_signin
from .viewsets import user_email_signin
from .viewsets import user_reset_password_email

router = routers.DefaultRouter()

router.register('user', CustomUserViewSet, base_name='UserViewSet')

view_urls = [
    url(r'^user/signin/', user_signin, name='CustomUserSigninView'),
    url(r'^user/email_signin/', user_email_signin, name='user_email_signin'),
    url(r'^user/send_reset_email/', user_reset_password_email, name='CustomUserResetPasswordEmailView'),

]

urlpatterns = [
    url(r'', include(view_urls)),
    url(r'', include(router.urls,)),
    ]

