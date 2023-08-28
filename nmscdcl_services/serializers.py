from rest_framework import serializers
from .models import *
from KrushiGram.settings import MODE_CREATE,MODE_APPEND,MODE_OVERWRITE,ACTION_INSERT,ACTION_UPDATE,\
ACTION_DELETE,EDIT_TYPE_SPATIAL,EDIT_TYPE_NON_SPATIAL,EDIT_TYPE_ALL
from rest_framework.validators import UniqueValidator

# class ExportToPostgisSerializer(serializers.Serializer):

# 	mode_choice=(
# 		(MODE_CREATE,MODE_CREATE),
# 		(MODE_APPEND,MODE_APPEND),
# 		(MODE_OVERWRITE,MODE_OVERWRITE))

# 	file=serializers.CharField(max_length=50)
# 	mode=serializers.ChoiceField(choices=mode_choice)
# 	name=serializers.CharField(max_length=50)
# 	encoding=serializers.CharField(max_length=20)
# 	srs=serializers.CharField(max_length=50)


#Query DB serializer
class DBQuerySerializer(serializers.Serializer):
	query = serializers.CharField(max_length=1000,required=True)


#Spatial & Non-Spatial Editing Serializer
class SpatialNonSpatialEditSerializer(serializers.Serializer):
	mode_choice = (
		(ACTION_INSERT,ACTION_INSERT),
		(ACTION_UPDATE,ACTION_UPDATE),
		(ACTION_DELETE,ACTION_DELETE))

	type_choice = (
		(EDIT_TYPE_SPATIAL,EDIT_TYPE_SPATIAL),
		(EDIT_TYPE_NON_SPATIAL,EDIT_TYPE_NON_SPATIAL),
		(EDIT_TYPE_ALL,EDIT_TYPE_ALL))

	Geojson = serializers.JSONField()
	action = serializers.ChoiceField(choices = mode_choice)
	editType = serializers.ChoiceField(choices = type_choice)


"""
Server Serialziers
"""

class GetServerSerializer(serializers.ModelSerializer):

	class Meta:
		model=Server
		fields=("id","name","title","description","type","frontend_url","user","password","default")
		read_only_fields=fields


class PostServerSerializer(serializers.ModelSerializer):
	class Meta:
		model=Server
		fields=("name","title","description","type","frontend_url","user","password","default")

	def validate(self,validated_data):
		if "name" not in validated_data or validated_data["name"]=="":
			raise serializers.ValidationError("name cannot be empty")
		if "type" not in validated_data or validated_data["type"]=="":
			raise serializers.ValidationError("type cannot be empty")
		if "frontend_url" not in validated_data or validated_data["frontend_url"]=="":
			raise serializers.ValidationError("frontend_url cannot be empty")
		if "user" not in validated_data or validated_data["user"]=="":
			raise serializers.ValidationError("user cannot be empty")
		if "password" not in validated_data or validated_data["password"]=="":
			raise serializers.ValidationError("password cannot be empty")

		return validated_data


class UpdateServerSerializer(serializers.ModelSerializer):
	class Meta:
		model=Server
		fields=("name","title","description","type","frontend_url","user","password","default")



"""
Workspace Serialziers
"""

class GetWorkspaceSerializer(serializers.ModelSerializer):

	class Meta:
		model=Workspace
		fields=("id","server","name","description","uri","wms_endpoint","wfs_endpoint","wcs_endpoint",\
			"wmts_endpoint","cache_endpoint","is_public")
		read_only_fields=fields


class PostWorkspaceSerializer(serializers.ModelSerializer):
	class Meta:
		model=Workspace
		fields=("server","name","description","is_public")

	def validate(self,validated_data):
		if "server" not in validated_data or validated_data["server"]=="":
			raise serializers.ValidationError("server cannot be empty")
		if "name" not in validated_data or validated_data["name"]=="":
			raise serializers.ValidationError("name cannot be empty")
		if "is_public" not in validated_data or validated_data["is_public"]=="":
			raise serializers.ValidationError("is_public cannot be empty")

		return validated_data


class UpdateWorkspaceSerializer(serializers.ModelSerializer):
	class Meta:
		model=Workspace
		fields=("description","uri","is_public")




"""
Datastore Serialziers
"""

class GetDatastoreSerializer(serializers.ModelSerializer):

	class Meta:
		model=Datastore
		fields=("id","workspace","type","name","description","connection_params")
		read_only_fields=fields


class PostDatastoreSerializer(serializers.ModelSerializer):
	class Meta:
		model=Datastore
		fields=("workspace","type","name","description","connection_params")

	def validate(self,validated_data):
		if "workspace" not in validated_data or validated_data["workspace"]=="":
			raise serializers.ValidationError("workspace cannot be empty")
		if "type" not in validated_data or validated_data["type"]=="":
			raise serializers.ValidationError("type cannot be empty")
		if "name" not in validated_data or validated_data["name"]=="":
			raise serializers.ValidationError("name cannot be empty")
		if "connection_params" not in validated_data or validated_data["connection_params"]=="":
			raise serializers.ValidationError("connection_params cannot be empty")

		return validated_data


class UpdateDatastoreSerializer(serializers.ModelSerializer):
	class Meta:
		model=Datastore
		fields=("description","connection_params")



"""
Layer List
"""
class GetLayerList(serializers.ModelSerializer):
	class Meta:
		model=Layer
		fields=("id","name")


"""
LayerGroup Serialziers
"""

class GetLayerGroupSerializer(serializers.ModelSerializer):
	# subLayers = GetLayerList(many = True , source = "layer_set")
	class Meta:
		model=LayerGroup
		fields=('id','server_id','name','title','visible','cached','layer_set','isChecked')
		read_only_fields=fields


