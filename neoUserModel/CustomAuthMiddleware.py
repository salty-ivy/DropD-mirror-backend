from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.authentication import JWTAuthentication
# from authUser.models import Users


@database_sync_to_async
def get_user(token_key):
	try:
		valid_token = JWTAuthentication().get_validated_token(token_key)
		token_user = JWTAuthentication().get_user(valid_token)
		
		return token_user
	except:
		return AnonymousUser()

class CustomTokenAuthMiddlewareStack(BaseMiddleware):
	def __init__(self,inner):
		super().__init__(inner)

	async def __call__(self,scope,receive,send):
		try:
			token_key = dict((x.split('=') for x in scope['query_string'].decode().split("&"))).get('token')
			# print(token_key)
		except ValueError:
			token_key = None
		scope['user'] = AnonymousUser() if token_key is None else await get_user(token_key)
		return await super().__call__(scope,receive,send)