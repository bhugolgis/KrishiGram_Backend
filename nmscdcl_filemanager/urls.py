from django.urls import path, include
from django.conf import settings
from django.utils.module_loading import import_string
from . import views as file_views

urlpatterns=[
	path("GetUploadedShapeFile",file_views.GetUploadedShapeFile.as_view(),name="GetUploadedShapeFile"),
	path("UploadShapeFile",file_views.UploadShapeFile.as_view(),name="UploadShapeFile"),
	# path("UpdateServerApi/<int:id>/",file_views.UpdateServerApi.as_view(),name="UpdateServerApi"),
	# path("GetServer/<int:id>/",file_views.GetServer.as_view(),name="GetServer"),
	path("DeleteShapeFolder/<str:filename>/",file_views.DeleteShapeFolder.as_view(),name="DeleteShapeFolder"),
	path("UploadGeojson/<int:workspace_id>/<int:datastore_id>/",file_views.UploadGeojson.as_view(),name="UploadGeojson"),
	path("LayerCSV/<int:layer_id>/",file_views.LayerCSV.as_view(),name="LayerCSV"),
	path("LayerGeojson/<int:layer_id>/",file_views.LayerGeojson.as_view(),name="LayerGeojson"),
	# Export to postgis
	path("export-to-postgis",file_views.ExportToPostgis.as_view(),name="ExportToPostgis"),
	path("get-exported-layers-list",file_views.GetExportedLayersList.as_view(),name="GetExportedLayersList"),
    
	path("Get-Geotiff-List",file_views.GetGeotiffList.as_view(),name="GetExportedLayersList"),
]