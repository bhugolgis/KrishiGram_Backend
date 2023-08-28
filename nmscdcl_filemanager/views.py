from django.shortcuts import render
from rest_framework import generics,permissions,status,mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser,MultiPartParser
from .models import ShapeFiles
import os
from django.conf import settings
import shutil
import zipfile
import json
from .models import *
from nmscdcl_services.models import Datastore
from nmscdcl_services.utils import error_simplifier
from .serializers import UploadShapeSerializer,GetShapeFileSerializer,storeshapefilePathSerializer,\
ExportGeojsonToPostgis,ExportToPostgisSerializer,GetExportToPostgisSerializer
from osgeo import gdal
from django.core.files.storage import default_storage
from KrushiGram.settings import FILEMANAGER_DIRECTORY
from .core import FileManager
from . import core
from dbfread import DBF
from nmscdcl_services.data_processing import DataProcessing
from django.http import HttpResponse
from nmscdcl_services.models import Layer
import csv
import glob
from pathlib import Path
from krishi_auth.core_auth import IsAdmin,IsView,IsViewAndNonSpatialEdit,IsViewAndEdit
from nmscdcl_services import geographic_servers
from KrushiGram.settings import MODE_CREATE,MODE_OVERWRITE

# Create your views here.

#Export Shape file
class ExportToPostgis(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=ExportToPostgisSerializer
	parser_classes=[MultiPartParser]

	def post(self,request,*args,**kwargs):
		if request.FILES:
			request.data["fileName"] = request.FILES["file"].name.split(".")[0]
		if request.data["fileName"].endswith(("shp","SHP")):
			request.data["fileName"] = request.data["fileName"].split(".")[0]
		serializer=self.get_serializer(data=request.data)
		if serializer.is_valid():
			fileName = serializer.validated_data["fileName"]
			fm=core.get_instance()
			shp_path=os.path.join(fm.location,fileName,f'{fileName}.shp')
			if not Path(shp_path).is_file():
				return Response({
					"message":"there is no shapefile named {val} in the shapefiles directory".format(val=fileName),
					"status":"error"
					},status=status.HTTP_400_BAD_REQUEST)

			workspace = serializer.validated_data["datastore"].workspace

			gs=geographic_servers.get_instance().get_server_by_id(workspace.server.id)
			layer_data={**serializer.validated_data, "shp_path":shp_path, "userName":request.user.name}

			try:
				exported_data = gs.exportShpToPostgis(layer_data)

				if isinstance(exported_data , dict):
					return Response(exported_data,status = status.HTTP_400_BAD_REQUEST)
			except Exception as e:
				return Response({
	            "message":"exception occured while exporting layer to postgis",
	            "status":"error",
	            "error":str(e)
	            },status = status.HTTP_400_BAD_REQUEST)
			data=serializer.save(created_by = request.user, layerName = serializer.validated_data["name"].lower())

			serialized_data=GetExportToPostgisSerializer(data).data
			return Response({
				"message":"layer exported successfully",
				"status":"success",
				"data":serialized_data,
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"error occurred while exporting data to postgis",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)



class GetExportedLayersList(APIView):
	permission_classes=(IsAdmin,)

	def get(self, request, *args, **kwargs):
		exported_layers = ExportHistory.objects.filter(is_published = False)

		data=GetExportToPostgisSerializer(exported_layers,many=True).data

		if data:
			return Response({
			"message":"exported layers data fetched successfully",
			"status":"success",
			"data":data
			})
		return Response({
			"message":"there is no exported layers data available",
			"status":"error",
			"data":data
			})



class GetGeotiffList(APIView):
	permission_classes =(IsAdmin,)

	def get(self , request , *args , **kwargs):
		file_path = "D:\\tiff_data\\*tif"
		file_list = glob.glob(file_path)

		return Response ({"status" : "Success" ,
		    				"data" : file_list} , status= 200)

class UploadShapeFile(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=UploadShapeSerializer
	parser_classes = [MultiPartParser]

	def get_new_media_path(self, media_path):
		index = 1
		while os.path.exists(f"{media_path}_{index}"):
			index += 1
		return f"{media_path}_{index}"

	def post(self, request, format=None, *args, **kwargs):

		if 'file' not in request.FILES:
			return Response({
			"message":"No shape file was uploaded",
			"status":"error"
			},status=status.HTTP_400_BAD_REQUEST)

		zip_file = request.FILES['file']
		zip_filename = zip_file.name
		if not zip_filename.endswith('.zip'):
			return Response({
			"message":f"{zip_filename} - uploaded file was not a zip file",
			"status":"error"
			},status=status.HTTP_400_BAD_REQUEST)
		media_path = os.path.join(settings.FILEMANAGER_DIRECTORY, zip_filename[:-4])

		serializer = self.get_serializer(data = request.data)
		if serializer.is_valid():

			choice = serializer.validated_data["choice"]

			# Check if media folder for extracted files already exists
			while os.path.exists(media_path):
				if choice == MODE_OVERWRITE:
					shutil.rmtree(media_path)
				elif choice == MODE_CREATE:
					media_path = self.get_new_media_path(media_path)
				else:
					return Response({
						'message': 'Invalid choice. Please select overwrite or create',
						'status': 'error'
						},status=status.HTTP_400_BAD_REQUEST)

			# Extract the ZIP file to the media folder
			with zipfile.ZipFile(zip_file, 'r') as zip_ref:
				zip_ref.extractall(media_path)
			folder_name = media_path.split('\\')[-1]

			store_serializer = storeshapefilePathSerializer(data = {'fileName':folder_name})
			if store_serializer.is_valid():
				store_serializer.save(user = request.user)

			is_export = serializer.validated_data["export"]

			if is_export:
				view = ExportToPostgis.as_view()

				return view(request._request,*args,**kwargs)

			return Response({
				'message': f'{zip_filename} uploaded and extracted successfully.',
				'status':'success'
				})
		else:
			error = error_simplifier(serializer.errors)
			return Response({
				"message":"error occurred while uploading shapefile",
				"status":"error",
				"error":error
				},status=status.HTTP_400_BAD_REQUEST)




class GetUploadedShapeFile(APIView):
	permission_classes=(IsAdmin,)
	def get(self, request):
		try:
			instance = ShapeFiles.objects.all()
		except ShapeFiles.DoesNotExist as e:
			return Response({"message":'No data found',
				"status": "error"},status=status.HTTP_400_BAD_REQUEST)

		serializer = GetShapeFileSerializer(instance , many = True).data
		return Response({'message': 'data fetched successfully',
			'status':'success',
			'data': serializer})



class DeleteShapeFolder(generics.DestroyAPIView):
	# permission_classes=(permissions.IsAuthenticated,)
	permission_classes=(IsAdmin,)

	def delete(self, request, filename, format=None):
		media_path = os.path.join(settings.MEDIA_ROOT, 'shapefiles', filename)
		filename= media_path.split('\\')[-1]
		if os.path.exists(media_path):
			shutil.rmtree(media_path)
			ShapeFiles.objects.filter(fileName=filename).delete()
			return Response({
				'message': 'Folder deleted successfully.',
				'status': 'success' , })
		else:
			return Response({
				'message': f'{filename} - This folder not found.',
				'status': 'error'},
			 	status=status.HTTP_400_BAD_REQUEST)



# class UploadGeojson(generics.GenericAPIView):
# 	# permission_classes=(permissions.IsAuthenticated,)
# 	serializer_class=UploadShapeSerializer
# 	parser_classes=[MultiPartParser]

# 	def post(self,request,*args,**kwargs):
# 		json_file = request.FILES['shape_file']
# 		print(json_file.name)
# 		# media_path = os.path.join(settings.MEDIA_ROOT, 'shapefiles', json_file.name[:-8])
# 		folder_path = os.path.join(settings.MEDIA_ROOT, 'shapefiles',json_file.name[:-8])
# 		file_path= os.path.join(settings.MEDIA_ROOT, 'shapefiles',json_file.name)

# 		path=default_storage.save(file_path,json_file)

# 		# if path:
# 		# 	# Open the GeoJSON
# 		# 	src = gdal.OpenEx(file_path)
# 		# 	# Translate the vector data into Shapefile
# 		# 	dest = gdal.VectorTranslate(folder_path, src, format='ESRI Shapefile')
# 		# 	src=None

# 		print(default_storage.listdir(folder_path))
# 		walk=os.walk(folder_path)
# 		print(next(walk),"walking")

# 		print(default_storage.listdir(os.path.join(settings.MEDIA_ROOT, 'shapefiles')))

# 		# print(default_storage.listdir(file_path))
# 		default_storage.delete(file_path)

# 		if 1:
# 			return Response({
# 				"message":"successfully saved geojson file"
# 				})


# 		# return Response({
# 		# 	"message":"successfully"
# 		# 	})


class UploadGeojson(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=ExportGeojsonToPostgis
	parser_classes=[MultiPartParser]

	def post(self,request,workspace_id,datastore_id,*args,**kwargs):
		json_file = request.FILES['file']
		filemanager=FileManager()

		if json_file.name.split(".")[1] != "geojson":
			return Response({
				"message":"The uploaded file is not a geojson file",
				"status":"error"
				},status=status.HTTP_400_BAD_REQUEST)

		shp=filemanager.geojson_to_shape(json_file)

		if isinstance(shp,dict):
			return Response(shp,status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		view=ExportToPostgis.as_view()

		return Response({
			"message":"geojson uploaded and converted to shapefile successfully",
			"status":"success"
			})


		# return view(request._request,workspace_id,datastore_id,*args,**kwargs)



class LayerCSV(APIView):
	permission_classes=(IsAdmin,IsViewAndEdit,IsViewAndNonSpatialEdit)
	def get(self, request, layer_id):

		try:
			layer = Layer.objects.get(pk = layer_id)
		except Layer.DoesNotExist as e:
			return Response({
				"message":"There is no Layer data for id %s"%(layer_id),
				"status":"error"
				},status=status.HTTP_400_BAD_REQUEST)
		processed_data = DataProcessing(layer.datastore)
		attributes = processed_data.GetAttributeDataForCsv(layer.name)

		if isinstance(attributes,dict):
			return Response(attributes,status = status.HTTP_400_BAD_REQUEST)

		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = f'attachment; filename="{layer.name}.csv"'

		data,columns,geometry_field = attributes

		writer = csv.writer(response)

		writer.writerow([col for col in columns])

		for row in data:
			writer.writerow([value for key, value in row.items() if key != geometry_field])

		return response


class LayerGeojson(APIView):
	permission_classes=(IsAdmin,IsViewAndEdit,IsViewAndNonSpatialEdit)

	def get(self , request , layer_id):

		try:
			layer = Layer.objects.get(pk = layer_id)
		except Layer.DoesNotExist as e:
			return Response({
				"message":"There is no Layer data for id %s"%(layer_id),
				"status":"error"
				},status=status.HTTP_400_BAD_REQUEST)

		processed_data = DataProcessing(layer.datastore)
		data = processed_data.GetAttributeDataForGeoJson(layer.name)

		if isinstance(data,dict):
			return Response(data,status = status.HTTP_400_BAD_REQUEST)

		response = HttpResponse(json.dumps(data), content_type='application/json')
		response['Content-Disposition'] = f'attachment; filename={layer.name}.geojson'

		return response