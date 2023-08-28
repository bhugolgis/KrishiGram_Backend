

from django.contrib import admin
# from django.urls import path
from django.urls import path
from sensors.views import *
urlpatterns = [
    path('PostDevices/', PostDevicesAPIview.as_view(), name='PostDevices'),
    path('sensor_data/<str:device_id>/', SensorDataView.as_view(), name='sensor-data'),
  
    path('sensors/<str:sensor_type>/<str:start_date>/<str:end_date>/', SensorList.as_view(), name='sensor-list'),
    
    path('Advisory/upload-excel/',AdvisoryExcelInsertxlsx.as_view(), name='excel_upload'),
    
    path('advisory/<str:advisory_date>/', AdvisoryList.as_view()),

    path('Soilsensor/upload-json/', SensorUploadView.as_view(), name='sensor-upload'),
    path('WeatherInsertCSV/upload-excel/',WeatherInsertCSV.as_view(), name='excel_upload'),
   
    path('api/SoilSensor_Latestdata/<str:sensor_type>/<str:start_date>/<str:end_date>/',SoilSensorLatestdata.as_view(), name='SoilSensor-Latestdata'),
    path('SoilSensor-Latest-DataList/<str:device_id>/<str:start_date>/<str:end_date>/', SoilSensorLatestDataList.as_view(), name='SoilSensor-Latest-DataList'),
    path('sensor-data-Graph/<str:device_id>/<str:parameter>/<str:start_date>/<str:end_date>/', SensorGraphAPIView.as_view(), name='sensor-data-Graph'),

    path('DownloadExcelAllSoilSensor/<str:sensor_type>/<str:start_date>/<str:end_date>/', DownloadExcelAllSoilSensor.as_view(),name='Download-Excel-all-SoilSensor'),
    path('DownloadExcelBySoilSensorDeviceid/<str:sensor_type>/<str:start_date>/<str:end_date>/<device_id>/', DownloadExcelBySoilSensorDeviceid.as_view(),name='Download-Excel-SoilSensor-device_id')


 
    
]