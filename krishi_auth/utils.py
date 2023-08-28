"""
file for additional work or function needs to be done can be written here 
"""
from rest_framework_simplejwt.tokens  import RefreshToken

#JWT token Generator
def generate_token(user):
	refresh=RefreshToken.for_user(user)
	return {
		"refresh":str(refresh),
		"access":str(refresh.access_token)
	}