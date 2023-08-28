from django.shortcuts import render
from .models import Server,Workspace,Datastore,LayerGroup,Layer
from django.contrib.auth.models import Group
from .serializers import GetServerSerializer,PostServerSerializer,UpdateServerSerializer,\
GetWorkspaceSerializer,PostWorkspaceSerializer,UpdateWorkspaceSerializer,GetDatastoreSerializer,\
PostDatastoreSerializer,UpdateDatastoreSerializer,GetLayerSerializer,PostLayerSerializer,\
UpdateLayerSerializer,GetGsLayerSerializer,GetLayerGroupSerializer,PostLayerGroupSerializer,\
UpdateLayerGroupSerializer,GetShortLayerSerializer,GetVectorLayerSerializer,\
SpatialNonSpatialEditSerializer
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import permissions,mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import JSONParser,FormParser,MultiPartParser
from django.db.models import Q
from django.contrib.auth.models import Group
import os
from KrushiGram.settings import DEFAULT_DB_STRUCTURE
from .backend_geoserver import Geoserver
from . import geographic_servers
# from .backend_postgis import Introspect
from .data_processing import DataProcessing
from KrushiGram.settings import ACTION_INSERT,ACTION_UPDATE,\
ACTION_DELETE,EDIT_TYPE_SPATIAL,EDIT_TYPE_NON_SPATIAL,EDIT_TYPE_ALL

from krishi_auth.core_auth import IsAdmin,IsView,IsViewAndNonSpatialEdit,IsViewAndEdit

from .utils import *
from pathlib import Path
import json

# Create your views here.



"""
Server Api's
"""

class GetServerList(APIView):
	permission_classes=(IsAdmin,)
	
	def get(self,request,*args,**kwargs):
		server=Server.objects.all()
		data=GetServerSerializer(server,many=True).data

		if data:
			return Response({
			"message":"data fetched successfully",
			"status":"success",
			"data":data
			})
		return Response({
			"message":"there is no server data available",
			"status":"error",
			"data":data
			})


class PostServerApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=PostServerSerializer

	def post(self,request,*args,**kwargs):
		serializer=self.get_serializer(data=request.data)
		if serializer.is_valid():
			server=serializer.save()
			data=GetServerSerializer(server,context=self.get_serializer_context()).data
			return Response({
				"message":"Server data saved successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"Server data not saved",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)


class UpdateServerApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)	
	serializer_class=UpdateServerSerializer

	def put(self,request,id,*args,**kwargs):
		try:
			instance=Server.objects.get(pk=id)
		except Server.DoesNotExist as e:
			return Response({
				"message":"server with id %s does not exists"%(id),
				"status":"error"
				})
		serializer=self.get_serializer(data=request.data,instance=instance)

		if serializer.is_valid():
			server=serializer.save()
			data=GetServerSerializer(server,context=self.get_serializer_context()).data

			return Response({
				"message":"server data updated successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"server data not updated",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)
	def patch(self,request,id,*args,**kwargs):
		try:
			instance=Server.objects.get(pk=id)
		except Server.DoesNotExist as e:
			return Response({
				"message":"server with id %s does not exists"%(id),
				"status":"error"
				})
		serializer=self.get_serializer(data=request.data,instance=instance,partial=True)

		if serializer.is_valid():
			server=serializer.save()
			data=GetServerSerializer(server,context=self.get_serializer_context()).data

			return Response({
				"message":"server data updated successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"server data not updated",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)

class GetServer(APIView):
	permission_classes=(IsAdmin,)

	def get(self,request,id,*args,**kwargs):

		try:
			instance=Server.objects.get(pk=id)
		except Server.DoesNotExist as e:
			return Response({
				"message":"server with id %s does not exists"%(id),
				"status":"error"
				})

		data=GetServerSerializer(instance).data

		return Response({
			"message":"server data fetched successfully",
			"status":"success",
			"data":data
			})


class DeleteServer(APIView):
	permission_classes=(IsAdmin,)

	def delete(self,request,id,*args,**kwargs):
		try:
			instance=Server.objects.get(pk=id)
		except Server.DoesNotExist as e:
			return Response({
				"message":"server with id %s does not exists"%(id),
				"status":"error"
				})
		instance.delete()

		return Response({
			"message":"server data deleted successfully",
			"status":"success"
			},status=status.HTTP_200_OK)




"""
Workspace Api's
"""

class GetWorkspaceList(APIView):
	permission_classes=(IsAdmin,)
	
	def get(self,request,*args,**kwargs):
		workspace=Workspace.objects.all()
		data=GetWorkspaceSerializer(workspace,many=True).data

		if data:
			return Response({
			"message":"workspace data fetched successfully",
			"status":"success",
			"data":data
			})
		return Response({
			"message":"there is no workspace data avialable",
			"status":"error",
			"data":data
			})


class PostWorkspaceApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	parser_classes = (MultiPartParser,)
	serializer_class=PostWorkspaceSerializer

	def post(self,request,*args,**kwargs):
		serializer=self.get_serializer(data=request.data)
		if serializer.is_valid():
			# server_id=serializer.validated_data["server"]
			name=serializer.validated_data["name"]
			try:
				# server=Server.objects.get(pk=server_id)
				server=serializer.validated_data["server"]
			except Exception as e:
				return Response({
					"message":"server with id %s does not exists",
					"status":"error"
					})
			server_url=server.frontend_url
			services_dict={
			"uri":server.frontend_url+"/"+name,
			"wms_endpoint":server.getWmsEndpoint(workspace=name),
			"wfs_endpoint":server.getWfsEndpoint(workspace=name),
			"wcs_endpoint":server.getWcsEndpoint(workspace=name),
			"wmts_endpoint":server.getWmtsEndpoint(workspace=name),
			"cache_endpoint":server.getCacheEndpoint(workspace=name)
			}
			workspace=serializer.save(**services_dict)
			data=GetWorkspaceSerializer(workspace,context=self.get_serializer_context()).data
			return Response({
				"message":"workspace data saved successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"workspace data not saved",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)


class UpdateWorkspaceApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=UpdateWorkspaceSerializer

	# def put(self,request,id,*args,**kwargs):
	# 	try:
	# 		instance=Workspace.objects.get(pk=id)
	# 	except Workspace.DoesNotExist as e:
	# 		return Response({
	# 			"message":"workspace with id %s does not exists"%(id),
	# 			"status":"error"
	# 			})
	# 	serializer=self.get_serializer(data=request.data,instance=instance)

	# 	if serializer.is_valid():
	# 		workspace=serializer.save()
	# 		data=GetWorkspaceSerializer(workspace,context=self.get_serializer_context()).data

	# 		return Response({
	# 			"message":"workspace updated successfully",
	# 			"status":"success",
	# 			"data":data
	# 			})
	# 	return Response({
	# 		"message":"workspace not updated",
	# 		"status":"error",
	# 		"error":serializer.errors
	# 		})
	def patch(self,request,id,*args,**kwargs):
		try:
			instance=Workspace.objects.get(pk=id)
		except Workspace.DoesNotExist as e:
			return Response({
				"message":"workspace with id %s does not exists"%(id),
				"status":"error"
				})
		serializer=self.get_serializer(data=request.data,instance=instance,partial=True)

		if serializer.is_valid():
			workspace=serializer.save()
			data=GetWorkspaceSerializer(workspace,context=self.get_serializer_context()).data

			return Response({
				"message":"workspace data updated successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"workspace data not updated",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)

class GetWorkspace(APIView):
	permission_classes=(IsAdmin,)

	def get(self,request,id,*args,**kwargs):

		try:
			instance=Workspace.objects.get(pk=id)
		except Workspace.DoesNotExist as e:
			return Response({
				"message":"workspace with id %s does not exists"%(id),
				"status":"error"
				})

		data=GetWorkspaceSerializer(instance).data

		return Response({
			"message":"workspace data fetched successfully",
			"status":"success",
			"data":data
			})


class DeleteWorkspace(APIView):
	permission_classes=(IsAdmin,)

	def delete(self,request,id,*args,**kwargs):
		try:
			instance=Workspace.objects.get(pk=id)
		except Workspace.DoesNotExist as e:
			return Response({
				"message":"workspace with id %s does not exists"%(id),
				"status":"error"
				})
		instance.delete()

		return Response({
			"message":"workspace data deleted successfully",
			"status":"success"
			},status=status.HTTP_200_OK)



"""
Datastore Api's
"""

class GetDatastoreList(APIView):
	permission_classes=(IsAdmin,)
	
	def get(self,request,*args,**kwargs):
		datastore=Datastore.objects.all()
		# datastore.connection_params["passwd"]="****"
		data=GetDatastoreSerializer(datastore,many=True).data

		if data:
			return Response({
			"message":"datastore data fetched successfully",
			"status":"success",
			"data":data
			})
		return Response({
			"message":"there is no datastore data avialable",
			"status":"error",
			"data":data
			})


class PostDatastoreApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	parser_classes = (MultiPartParser,)
	serializer_class=PostDatastoreSerializer

	def post(self,request,*args,**kwargs):
		serializer=self.get_serializer(data=request.data)
		if serializer.is_valid():
			params = json.loads(serializer.validated_data["connection_params"])
			if serializer.validated_data["type"] == "c_GeoTIFF":
				path = params.get("url",None)
				if not path:
					return Response({
						"message":"Invalid connection_params.. you should pass {'url':'file:/path/to/file.tiff'}",
						"status":"error"
						},status=status.HTTP_400_BAD_REQUEST)
				# if not Path(path).is_file():
				# 	return Response({
				# 		"message":"you must pass proper geotiff file path",
				# 		"status":"error"
				# 		},status=status.HTTP_400_BAD_REQUEST)
			if serializer.validated_data["type"] == "v_PostGIS":
				default_connection=("host","port","database","schema","user","passwd","dbtype")
				validate=lambda x:True if x in params else False
				connection_field_status=all(list(map(validate,default_connection)))
				if not bool(params) or not connection_field_status:
					return Response({
						"message":f"error in connection_params, there are several fields that are missing. connection_params should be like this {DEFAULT_DB_STRUCTURE}",
						"status":"error"
						})
			ds_params = {
			"workspace" : serializer.validated_data["workspace"],
			"type" : serializer.validated_data["type"],
			"name" : serializer.validated_data["name"],
			"description" : serializer.validated_data["description"],
			"connection_params" : serializer.validated_data["connection_params"],
			}
			workspace = ds_params.get("workspace")
			gs = geographic_servers.get_instance().get_server_by_id(workspace.server.id)
			ds =  gs.createDatastore(**ds_params)
			if isinstance(ds,dict):
				return Response(ds,status=status.HTTP_400_BAD_REQUEST)
			else:
				created_by=request.user.username
				datastore=serializer.save(created_by = created_by)
				data=GetDatastoreSerializer(datastore,context=self.get_serializer_context()).data
				return Response({
					"message":"datastore data saved successfully",
					"status":"success",
					"data":data
					})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"datastore data not saved",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)


class UpdateDatastoreApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=UpdateDatastoreSerializer

	def put(self,request,id,*args,**kwargs):
		try:
			instance=Datastore.objects.get(pk=id)
		except Datastore.DoesNotExist as e:
			return Response({
				"message":"datastore with id %s does not exists"%(id),
				"status":"error"
				})
		serializer=self.get_serializer(data=request.data,instance=instance)

		if serializer.is_valid():
			datastore=serializer.save()
			data=GetDatastoreSerializer(datastore,context=self.get_serializer_context()).data

			return Response({
				"message":"datastore data updated successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"datastore data not updated",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)
	def patch(self,request,id,*args,**kwargs):
		try:
			instance=Datastore.objects.get(pk=id)
		except Datastore.DoesNotExist as e:
			return Response({
				"message":"datastore with id %s does not exists"%(id),
				"status":"error"
				})
		serializer=self.get_serializer(data=request.data,instance=instance,partial=True)

		if serializer.is_valid():
			datastore=serializer.save()
			data=GetDatastoreSerializer(datastore,context=self.get_serializer_context()).data

			return Response({
				"message":"datastore data updated successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"datastore data not updated",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)

class GetDatastore(APIView):
	permission_classes=(IsAdmin,)

	def get(self,request,id,*args,**kwargs):

		try:
			instance=Datastore.objects.get(pk=id)
			instance.connection_params["passwd"]="****"
		except Datastore.DoesNotExist as e:
			return Response({
				"message":"datastore with id %s does not exists"%(id),
				"status":"error"
				})

		data=GetDatastoreSerializer(instance).data

		return Response({
			"message":"datastore data fetched successfully",
			"status":"success",
			"data":data
			})


class DeleteDatastore(APIView):
	permission_classes=(IsAdmin,)

	def delete(self,request,id,*args,**kwargs):
		try:
			instance=Datastore.objects.get(pk=id)
		except Datastore.DoesNotExist as e:
			return Response({
				"message":"datastore with id %s does not exists"%(id),
				"status":"error"
				})
		instance.delete()

		return Response({
			"message":"datastore data deleted successfully",
			"status":"success"
			},status=status.HTTP_200_OK)




"""
LayerGroup Api's
"""


class GetLayerGroupList(APIView):
	permission_classes=(permissions.IsAuthenticated,)
	
	def get(self,request,*args,**kwargs):
		layergroup=LayerGroup.objects.all()	
		
		data=GetLayerGroupSerializer(layergroup,many=True).data

		if data:
			return Response({
			"message":"layer group data fetched successfully",
			"status":"success",
			"data":data
			})
		return Response({
			"message":"there is no layergroup data avialable",
			"status":"error",
			"data":data
			})


#Temporary api for all data
class GetLayerGroupListOther(APIView):
	permission_classes=(permissions.IsAuthenticated,)
	
	def get(self,request,*args,**kwargs):
		layergroup=LayerGroup.objects.all()
		data=GetLayerGroupSerializer(layergroup,many=True).data

		if data:
			return Response({
			"message":"layer group data fetched successfully",
			"status":"success",
			"data":data
			})
		return Response({
			"message":"there is no layergroup data avialable",
			"status":"error",
			"data":data
			})


class PostLayerGroupApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=PostLayerGroupSerializer
	parser_classes=[MultiPartParser]

	def post(self,request,*args,**kwargs):
		serializer=self.get_serializer(data=request.data)
		if serializer.is_valid():
			try:
				Server.objects.get(pk=serializer.validated_data["server_id"])
			except Server.DoesNotExist as e:
				return Response({
					"message":"There is not any server data for id %s"%(serializer.validated_data["server_id"]),
					"status":"error"
					})
			layergroup=serializer.save()
			data=GetLayerGroupSerializer(layergroup,context=self.get_serializer_context()).data
			return Response({
				"message":"layergroup data saved successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"layergroup data not saved",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)


class UpdateLayerGroupApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=UpdateLayerGroupSerializer
	parser_classes=[MultiPartParser]

	def put(self,request,id,*args,**kwargs):
		try:
			instance=LayerGroup.objects.get(pk=id)
		except LayerGroup.DoesNotExist as e:
			return Response({
				"message":"layer with id %s does not exists"%(id),
				"status":"error"
				})
		serializer=self.get_serializer(data=request.data,instance=instance)

		if serializer.is_valid():
			layergroup=serializer.save()
			data=GetLayerGroupSerializer(layergroup,context=self.get_serializer_context()).data

			return Response({
				"message":"layergroup data updated successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"layergroup data not updated",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)
	def patch(self,request,id,*args,**kwargs):
		try:
			instance=LayerGroup.objects.get(pk=id)
		except LayerGroup.DoesNotExist as e:
			return Response({
				"message":"layergroup with id %s does not exists"%(id),
				"status":"error"
				})
		serializer=self.get_serializer(data=request.data,instance=instance,partial=True)

		if serializer.is_valid():
			layergroup=serializer.save()
			data=GetLayerGroupSerializer(layergroup,context=self.get_serializer_context()).data

			return Response({
				"message":"layergroup data updated successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"layergroup data not updated",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)

class GetLayerGroup(APIView):
	permission_classes=(permissions.IsAuthenticated,)

	def get(self,request,id,*args,**kwargs):

		try:
			instance=LayerGroup.objects.get(pk=id)
		except LayerGroup.DoesNotExist as e:
			return Response({
				"message":"layergroup with id %s does not exists"%(id),
				"status":"error"
				})
		# print(instance.get_ol_params())

		data=GetLayerGroupSerializer(instance).data

		return Response({
			"message":"layergroup data fetched successfully",
			"status":"success",
			"data":data
			})


class DeleteLayerGroup(APIView):
	permission_classes=(IsAdmin,)

	def delete(self,request,id,*args,**kwargs):
		try:
			instance=LayerGroup.objects.get(pk=id)
		except LayerGroup.DoesNotExist as e:
			return Response({
				"message":"layergroup with id %s does not exists"%(id),
				"status":"error"
				})
		instance.delete()

		return Response({
			"message":"layergroup data deleted successfully",
			"status":"success"
			},status=status.HTTP_200_OK)






"""
Layer Api's
"""

class GetDetailedLayerList(APIView):
	permission_classes=(permissions.IsAuthenticated,)
	
	def get(self,request,*args,**kwargs):
		layer=Layer.objects.all()
		data=GetLayerSerializer(layer,many=True).data

		if data:
			return Response({
			"message":"layer data fetched successfully",
			"status":"success",
			"data":data
			})
		return Response({
			"message":"there is no layer data avialable",
			"status":"error",
			"data":data
			})


class GetLayerList(APIView):
	permission_classes=(permissions.IsAuthenticated,)
	serializer=GetShortLayerSerializer
	
	def get(self,request,*args,**kwargs):
		if request.query_params:
			layer=Layer.objects.filter(layer_group__name__in=dict(request.query_params)["layer_group"])
		else:
			layer=Layer.objects.all()
			
		data=self.serializer(layer,many=True).data

		if data:
			return Response({
			"message":"layer data fetched successfully",
			"status":"success",
			"data":data
			})
		return Response({
			"message":"there is no layer data avialable",
			"status":"error",
			"data":data
			})


#Temporary api for all data
class GetVectorTileLayerListOther(APIView):
	permission_classes=(permissions.IsAuthenticated,)
	serializer=GetShortLayerSerializer
	
	def get(self,request,*args,**kwargs):
		layer=Layer.objects.all()
		data=self.serializer(layer,many=True).data

		if data:
			return Response({
			"message":"layer data fetched successfully",
			"status":"success",
			"data":data
			})
		return Response({
			"message":"there is no layer data avialable",
			"status":"error",
			"data":data
			})

class GetVectorTileLayerList(GetLayerList):
	permission_classes=(permissions.IsAuthenticated,)
	serializer=GetVectorLayerSerializer


class PostLayerApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=PostLayerSerializer
	parser_classes=[MultiPartParser]

	def post(self,request,*args,**kwargs):
		serializer=self.get_serializer(data=request.data)
		if serializer.is_valid():
			name = serializer.validated_data["source_name"]
			title = serializer.validated_data["title"]
			datastore = serializer.validated_data["datastore"]
			workspace = datastore.workspace
			gs=geographic_servers.get_instance().get_server_by_id(workspace.server.id)

			published_data = gs.createLayer(workspace,datastore,name,title)
			
			if isinstance(published_data,dict):
				return Response(published_data,status=status.HTTP_400_BAD_REQUEST)
			layer=serializer.save()
			data=GetLayerSerializer(layer,context=self.get_serializer_context()).data
			return Response({
				"message":"layer data saved successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"layer data not saved",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)


class UpdateLayerApi(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=UpdateLayerSerializer
	parser_classes=[MultiPartParser]

	def put(self,request,id,*args,**kwargs):
		try:
			instance=Layer.objects.get(pk=id)
		except Layer.DoesNotExist as e:
			return Response({
				"message":"layer with id %s does not exists"%(id),
				"status":"error"
				})
		serializer=self.get_serializer(data=request.data,instance=instance)

		if serializer.is_valid():
			layer=serializer.save()
			data=GetLayerSerializer(layer,context=self.get_serializer_context()).data

			return Response({
				"message":"layer data updated successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"layer data not updated",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)
	def patch(self,request,id,*args,**kwargs):
		try:
			instance=Layer.objects.get(pk=id)
		except Layer.DoesNotExist as e:
			return Response({
				"message":"layer with id %s does not exists"%(id),
				"status":"error"
				})
		serializer=self.get_serializer(data=request.data,instance=instance,partial=True)

		if serializer.is_valid():
			layer=serializer.save()
			data=GetLayerSerializer(layer,context=self.get_serializer_context()).data

			return Response({
				"message":"layer data updated successfully",
				"status":"success",
				"data":data
				})
		error = error_simplifier(serializer.errors)
		return Response({
			"message":"layer data not updated",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)

class GetLayer(APIView):
	permission_classes=(permissions.IsAuthenticated,)

	def get(self,request,id,*args,**kwargs):

		try:
			instance=Layer.objects.get(pk=id)
		except Layer.DoesNotExist as e:
			return Response({
				"message":"layer with id %s does not exists"%(id),
				"status":"error"
				})
		# print(instance.get_ol_params())

		data=GetLayerSerializer(instance).data

		return Response({
			"message":"layer data fetched successfully",
			"status":"success",
			"data":data
			})


class DeleteLayer(APIView):
	permission_classes=(IsAdmin,)

	def delete(self,request,id,*args,**kwargs):
		try:
			instance=Layer.objects.get(pk=id)
		except Layer.DoesNotExist as e:
			return Response({
				"message":"layer with id %s does not exists"%(id),
				"status":"error"
				})
		datastore = instance.datastore
		workspace = datastore.workspace
		name = instance.source_name

		gs=geographic_servers.get_instance().get_server_by_id(workspace.server.id)

		deleted_layer = gs.deleteLayer(workspace,datastore,name)
		if isinstance(deleted_layer,dict):
			return Response(deleted_layer,status = status.HTTP_400_BAD_REQUEST)
		instance.delete()

		return Response({
			"message":"layer data deleted successfully",
			"status":"success"
			},status=status.HTTP_200_OK)





"""
Temporary Get Layer Api
"""

class GetGsLayerList(generics.GenericAPIView):
	permission_classes=(IsAdmin,)
	serializer_class=GetGsLayerSerializer
	def post(self,request,*args,**kwargs):
		serializer=self.get_serializer(data=request.data)
		if serializer.is_valid():
			workspace=serializer.validated_data["workspace"]
			gs=Geoserver(1,"default","geoserver","admin","geoserver","http://localhost:8080/geoserver")
			gs_data=gs.getGsLayers()
			gs_config=gs.getGsconfig()
			gs_styles=gs_config.get_styles(workspaces=workspace)
			print([i.sld_name for i in gs_styles ])
			layers=[]
			for lyr in gs_data:
				if workspace in lyr.name:
					print(lyr._get_alternate_styles(),"get alternate styles")
					print(lyr._get_default_style(),"get default style")
					layers.append({"extent":list(lyr.resource.native_bbox)[:-1],\
						"url":"http://localhost:8080/geoserver/wms",\
						"srs":lyr.resource.projection,\
						"params":{"LAYERS":lyr.name,'VERSION': '1.1.1',"STYLES": '','TILED': False},
						})
				if lyr.name=="tiger:tiger_roads":
					print([i.sld_name for i in lyr._get_alternate_styles()],"get alternate style")
					print(lyr._get_default_style().sld_name,"get default style")
			if layers:
				return Response({
					"message":"successfully fetched layers data",
					"status":"success",
					"data":layers
					})
		return Response({
			"message":"layer data not fetched",
			"status":"error",
			"error":serializer.errors
			},status=status.HTTP_400_BAD_REQUEST)



"""
Spatial Data and Non-spatial data updating
"""

class SpatialNonSpatialEditing(generics.GenericAPIView):
	permission_classes = (permissions.IsAuthenticated,~IsView)
	serializer_class = SpatialNonSpatialEditSerializer
	parser_classes = (MultiPartParser,)

	def post(self,request,layer_id,*args,**kwargs):
		serializer = self.get_serializer(data = request.data)

		if serializer.is_valid():
			action = serializer.validated_data["action"]
			editType = serializer.validated_data["editType"]
			if (action == ACTION_INSERT or action == ACTION_DELETE) and editType != EDIT_TYPE_ALL:
				return Response({
					"message":"For actions Insert Or Delete you must Choose '%s' in editType"%(EDIT_TYPE_ALL),
					"status":"error",
					},status=status.HTTP_400_BAD_REQUEST)

			if "View_and_nonspatial_edit" in request.user.groups.values_list("name",flat = True):
				if action != ACTION_UPDATE:
					return Response({
						"message":"You are only allowed to update the existing Attribute data",
						"status":"error"
						},status=status.HTTP_400_BAD_REQUEST)
				if editType != EDIT_TYPE_NON_SPATIAL:
					return Response({
						"message":"You can only update Non-spatial data i.e Attribute data so you must Choose '%s' in editType"%(EDIT_TYPE_NON_SPATIAL),
						"status":"error"
						},status=status.HTTP_400_BAD_REQUEST)

			try:
				layer = Layer.objects.get(id=layer_id)
			except Layer.DoesNotExist as e:
				return Response({
					"message":"Layer with id %d does not exist"%(layer_id),
					"status":"error",
					},status=status.HTTP_400_BAD_REQUEST)

			data = serializer.validated_data["Geojson"]
			processing = DataProcessing(layer.datastore)
			if action == ACTION_UPDATE:
				updated_data = processing.UpdateData(data,layer.native_srs,layer.name,
					action,editType)
			elif action == ACTION_INSERT:
				updated_data = processing.InsertData(data,layer.native_srs,layer.name,
					action,editType)
			elif action == ACTION_DELETE:
				updated_data = processing.DeleteData(data,layer.native_srs,layer.name,
					action,editType)

			if isinstance(updated_data,dict):
				return Response(updated_data, status = status.HTTP_400_BAD_REQUEST)
			elif updated_data:
				return Response({
					"message":"layer data %sed successfully"%(action),
					"status":"success",
					"data":data
					})
			else:
				return Response({
					"message":"layer data not %sed"%(action),
					"status":"error"
					})

		error = error_simplifier(serializer.errors)
		return Response({
			"message":"error occurred while performing spatial - nonspatial update",
			"status":"error",
			"error":error
			},status=status.HTTP_400_BAD_REQUEST)