class PostLayerGroupSerializer(serializers.ModelSerializer):
	class Meta:
		model=LayerGroup
		fields=('server_id','name','title','visible','cached')
		extra_kwargs = {
			"name":{
				"validators":[
				UniqueValidator(
					queryset=LayerGroup.objects.all()
					)
				]
			}
		}

	def validate(self,validated_data):
		if "server_id" not in validated_data or validated_data["server_id"]=="":
			raise serializers.ValidationError("server_id cannot be empty")
		if "name" not in validated_data or validated_data["name"]=="":
			raise serializers.ValidationError("name cannot be empty")
		if "visible" not in validated_data or validated_data["visible"]=="":
			raise serializers.ValidationError("visible cannot be empty")
		if "cached" not in validated_data or validated_data["cached"]=="":
			raise serializers.ValidationError("cached cannot be empty")

		return validated_data


class UpdateLayerGroupSerializer(serializers.ModelSerializer):
	class Meta:
		model=LayerGroup
		fields=('server_id','name','title','visible','cached')
		extra_kwargs = {
			"name":{
				"validators":[
				UniqueValidator(
					queryset=LayerGroup.objects.all()
					)
				]
			}
		}



"""
Layer Serialziers
"""
class GetShortLayerSerializer(serializers.ModelSerializer):
	layergroup_name=serializers.CharField(source="layer_group.name")

	class Meta:
		model=Layer
		fields=("id","title","layergroup_name","tile_params","checked","opacity")


"""
Layer Serialziers
"""
class GetVectorLayerSerializer(serializers.ModelSerializer):
	layergroup_name=serializers.CharField(source="layer_group.name")

	class Meta:
		model=Layer
		fields=("id","title","name","layergroup_name","vector_tile_params","checked","opacity","opacityChecked")


class GetLayerSerializer(serializers.ModelSerializer):
	layergroup_name=serializers.CharField(source="layer_group.name")

	class Meta:
		model=Layer
		fields=("id","external","external_params","datastore","layer_group","layergroup_name","name","title",\
			"abstract","type","public","visible","queryable","cached","single_image","vector_tile",\
			"allow_download","order","created_by","thumbnail","timeout","native_srs","native_extent",\
			"latlong_extent","source_name")
		# read_only_fields=fields


class PostLayerSerializer(serializers.ModelSerializer):
	class Meta:
		model=Layer
		fields=("external","external_params","datastore","layer_group","name","title",\
			"abstract","type","public","visible","queryable","cached","single_image","vector_tile",\
			"allow_download","order","thumbnail","timeout","native_srs","native_extent",\
			"latlong_extent","source_name")
		extra_kwargs = {
			"name":{
				"validators":[
				UniqueValidator(
					queryset=Layer.objects.all()
					)
				]
			}
		}

	def validate(self,validated_data):
		if "external" not in validated_data or validated_data["external"]=="":
			raise serializers.ValidationError("external cannot be empty")
		if "datastore" not in validated_data or validated_data["datastore"]=="":
			raise serializers.ValidationError("datastore cannot be empty")
		if "layer_group" not in validated_data or validated_data["layer_group"]=="":
			raise serializers.ValidationError("layer_group cannot be empty")
		if "name" not in validated_data or validated_data["name"]=="":
			raise serializers.ValidationError("name cannot be empty")
		if "title" not in validated_data or validated_data["title"]=="":
			raise serializers.ValidationError("title cannot be empty")
		if "type" not in validated_data or validated_data["type"]=="":
			raise serializers.ValidationError("type cannot be empty")
		if "public" not in validated_data or validated_data["public"]=="":
			raise serializers.ValidationError("public cannot be empty")
		if "visible" not in validated_data or validated_data["visible"]=="":
			raise serializers.ValidationError("visible cannot be empty")
		if "queryable" not in validated_data or validated_data["queryable"]=="":
			raise serializers.ValidationError("queryable cannot be empty")
		if "cached" not in validated_data or validated_data["cached"]=="":
			raise serializers.ValidationError("cached cannot be empty")
		if "single_image" not in validated_data or validated_data["single_image"]=="":
			raise serializers.ValidationError("single_image cannot be empty")
		if "vector_tile" not in validated_data or validated_data["vector_tile"]=="":
			raise serializers.ValidationError("vector_tile cannot be empty")
		if "allow_download" not in validated_data or validated_data["allow_download"]=="":
			raise serializers.ValidationError("allow_download cannot be empty")
		if "order" not in validated_data or validated_data["order"]=="":
			raise serializers.ValidationError("order cannot be empty")
		if "timeout" not in validated_data or validated_data["timeout"]=="":
			raise serializers.ValidationError("timeout cannot be empty")
		if "native_srs" not in validated_data or validated_data["native_srs"]=="":
			raise serializers.ValidationError("native_srs cannot be empty")
		if "native_extent" not in validated_data or validated_data["native_extent"]=="":
			raise serializers.ValidationError("native_extent cannot be empty")
		if "latlong_extent" not in validated_data or validated_data["latlong_extent"]=="":
			raise serializers.ValidationError("latlong_extent cannot be empty")


		return validated_data


class UpdateLayerSerializer(serializers.ModelSerializer):
	class Meta:
		model=Layer
		fields=("external","external_params","datastore","layer_group","name","title",\
			"abstract","type","public","visible","queryable","cached","single_image","vector_tile",\
			"allow_download","order","thumbnail","timeout","native_srs","native_extent",\
			"latlong_extent","source_name")
		extra_kwargs = {
			"name":{
				"validators":[
				UniqueValidator(
					queryset=Layer.objects.all()
					)
				]
			}
		}


class GetGsLayerSerializer(serializers.Serializer):
	workspace=serializers.CharField(max_length=50)