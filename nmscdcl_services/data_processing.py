import json
from .utils import read_geojson
from KrushiGram.settings import ACTION_INSERT,ACTION_UPDATE,\
ACTION_DELETE,EDIT_TYPE_SPATIAL,EDIT_TYPE_NON_SPATIAL,EDIT_TYPE_ALL,GEOMETRY_TYPE_POLYGON,\
GEOMETRY_TYPE_LINESTRING

class DataProcessing(object):

	def __init__(self,ds):
		self.ds = ds
		self.Introspect , self.params = self.ds.get_db_connection()

	def GetDataByQuery(self,crs,query,table_name):
		# select_stmt,where_stmt = query.split("*") #temporary
		schema_name = self.params.get("schema","public")
		geometry_field = self.Introspect.get_geometry_field(table = table_name,schema = schema_name)
		attributes = self.Introspect.get_attribute_fields(table = table_name,schema = schema_name)

		if not geometry_field:
			return {
			"message":"There is no geometry field in table %s"%(table_name),
			"status":"error"
			}

		# raw_data = self.Introspect.query_db("""
		# 	SELECT row_to_json(fc) FROM ({query}) as fc
		# 	""".format(query=query))

		data = self.Introspect.query_db(crs,query,attributes,geometry_field[0])

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		if data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data for the non spatial query"%(table_name),
			"status":"error"
			}

		self.Introspect.close()
		return data[0],


	def SQLFieldMapValidator(self,data,fields,pk_fields,table_name,geometry_field=None,action=ACTION_UPDATE,editType = EDIT_TYPE_ALL):
		update_fields = {}
		if action == ACTION_DELETE:
			pk_field = ""
			if len(pk_fields) == 1:
				if pk_fields[0] in data.keys():
					pk_field = pk_fields[0]
				else:
					return {
					"message":"the primary key field is either not present in %s %s field or not valid for table %s"%(editType,action,table_name),
					"status":"error"
					}
			else:
				pk_field = "ogc_fid"

			update_fields = {pk_field:data[pk_field]}

			return pk_field,update_fields
		for i in data["properties"].keys():
			if i not in fields:
				return {
				"message":"the field %s is not a valid field name for table %s"%(i,table_name),
				"status":"error"
				}
		if action != ACTION_INSERT:
			pk_field = ""
			if len(pk_fields) == 1:
				if pk_fields[0] in data["properties"].keys():
					pk_field = pk_fields[0]
				else:
					return {
					"message":"the primary key field is either not present in %s %s field or not valid for table %s"%(editType,action,table_name),
					"status":"error"
					}
			else:
				pk_field = "ogc_fid"

			# geo_field = {pk_field:data["properties"][pk_field],geometry_field[0]:(data["geometry"])}
			geo_field = {pk_field:data["properties"][pk_field],geometry_field[0]:(data.get("geometry",{}))}
		else:
			geo_field = {geometry_field[0]:(data["geometry"])}

		if editType == EDIT_TYPE_SPATIAL:
			update_fields = geo_field
		elif editType == EDIT_TYPE_NON_SPATIAL:
			update_fields = data["properties"]
		else:
			update_fields = dict({**data["properties"],**geo_field}.items())

		if action == ACTION_INSERT:
			return update_fields,
		return pk_field,update_fields


	def UpdateData(self,data,srs,table_name,action,editType):
		# table_name = layer.name
		schema_name = self.params.get("schema","public")
		fields = self.Introspect.get_fields(table=table_name,schema=schema_name)
		pk_fields = self.Introspect.get_pk_columns(table=table_name,schema=schema_name)
		geometry_field = self.Introspect.get_geometry_field(table = table_name,schema = schema_name)

		if not geometry_field:
			return {
			"message":"There is no geometry field in table %s"%(table_name),
			"status":"error"
			}


		data_list = read_geojson(data)
		# data_list = [data]

		if not isinstance(data_list,list):
			return {
			"message":"data should be a valid geojson or valid geojson array",
			"status":"error"
			}

		for dt in data_list:
			validated_data = self.SQLFieldMapValidator(dt,fields,pk_fields,table_name,
				geometry_field,action,editType)
			if isinstance(validated_data,dict):
				return validated_data
			else:
				pk_field,update_fields = validated_data

			status = self.Introspect.update_data(update_fields,pk=pk_field,
				editType=editType,srs=srs,geo_field=geometry_field[0],
				table=table_name,schema=schema_name)
			if isinstance(status,dict):
				self.Introspect.close()
				return status

		if status:
			self.Introspect.close()
			return True
		return False


	def InsertData(self,data,srs,table_name,action,editType):
		schema_name = self.params.get("schema","public")
		fields = self.Introspect.get_fields(table=table_name,schema=schema_name)
		pk_fields = self.Introspect.get_pk_columns(table=table_name,schema=schema_name)
		geometry_field = self.Introspect.get_geometry_field(table = table_name,schema = schema_name)

		if not geometry_field:
			return {
			"message":"There is no geometry field in table %s"%(table_name),
			"status":"error"
			}

		data_list = read_geojson(data)

		if not isinstance(data_list,list):
			return {
			"message":"data should be a valid json or valid json array",
			"status":"error"
			}


		for dt in data_list:
			validated_data = self.SQLFieldMapValidator(dt,fields,pk_fields,table_name,
				geometry_field,action,editType)
			if isinstance(validated_data,dict):
				return validated_data
			else:
				update_fields, = validated_data

			status = self.Introspect.insert_data(update_fields,
				srs=srs,geo_field=geometry_field[0],
				table=table_name,schema=schema_name)
			if isinstance(status,dict):
				self.Introspect.close()
				return status

		if status:
			self.Introspect.close()
			return True
		return False


	def DeleteData(self,data,srs,table_name,action,editType):
		schema_name = self.params.get("schema","public")
		fields = self.Introspect.get_fields(table=table_name,schema=schema_name)
		pk_fields = self.Introspect.get_pk_columns(table=table_name,schema=schema_name)

		validated_data = self.SQLFieldMapValidator(data,fields,pk_fields,table_name,
			action=action,editType=editType)
		if isinstance(validated_data,dict):
			return validated_data
		else:
			pk_field,update_fields = validated_data

		status = self.Introspect.delete_data(update_fields,pk=pk_field,
			table=table_name,schema=schema_name)
		if isinstance(status,dict):
			self.Introspect.close()
			return status

		if status:
			self.Introspect.close()
			return True
		return False

	def GetAttributeDataForCsv(self,table_name):
		schema_name = self.params.get("schema","public")
		geometry_field = self.Introspect.get_geometry_field(table = table_name,schema = schema_name)[0]

		if not geometry_field:
			return {
			"message":"There is no geometry field in table %s"%(table_name),
			"status":"error"
			}

		attributes = self.Introspect.get_attr_data(table = table_name, geometry_field = geometry_field , schema = schema_name)

		if isinstance(attributes,dict):
			self.Introspect.close()
			return attributes

		data,columns = attributes

		if not columns:
			self.Introspect.close()
			return {
			"message":"There are not any columns in table %s"%(table_name),
			"status":"error"
			}
		elif not data:
			self.Introspect.close()
			return {
			"message":"there are no data in table %s"%(table_name),
			"status":"error"
			}
		return data,columns,geometry_field


	def GetAttributeDataForGeoJson(self,table_name):
		schema_name = self.params.get("schema","public")
		geometry_field = self.Introspect.get_geometry_field(table = table_name,schema = schema_name)[0]

		if not geometry_field:
			return {
			"message":"There is no geometry field in table %s"%(table_name),
			"status":"error"
			}

		attributes = self.Introspect.get_attribute_fields(table = table_name,schema = schema_name)
		json_stmt = ', '.join(f"'{column}', l.{column}" for column in attributes)

		data = self.Introspect.get_attr_geojson(json_stmt,geometry_field ,table_name,schema_name)

		if not data:
			self.Introspect.close()
			return {
			"message":"there is not any data in table %s"%(table_name),
			"status":"error"
			}
		return data


	def GetNonSpatialColumnNames(self,table_name):
		schema_name = self.params.get("schema","public")
		attributes = self.Introspect.get_attribute_fields(table = table_name,schema = schema_name)

		if not attributes:
			self.Introspect.close()
			return {
			"message":"There are not any attribute field in table %s"%(table_name),
			"status":"error"
			}
		self.Introspect.close()
		return attributes

	def GetTableNames(self):
		schema_name = self.params.get("schema","public")
		database_name = self.params.get("database",None)
		table_names = self.Introspect.get_table_names(schema = schema_name)

		if not table_names:
			self.Introspect.close()
			return {
			"message":"There is not any table in database %s"%(database_name),
			"status":"error"
			}
		self.Introspect.close()
		return table_names

	def GetUniqueValues(self,table_name,column_name):
		schema_name = self.params.get("schema","public")
		fields = self.Introspect.get_attribute_fields(table=table_name,schema=schema_name)
		if column_name in fields:
			unique_values = self.Introspect.get_unique_values(column_name,table = table_name,schema = schema_name)
		else:
			return {
			"message":"Table %s does not contains Attribute column %s"%(table_name,column_name),
			"status":"error"
			}

		if not unique_values or (len(unique_values) == 1 and unique_values[0] == None):
			self.Introspect.close()
			return {
			# "message":"There is not any values in column %s of table %s"%(column_name,table_name),
			"message":"No data",
			"status":"error"
			}

		self.Introspect.close()
		return unique_values

	def GetAttributeData(self,table_name,limit,offset):
		schema_name = self.params.get("schema","public")
		attributes = self.Introspect.get_attribute_fields(table = table_name,schema = schema_name)
		pk_fields = self.Introspect.get_pk_columns(table=table_name,schema=schema_name)

		pk_field = ""
		if len(pk_fields) == 1:
			if pk_fields[0] in attributes:
				pk_field = pk_fields[0]
			else:
				return {
				"message":"the primary key field is not valid for table %s"%(table_name),
				"status":"error"
				}
		else:
			pk_field = "ogc_fid"

		count = self.Introspect.get_count(table = table_name,schema = schema_name)

		if limit == 0:
			limit = count
			offset=0

		data = self.Introspect.get_attribute_data(attributes,pk_field,limit,offset,table = table_name,schema = schema_name)

		if not count:
			self.Introspect.close()
			return {
			"message":"There is not any data in table %s"%(table_name),
			"status":"error"
			}

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		self.Introspect.close()
		return data[0],count


	def GetAttributeJsonData(self,table_name,limit,offset):
		schema_name = self.params.get("schema","public")
		attributes = self.Introspect.get_attribute_fields(table = table_name,schema = schema_name)
		pk_fields = self.Introspect.get_pk_columns(table=table_name,schema=schema_name)

		pk_field = ""
		if len(pk_fields) == 1:
			if pk_fields[0] in attributes:
				pk_field = pk_fields[0]
			else:
				return {
				"message":"the primary key field is not valid for table %s"%(table_name),
				"status":"error"
				}
		else:
			pk_field = "ogc_fid"

		count = self.Introspect.get_count(table = table_name,schema = schema_name)

		if limit == 0:
			limit = count
			offset=0

		data = self.Introspect.get_attribute_data_json(attributes,pk_field,limit,offset,table = table_name,schema = schema_name)

		if not count:
			self.Introspect.close()
			return {
			"message":"There is not any data in table %s"%(table_name),
			"status":"error"
			}

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		self.Introspect.close()
		return data,count


	def NonSpatialRelationship(self,table_name1,table_name2):
		schema_name = self.params.get("schema","public")
		geometry_field1 = self.Introspect.get_geometry_field(table = table_name1,schema = schema_name)
		geometry_field2 = self.Introspect.get_geometry_field(table = table_name2,schema = schema_name)

		if not geometry_field1:
			return {
			"message":"There is no geometry field in table %s"%(table_name1),
			"status":"error"
			}

		if not geometry_field2:
			return {
			"message":"There is no geometry field in table %s"%(table_name2),
			"status":"error"
			}

		return schema_name,geometry_field1,geometry_field2



	def GetIntersect(self,table_name1,table_name2,crs):
		prerequisite = self.NonSpatialRelationship(table_name1,table_name2)

		if isinstance(prerequisite,dict):
			self.Introspect.close()
			return prerequisite

		schema_name,geometry_field1,geometry_field2 = prerequisite

		data = self.Introspect.get_intersect(crs,table_name1,geometry_field1[0],table_name2,
			geometry_field2[0],schema_name)

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		if data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any common data in table %s and table %s"%(table_name1,table_name2),
			"status":"error"
			}

		self.Introspect.close()
		return data[0],


	def AreWithin(self,table_name1,table_name2,crs,distance=None):
		prerequisite = self.NonSpatialRelationship(table_name1,table_name2)

		if isinstance(prerequisite,dict):
			self.Introspect.close()
			return prerequisite

		schema_name,geometry_field1,geometry_field2 = prerequisite

		if distance:
			if "km" in distance.lower():
				within_distance = float(distance.replace("km",""))*(1000)
			elif "m" in distance.lower():
				within_distance = float(distance.replace("m",""))
			else:
				return {
				"message":"Invalid buffer size",
				"status":"error"
				}
		else:
			within_distance = distance

		data = self.Introspect.are_within(crs,within_distance,table_name1,geometry_field1[0],table_name2,
			geometry_field2[0],schema_name)

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		print(data,"aljdjd")
		if data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data in table %s that is within table %s"%(table_name1,table_name2),
			"status":"error"
			}

		self.Introspect.close()
		return data[0],


	def Contains(self,table_name1,table_name2,crs,complete=True):
		prerequisite = self.NonSpatialRelationship(table_name1,table_name2)

		if isinstance(prerequisite,dict):
			self.Introspect.close()
			return prerequisite

		schema_name,geometry_field1,geometry_field2 = prerequisite

		data = self.Introspect.contains(crs,complete,table_name1,geometry_field1[0],table_name2,
			geometry_field2[0],schema_name)

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		if data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data in table %s that contains data in table %s"%(table_name1,table_name2),
			"status":"error"
			}

		self.Introspect.close()
		return data[0],

	def LayerTouches(self,table_name1,table_name2,crs):
		prerequisite = self.NonSpatialRelationship(table_name1,table_name2)

		if isinstance(prerequisite,dict):
			self.Introspect.close()
			return prerequisite

		schema_name,geometry_field1,geometry_field2 = prerequisite

		data = self.Introspect.layer_touches(crs,table_name1,geometry_field1[0],table_name2,
			geometry_field2[0],schema_name)

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		if data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data in table %s that touches data in table %s"%(table_name1,table_name2),
			"status":"error"
			}

		self.Introspect.close()
		return data[0],


	def LayerIdentical(self,table_name1,table_name2,crs):
		prerequisite = self.NonSpatialRelationship(table_name1,table_name2)

		if isinstance(prerequisite,dict):
			self.Introspect.close()
			return prerequisite

		schema_name,geometry_field1,geometry_field2 = prerequisite

		data = self.Introspect.layer_identical(crs,table_name1,geometry_field1[0],table_name2,
			geometry_field2[0],schema_name)

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		if data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data in table %s that is identical with data in table %s"%(table_name1,table_name2),
			"status":"error"
			}

		self.Introspect.close()
		return data[0],


	def LayerCentroidIn(self,table_name1,table_name2,crs):
		prerequisite = self.NonSpatialRelationship(table_name1,table_name2)

		if isinstance(prerequisite,dict):
			self.Introspect.close()
			return prerequisite

		schema_name,geometry_field1,geometry_field2 = prerequisite

		data = self.Introspect.layer_centroid_in(crs,table_name1,geometry_field1[0],table_name2,
			geometry_field2[0],schema_name)

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		if data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data in layer %s that have their centroid in layer %s"%(table_name1,table_name2),
			"status":"error"
			}

		self.Introspect.close()
		return data[0],


	def LayerSharesLineSegment(self,table_name1,table_name2,crs):
		prerequisite = self.NonSpatialRelationship(table_name1,table_name2)

		if isinstance(prerequisite,dict):
			self.Introspect.close()
			return prerequisite

		schema_name,geometry_field1,geometry_field2 = prerequisite

		geometry_type1 = self.Introspect.get_geometry_type(geometry_field1[0],table_name1,schema_name)

		if isinstance(geometry_type1,dict):
			self.Introspect.close()
			return geometry_type1
		elif not geometry_type1:
			return {
			"message":"geometry type is not there for the layer %s"%(table_name1),
			"status":"error"
			}

		geometry_type2 = self.Introspect.get_geometry_type(geometry_field2[0],table_name2,schema_name)

		if isinstance(geometry_type2,dict):
			self.Introspect.close()
			return geometry_type2
		elif not geometry_type2:
			return {
			"message":"geometry type is not there for the layer %s"%(table_name2),
			"status":"error"
			}

		if GEOMETRY_TYPE_POLYGON.upper() in geometry_type1[0] or GEOMETRY_TYPE_LINESTRING.upper() in geometry_type1[0]:
			if GEOMETRY_TYPE_POLYGON.upper() in geometry_type1[0]:
				geom_type1 = GEOMETRY_TYPE_POLYGON
			else:
				geom_type1 = GEOMETRY_TYPE_LINESTRING
		else:
			self.Introspect.close()
			return {
			"message":"layer %s geometry should be either polygon or line to perform this query"%(table_name1),
			"status":"error"
			}

		if GEOMETRY_TYPE_POLYGON.upper() in geometry_type2[0] or GEOMETRY_TYPE_LINESTRING.upper() in geometry_type2[0]:
			if GEOMETRY_TYPE_POLYGON.upper() in geometry_type2[0]:
				geom_type2 = GEOMETRY_TYPE_POLYGON
			else:
				geom_type2 = GEOMETRY_TYPE_LINESTRING
		else:
			self.Introspect.close()
			return {
			"message":"layer %s geometry should be either polygon or line to perform this query"%(table_name2),
			"status":"error"
			}

		data = self.Introspect.layer_shares_line_segment(crs,table_name1,geometry_field1[0],
			geom_type1,table_name2,geometry_field2[0],geom_type2,schema_name)

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		if data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data in layer %s that share line segment with layer %s"%(table_name1,table_name2),
			"status":"error"
			}

		self.Introspect.close()
		return data[0],


	def LayersAreCrossedByTheLineOf(self,table_name1,table_name2,crs):
		prerequisite = self.NonSpatialRelationship(table_name1,table_name2)

		if isinstance(prerequisite,dict):
			self.Introspect.close()
			return prerequisite

		schema_name,geometry_field1,geometry_field2 = prerequisite

		# geometry_type1 = self.Introspect.get_geometry_type(geometry_field1[0],table_name1,schema_name)

		# if isinstance(geometry_type1,dict):
		# 	self.Introspect.close()
		# 	return geometry_type1
		# elif not geometry_type1:
		# 	return {
		# 	"message":"geometry type is not there for the layer %s"%(table_name1),
		# 	"status":"error"
		# 	}

		# geometry_type2 = self.Introspect.get_geometry_type(geometry_field2[0],table_name2,schema_name)

		# if isinstance(geometry_type2,dict):
		# 	self.Introspect.close()
		# 	return geometry_type2
		# elif not geometry_type2:
		# 	return {
		# 	"message":"geometry type is not there for the layer %s"%(table_name2),
		# 	"status":"error"
		# 	}

		# if GEOMETRY_TYPE_POLYGON.upper() in geometry_type1[0] or GEOMETRY_TYPE_LINESTRING.upper() in geometry_type1[0]:
		# 	if GEOMETRY_TYPE_POLYGON.upper() in geometry_type1[0]:
		# 		geom_type1 = GEOMETRY_TYPE_POLYGON
		# 	else:
		# 		geom_type1 = GEOMETRY_TYPE_LINESTRING
		# else:
		# 	self.Introspect.close()
		# 	return {
		# 	"message":"layer %s geometry should be either polygon or line to perform this query"%(table_name1),
		# 	"status":"error"
		# 	}

		# if GEOMETRY_TYPE_POLYGON.upper() in geometry_type2[0] or GEOMETRY_TYPE_LINESTRING.upper() in geometry_type2[0]:
		# 	if GEOMETRY_TYPE_POLYGON.upper() in geometry_type2[0]:
		# 		geom_type2 = GEOMETRY_TYPE_POLYGON
		# 	else:
		# 		geom_type2 = GEOMETRY_TYPE_LINESTRING
		# else:
		# 	self.Introspect.close()
		# 	return {
		# 	"message":"layer %s geometry should be either polygon or line to perform this query"%(table_name2),
		# 	"status":"error"
		# 	}

		data = self.Introspect.layers_are_crossed_by_the_line_of(crs,table_name1,geometry_field1[0],
			table_name2,geometry_field2[0],schema_name)

		if isinstance(data,dict):
			self.Introspect.close()
			return data

		if data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data in layer %s that crossed by the line of layer %s"%(table_name1,table_name2),
			"status":"error"
			}

		self.Introspect.close()
		return data[0],


	def GetBuffer(self,crs,table_name,size,features=None):
		schema_name = self.params.get("schema","public")
		pk_fields = self.Introspect.get_pk_columns(table=table_name,schema=schema_name)
		geometry_field = self.Introspect.get_geometry_field(table = table_name,schema = schema_name)

		pk_field = ""
		if len(pk_fields) == 1:
			pk_field = pk_fields[0]
		else:
			pk_field = "ogc_fid"

		if "km" in size.lower():
			buffer_size = float(size.replace("km",""))*(1000)
		elif "m" in size.lower():
			buffer_size = float(size.replace("m",""))
		else:
			self.Introspect.close()
			return {
			"message":"Invalid buffer size It should like ex: '10m' or '10km'",
			"status":"error"
			}

		if features and (not isinstance(features,list) and isinstance(features,int)):
			features = [features]
		elif features and not isinstance(features,list):
			self.Introspect.close()
			return {
			"message":"features should be either in list or integer",
			"status":"error"
			}
		elif features and isinstance(features,list):
			features = list(map(int,features))


		buffer_data = self.Introspect.get_buffer(crs,buffer_size,pk_field,geometry_field[0],table_name,schema_name,features)

		if isinstance(buffer_data,dict):
			self.Introspect.close()
			return buffer_data

		if buffer_data[0].get("features") == None:
			self.Introspect.close()
			if features:
				msg = "There is not any data in table %s for features %s"%(table_name,features)
			else:
				msg = "There is not any data in table %s"%(table_name)
			return {
			"message":msg,
			"status":"error"
			}

		self.Introspect.close()

		return buffer_data[0],

	def GetClip(self,crs,table_name,clip_geom,native_crs):
		schema_name = self.params.get("schema","public")
		geometry_field = self.Introspect.get_geometry_field(table = table_name,schema = schema_name)

		data_list = read_geojson(clip_geom)

		if not isinstance(data_list,list):
			self.Introspect.close()
			return {
			"message":"data should be a valid geojson or valid geojson array",
			"status":"error"
			}
		elif len(data_list) != 1:
			self.Introspect.close()
			return {
			"message":"there should be only one geojson.. required for Clip function",
			"status":"error"
			}

		clip_geometry = data_list[0]["geometry"]

		clip_data = self.Introspect.get_clip(geometry_field[0],crs,clip_geometry,native_crs,table_name,schema_name)

		if isinstance(clip_data,dict):
			self.Introspect.close()
			return clip_data

		if clip_data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data for the clip geometry you passed in layer %s"%(table_name),
			"status":"error"
			}

		self.Introspect.close()
		return clip_data[0],


	def GetErase(self,crs,table_name,erase_geom,native_crs):
		schema_name = self.params.get("schema","public")
		geometry_field = self.Introspect.get_geometry_field(table = table_name,schema = schema_name)

		data_list = read_geojson(erase_geom)

		if not isinstance(data_list,list):
			self.Introspect.close()
			return {
			"message":"data should be a valid geojson or valid geojson array",
			"status":"error"
			}
		elif len(data_list) != 1:
			self.Introspect.close()
			return {
			"message":"there should be only one geojson.. required for Erase function",
			"status":"error"
			}

		erase_geometry = data_list[0]["geometry"]

		erase_data = self.Introspect.get_erase(geometry_field[0],crs,erase_geometry,native_crs,table_name,schema_name)

		if isinstance(erase_data,dict):
			self.Introspect.close()
			return erase_data

		if erase_data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data for the Erase geometry you passed in layer %s"%(table_name),
			"status":"error"
			}

		self.Introspect.close()
		return erase_data[0],


	def GetSplit(self,crs,table_name,split_geom,native_crs):
		schema_name = self.params.get("schema","public")
		geometry_field = self.Introspect.get_geometry_field(table = table_name,schema = schema_name)

		data_list = read_geojson(split_geom)

		if not isinstance(data_list,list):
			self.Introspect.close()
			return {
			"message":"data should be a valid geojson or valid geojson array",
			"status":"error"
			}
		elif len(data_list) != 1:
			self.Introspect.close()
			return {
			"message":"there should be only one geojson.. required for split function",
			"status":"error"
			}

		split_geometry = data_list[0]["geometry"]

		split_data = self.Introspect.get_split(geometry_field[0],crs,split_geometry,native_crs,table_name,schema_name)

		if isinstance(split_data,dict):
			self.Introspect.close()
			return split_data

		if split_data[0].get("features") == None:
			self.Introspect.close()
			return {
			"message":"There is not any data for the split geometry you passed in layer %s"%(table_name),
			"status":"error"
			}

		self.Introspect.close()
		return split_data[0],
