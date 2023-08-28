"""KrushiGram URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path,include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from rest_framework import permissions
from django.conf.urls.static import static
# from app.views import SensorAPIView,SensorList, SensorDataView, Sensorpropertyviewer,SensorDataView, SensorDataCreateded, Sensorpropertyview,SensorListView,DumpExcelInsertxlsx,AdvisoryList,LayerList, LayerPost,SensorData,GeosensorExcelList,GeosensorList,SensorUploadView
# from app.views import SensorDataView



schema_view = get_schema_view(
   openapi.Info(
      title="KrishiGram API",
      default_version='v1',
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name ='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('Auth/' , include('krishi_auth.urls')),
    path ('Sensors/',include('sensors.urls')),
    path('services/',include('nmscdcl_services.urls')),
    path('filemanager/',include('nmscdcl_filemanager.urls')),
]
 

 
   

  
  
   
   
 





