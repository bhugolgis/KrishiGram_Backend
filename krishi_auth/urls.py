from django.urls import path, include
from django.conf import settings
from django.utils.module_loading import import_string
from . import views as auth_views
from rest_framework_simplejwt import views as jwt_views


LOGIN_VIEW=import_string(getattr(settings,"KRISHIGRAM_LOGIN_VIEW","krishi_auth.views.UserLogin"))
# LOGOUT_VIEW=import_string(getattr(settings,"NMSCDCL_LOGOUT_VIEW","nmscdcl_auth.views.UserLogout"))
REGISTER_VIEW=import_string(getattr(settings,"KRISHIGRAM_REGISTER_VIEW","krishi_auth.views.UserRegister"))

KRISHI_AUTH_BACKEND=getattr(settings,"KRISHI_AUTH_BACKEND","krishi_auth")

if KRISHI_AUTH_BACKEND == "krishi_auth":
	AUTH_PATHS=[
		path("login/",LOGIN_VIEW.as_view(),name="User_login"),
		path("logout/",jwt_views.TokenBlacklistView.as_view(),name="User_logout"),
		# path("logout/",auth_views.UserLogout.as_view(),name="User_logout"),
		path("register/",REGISTER_VIEW.as_view(),name="User_registeration")
	]
else:
	AUTH_PATHS=[path("",include(KRISHI_AUTH_BACKEND + ".urls"))]


urlpatterns=AUTH_PATHS + [
	# path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    # path("GetUserList/",auth_views.GetUserList.as_view(),name="GetUserList"),
    # path("GetUser/<int:user_id>/",auth_views.GetUser.as_view(),name="GetUser"),
    # path("GetGroup/",auth_views.GetGroup.as_view(),name="GetAllGroup"),
    # path("GetGroup/<str:group_name>/",auth_views.GetGroup.as_view(),name="GetOneGroup"),
]