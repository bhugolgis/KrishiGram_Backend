from django.db import models
from krishi_auth.models import User
from KrushiGram.settings import MODE_CREATE,MODE_APPEND,MODE_OVERWRITE,FILEMANAGER_DIRECTORY
from nmscdcl_services.models import Datastore

# Create your models here.

class ShapeFiles(models.Model):
	user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="userShape")
	fileName=models.CharField(max_length=100)
	# filePath=models.CharField(max_length=300)
	timestamp=models.DateTimeField(auto_now_add=True)

	def __str__(self) -> None:
		return self.fileName

	def get_absolute_path(self):
		path=FILEMANAGER_DIRECTORY + f"/{self.fileName}"

	def get_shape_path(self):
		path=FILEMANAGER_DIRECTORY + f"/{self.fileName}/{self.fileName}.shp"

class ExportHistory(models.Model):
	# Creation choices
	mode_choice=(
		(MODE_CREATE,MODE_CREATE),
		(MODE_APPEND,MODE_APPEND),
		(MODE_OVERWRITE,MODE_OVERWRITE))

	fileName = models.CharField(max_length = 300)
	creationMode = models.CharField(max_length = 50 ,choices = mode_choice)
	name = models.CharField(max_length = 300)
	layerName = models.CharField(max_length = 300)
	encoding = models.CharField(max_length = 100,blank=True)
	srs = models.CharField(max_length = 50,blank=True)
	datastore = models.ForeignKey(Datastore, on_delete = models.CASCADE, related_name = "dataSource")
	is_published = models.BooleanField(default = False)
	is_delete = models.BooleanField(default = False)
	created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="ExportUser")
	created_at = models.DateTimeField(auto_now_add = True)
	modified_at = models.DateTimeField(auto_now = True)

	def __str__(self) -> None:
		return self.fileName

	def get_absolute_path(self):
		path=FILEMANAGER_DIRECTORY + f"/{self.fileName}"

	def get_shape_path(self):
		path=FILEMANAGER_DIRECTORY + f"/{self.fileName}/{self.fileName}.shp"
