from django.core.files.storage import default_storage
from django.conf import settings
from KrushiGram.settings import FILEMANAGER_DIRECTORY
import zipfile
import shutil
import os
import platform
from .utils import sizeof_fmt,geojson_to_shape_convertor


class FileManager(object):
	def __init__(self,path=None):
		self.path=self.update_path(path)

	def update_path(self,path):
		if path is None or len(path) == 0:
			self.path=""
			self.abspath=FILEMANAGER_DIRECTORY
		else:
			self.path=self.validate_path(path)
			self.abspath=os.path.join(FILEMANAGER_DIRECTORY,self.path)
		self.location=os.path.join(settings.MEDIA_ROOT,self.abspath)

	def remove_slashes(self,path,sep):
		path=[e for e in path.split(sep) if e]

		path=sep.join(path)

		return path

	def validate_path(self,path):
		if platform.system()=="Windows":
			# removing slashes according to the os
			path=path.replace("/","\\")

			#removing trailing slashes
			path=self.remove_slashes(path,"\\")
		else:
			path=path.replace("\\","/")

			path=self.remove_slashes(path,"/")

		return path


	def get_breadcrumbs(self):
		breadcrumbs=[{
		"label":"data",
		"path":""
		}]

		if platform.system()=="Windows":
			data=[e for e in self.location.split("\\") if e]
		else:
			data=[e for e in self.location.split("/") if e]

		path=""

		for label in data:
			path=os.path.join(path,label)
			breadcrumbs.append({
				"label":label,
				"path":path
				})

		return breadcrumbs

	def file_details(self):
		if platform.system()=="Windows":
			filename=self.location.split("\\")[-1]
		else:
			filename=self.location.split("/")[-1]

		return {
		"directory":os.path.dirname(self.location),
		"filename":filename,
		"filepath":self.location,
		"filesize":sizeof_fmt(default_storage.size(self.location)),
		"filedate":default_storage.get_modified_time(self.location)
		}

	def upload(self,filedata):
		filename=default_storage.get_valid_name(filedata.name)
		filepath=os.path.join(self.path,filename)

		#uploading the file in the directory
		default_storage.save(filepath,filedata)

		return filename



	def extract_zip(self,file,folder):
		with zipfile.ZipFile(file,'r') as zip_ref:
			zip_ref.extractall(folder)


	def delete(self,name):

		try:
			if platform.system()=="Windows":
				file=name.split("\\")[-1]
			else:
				file=name.split("/")[-1]
			filename=file.split(".")[0]
			path=os.path.dirname(name)

			directories,files=default_storage.listdir(path)

			if len(files) >= 1:
				for f in files:
					if filename == f.split(".")[0]:
						default_storage.delete(os.path.join(path,f))

			if len(directories) >=1:
				for d in directories:
					if filename == d.split(".")[0]:
						default_storage.delete(os.path.join(path,d))
			return True
		except Exception as e:
			if e.errno == 21:
				# path=name.replace("file://","")
				path=name
				self.__set_permission_to_dir(path,775)
				shutil.rmtree(path)
				return True
			if e.errno == 1:
				# path=name.replace("file://","")
				path=name
				self.__set_permission_to_dir(path,775)
				shutil.rmtree(path)
				return True
			return False


	def __set_permission_to_dir(self,directory_path,permission):
		for root, directory, files in os.walk(directory_path):
			for momo in directory:
				self.__set_permission_to_dir(os.path.join(root,momo),permission)
			for momo in files:
				try:
					os.chmod(os.path.join(root,momo),permission)
				except Exception as e:
					pass

	def geojson_to_shape(self,geojson_file):
		path=self.validate_path(self.location)
		shp_path=os.path.join(path,geojson_file.name.split(".")[0])
		file_path=os.path.join(self.location,geojson_file.name)
		try:
			response=True
			default_storage.save(file_path,geojson_file)
			if not geojson_to_shape_convertor(file_path,shp_path):
				response = {
				"message":"There is some issue while converting geojson to shapefile",
				"status":"error"
				}
			default_storage.delete(file_path)

			return response
		except IOError as e:
			return {
			"message":"There is some issue while reading or writing the file",
			"status":"error"
			}
		

__filemanager=None

def get_instance(path=None):
	global __filemanager
	if __filemanager is None:
		__filemanager=FileManager(path)
	return __filemanager

def reset_instance(path=None):
	global __filemanager
	__filemanager=FileManager(path)
	return __filemanager