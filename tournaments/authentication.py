from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions
from .models import User
from .utils import decode_access_token


class JWTAuthentication(BaseAuthentication):
    keyword = b'Bearer'

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth:
            return None
        if auth[0] != self.keyword:
            return None
        if len(auth) != 2:
            raise exceptions.AuthenticationFailed('Invalid authorization header')
        token = auth[1].decode('utf-8')
        payload = decode_access_token(token)
        try:
            user = User.objects.get(pk=int(payload['sub']))
        except (User.DoesNotExist, KeyError, ValueError) as exc:
            raise exceptions.AuthenticationFailed('Користувача не знайдено.') from exc
        return (user, token)
