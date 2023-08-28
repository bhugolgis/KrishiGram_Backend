from osgeo import gdal
import sys

def sizeof_fmt(num):
	"""
	get human readable file size
	"""
	for i in ["bytes","KB","MB","GB"]:
		if num < 1024.0 and num > -1024.0:
			return "%3.1f %s"%(num,i)
		num=num/1024.0
	return "%3.1f %s"%(num,"TB")

def geojson_to_shape_convertor(src_path,dest_path):
	gdal.UseExceptions()
	try:
		#Opening the source geojson file to convert
		src=gdal.OpenEx(src_path)
		#Converting the geojson file to shape file 
		dest=gdal.VectorTranslate(dest_path, src, format='ESRI Shapefile')

		return True
	except Exception as e:
		print(e)
		return False