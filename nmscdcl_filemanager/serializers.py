from rest_framework import serializers
from .models import *
from KrushiGram.settings import MODE_CREATE,MODE_APPEND,MODE_OVERWRITE


class UploadShapeSerializer(serializers.Serializer):
	mode_choice = (
		(MODE_CREATE,MODE_CREATE),
		(MODE_OVERWRITE,MODE_OVERWRITE))

	creation_choice = (
		(MODE_CREATE,MODE_CREATE),
		(MODE_APPEND,MODE_APPEND),
		(MODE_OVERWRITE,MODE_OVERWRITE))

	file = serializers.FileField(required = True)
	choice = serializers.ChoiceField(required = True,choices = mode_choice)
	export = serializers.BooleanField(default = False , required = False)
	creationMode = serializers.ChoiceField(choices = creation_choice, required = False)
	name = serializers.CharField(max_length = 50, required = False)
	encoding = serializers.CharField(max_length = 20, required = False)
	srs = serializers.CharField(max_length = 50, required = False)
	datastore = serializers.IntegerField(required = False)

	def validate(self,validated_data):

		if "file" not in validated_data or validated_data["file"] == "":
			raise serializers.ValidationError("file field cannot be empty")
		if "choice" not in validated_data or validated_data["choice"] == "":
			raise serializers.ValidationError("choice field cannot be empty")

		return validated_data

class ExportGeojsonToPostgis(serializers.Serializer):
	mode_choice=(
		(MODE_CREATE,MODE_CREATE),
		(MODE_APPEND,MODE_APPEND),
		(MODE_OVERWRITE,MODE_OVERWRITE))

	file=serializers.FileField(required=True)
	mode=serializers.ChoiceField(choices=mode_choice)
	name=serializers.CharField(max_length=50)
	encoding=serializers.CharField(max_length=20)
	srs=serializers.CharField(max_length=50)


class GetShapeFileSerializer(serializers.ModelSerializer):
	class Meta:
		model = ShapeFiles
		fields = ('id','user' , 'fileName')
		read_only_fields=fields

class storeshapefilePathSerializer(serializers.ModelSerializer):
	class Meta:
		model = ShapeFiles
		fields = ('fileName',)

class GetExportToPostgisSerializer(serializers.ModelSerializer):
	datastore_name = serializers.SerializerMethodField()
	class Meta:
		model = ExportHistory
		fields = ("fileName","creationMode","name","layerName","encoding","srs",
			"datastore","datastore_name","is_published","created_by","created_at")
		read_only_fields=fields
	
	def get_datastore_name(self , obj):
		return obj.datastore.name
		

class ExportToPostgisSerializer(serializers.ModelSerializer):
	class Meta:
		model = ExportHistory
		fields = ("fileName","creationMode","name","encoding","srs",
			"datastore")

	def validate(self,validated_data):
		if "fileName" not in validated_data or validated_data["fileName"] == "":
			raise serializers.ValidationError("please provide fileName")
		if "creationMode" not in validated_data or validated_data["creationMode"] == "":
			raise serializers.ValidationError("please provide creationMode")
		if "name" not in validated_data or validated_data["name"] == "":
			raise serializers.ValidationError("please provide name")
		if "encoding" not in validated_data or validated_data["encoding"] == "":
			raise serializers.ValidationError("please provide encoding")
		if "srs" not in validated_data or validated_data["srs"] == "":
			raise serializers.ValidationError("please provide srs")
		if "datastore" not in validated_data or validated_data["datastore"] == "":
			raise serializers.ValidationError("please provide datastore")

		return validated_data
