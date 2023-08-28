from .backend_postgis import Introspect
import gdaltools
import logging
from dbfread import DBF
from KrushiGram import settings
from KrushiGram.settings import CONTROL_FIELDS , MODE_CREATE, MODE_OVERWRITE , MODE_APPEND
import re
import json
import os
# from django.conf import api_settings
from pathlib import Path
from osgeo import osr
import geoserver.catalog as gscat
from django.utils.translation import gettext_lazy as _
from . import rest_geoserver
from .rest_geoserver import RequestError
from rest_framework.response import Response



class InvalidValue(RequestError):
    pass

_valid_sql_name_regex=re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")

class Geoserver(): #need to fixed

    supported_crs=list(settings.SUPPORTED_CRS.values())
    supported_encodings=tuple((item,item) for item in settings.SUPPORTED_ENCODINGS)
    supported_encodings=supported_encodings+(("autodetect","autodetect"),)

    supported_srs=tuple((item["code"],item["code"]+"-"+item["title"]) for item in supported_crs)

    supported_srs_plain=[i[0] for i in supported_srs]
    supported_encodings_plain=[i[0] for i in supported_encodings]

    def __init__(self,id,default,name,user,password,master_node):
        self.id = id
        self.default = default
        self.name = name
        self.conf_url = master_node
        self.rest_url = master_node + "/rest"
        self.gwc_url = master_node + "/gwc/rest"
        # self.slave_node = slave_node
        self.rest_catalog = rest_geoserver.Geoserver(self.rest_url, self.gwc_url)
        self.user = user
        self.password=password
        self.supported_types = (
            ('v_PostGIS', _('PostGIS vector')),
            ('c_GeoTIFF', _('GeoTiff')),
            ('e_WMS', _('Cascading WMS')),
            ('c_ImageMosaic', _('ImageMosaic')),
        )

    def getGsconfig(self):
        return gscat.Catalog(self.rest_url, self.user, self.password, validate_ssl_certificate=False)


    def reload_master(self):
        try:
            self.rest_catalog.reload(self.conf_url,user=self.user,password=self.password)
        except Exception as e:
            print("Error reloading geoserver cause: {val}".format(val=str(e)))


    def reload_node(self, node_url):
        try:
            self.rest_catalog.reload(node_url, user=self.user, password=self.password) 
            return True
        
        except Exception as e:
            print(str(e))
            return False

    def getGsLayers(self):
        catalog=self.getGsconfig()
        # resource=catalog.get_resources(workspaces="tiger")
        layer_data=catalog.get_layers()
        return layer_data

    def getGsLayer(self,layer_name):
        catalog=self.getGsconfig()
        layer_data=catalog.get_layer(name=layer_name)
        return layer_data


    def createDatastore(self,workspace,type,name,description,connection_params):

        try:
            format_type = type[:1]
            driver = type[2:]
            params = json.loads(connection_params)
            catalog = self.getGsconfig()
            if format_type == "v":
                schema = params.get("schema","public")
                params["schema"] = schema
                params["Expose primary keys"] = params.get("Expose primary keys","true")
                params["Loose bbox"] = params.get("Loose bbox","true")
                params["Support on the fly geometry simplification"] = params.get("Support on the fly geometry simplification","true")
                params["Estimated extends"] = params.get("Estimated extends","true")
                params["encode functions"] = params.get("encode functions","true")

                ds = catalog.create_datastore(name,workspace = workspace.name)
                ds.connection_parameters.update(params)
            elif format_type == "c":
                ds = catalog.create_coveragestore(name, workspace = workspace.name, path = params.get("url"), create_layer = False)
            else:
                return {
                "message":"unsupported data source type",
                "status":"error"
                }
            ds.type = driver
            # ds.description = description
            response = catalog.save(ds)
            if response.status_code == 201:
                return True
        except Exception as e:
            return {
            "message":"exception occured while creating data source",
            "status":"error",
            "error":str(e)
            }


    def createLayer(self,workspace,datastore,name,title):

        try:
            format_type = datastore.type

            if format_type.startswith("v"):
                self.rest_catalog.create_feature_type(workspace.name,datastore.name,name,
                    title,user=self.user,password=self.password)
                return True
            elif format_type.startswith("c"):
                self.rest_catalog.create_coverage(workspace.name,datastore.name,name,
                    title,user=self.user,password=self.password)
                return True
            else:
                return {
                "message":"unsupported data source type",
                "status":"error"
                }
        except RequestError as e:
            return {
            "message":"issue occured while publishing layer %s"%(name),
            "status":"error",
            "error":e.get_detailed_message()
            }
        except Exception as e:
            return {
            "message":"exception occured while publishing the layer %s"%(name),
            "status":"error",
            "error":e.get_detailed_message()
            }


    def deleteLayer(self,workspace,datastore,name):

        try:
            format_type = datastore.type
            if format_type.startswith("v"):
                self.rest_catalog.delete_feature_type(workspace.name,datastore.name,name,
                    recurse = True,user=self.user,password=self.password)
                return True
            elif format_type.startswith("c"):
                self.rest_catalog.delete_coverage(workspace.name,datastore.name,name,
                    recurse = True,user=self.user,password=self.password)
                return True
            else:
                return {
                "message":"unsupported data source type",
                "status":"error"
                }
        except RequestError as e:
            return {
            "message":"issue occured while deleting layer %s"%(name),
            "status":"error",
            "error":e.get_detailed_message()
            }
        except Exception as e:
            return {
            "message":"exception occured while publishing the layer %s"%(name),
            "status":"error",
            "error":e.get_detailed_message()
            }

    def __field_mapping_sql(self,creation_mode,shp_path,shp_fields,db,host,port,user,password,table_name,schema):
        if creation_mode == settings.MODE_CREATE:
            return

        i=Introspect(db,host=host,port=port,user=user,password=password)
        db_fields=i.get_fields(table_name,schema=schema)
        db_pks=i.get_pk_columns(table_name,schema=schema)
        i.close()
        if len(db_pks) ==1:
            db_pk=db_pks[0]
        else:
            db_pk="ogc_fid"

        if "ogc_fid" in shp_fields:
            pk="ogc_fid"
        elif db_pk in shp_fields:
            pk=db_pk
        else:
            pk=None

        fields=[]
        pending=[]

        for i in shp_fields:
            if i == pk:
                fields.append(' "'+i+'" as ogc_fid')
            elif i in db_fields:
                control_fields=next((f for f in CONTROL_FIELDS if f.get("name") == i),None)
                if control_fields:
                    if creation_mode == MODE_APPEND:
                        #Skip the control fields in append mode
                        continue
                    elif control_fields.get("type","").startswith("timestamp"):
                            fields.append('CAST("' + i + '" AS timestamp)')
                            continue
                fields.append('"' + i + '"')
            else:
                pending.append(i)

        if (pk is None or pk == "ogc_fid") and len(pending) == 0:
            #No mappig needed if aboves condition satisfies
            return

        for i in pending:
            
            #try to find mapping
            db_mapped_field=None

            for db_field in db_fields:
                if db_field.startswith(i):
                    db_mapped_field=db_field
                elif db_field.startswith(i.rstrip("0123456789")):
                    db_mapped_field=db_field

            if db_mapped_field:
                control_fields=next((f for f in CONTROL_FIELDS if f.get("name") == db_mapped_field),None)
                if control_fields:
                    if creation_mode == MODE_APPEND:
                        #skip control fields in append mode
                        continue
                    elif control_fields.get("type","").startswith("timestamp"):
                        fields.append('CAST("' + i + '" AS timestamp) as "' + db_mapped_field + '"')
                        db_fields.remove(db_mapped_field)
                        continue
                fields.append('"' + i + '" as "' + db_mapped_field + '"')
                db_fields.remove(db_mapped_field)
            else:
                fields.append('"' + i + '"')

        sql=f"SELECT {','.join(fields)} FROM {table_name}"

        return sql



    def shp2postgis(self,creation_mode,encoding,shp_path,srs,host,port,dbname,schema,user,password,table_name,sql=None):
        ogr=gdaltools.ogr2ogr()
        ogr.set_encoding(encoding)
        ogr.set_input(shp_path,srs=srs)

        conn=gdaltools.PgConnectionString(host=host,port=port,dbname=dbname,schema=schema,user=user,password=password)

        ogr.set_output(conn,table_name=table_name)

        if creation_mode == settings.MODE_CREATE:
            ogr.set_output_mode(layer_mode=ogr.MODE_LAYER_CREATE, data_source_mode=ogr.MODE_DS_UPDATE)
        if creation_mode == settings.MODE_APPEND:
            ogr.set_output_mode(layer_mode=ogr.MODE_LAYER_APPEND, data_source_mode=ogr.MODE_DS_UPDATE)
        if creation_mode == settings.MODE_OVERWRITE:
            ogr.set_output_mode(layer_mode=ogr.MODE_LAYER_OVERWRITE, data_source_mode=ogr.MODE_DS_UPDATE)

        ogr.layer_creation_options = {
            "LAUNDER":"YES",
            "precision":"NO"
        }

        ogr.config_options = {
            "OGR_TRUNCATE":"NO"
        }

        ogr.set_sql(sql)
        ogr.set_dim("2")
        ogr.geom_type = "PROMOTE_TO_MULTI"

        ogr.execute()

        # print(" ".join(ogr.safe_args))

        return ogr.stderr if ogr.stderr is not None else ''


    # def shp2postgis(self,creation_mode,encoding,shp_path,srs,host,port,dbname,schema,user,password,table_name,sql=None):
    #     db_schema = "SCHEMA=public"
    #     overwrite_option = "OVERWRITE=YES"
    #     geom_type = "POINT"
    #     output_format = "PostgreSQL"

    #     # database connection string
    #     db_connection = """PG:host=localhost port=5432
    #       user=postgres dbname=nmscdcl password=bgis@123"""

    #     # input shapefile
    #     input_shp = shp_path

    #     # call ogr2ogr from python
    #     subprocess.call(["ogr2ogr","-lco", db_schema, "-lco", overwrite_option, "-nlt", geom_type, "-f", output_format, db_connection,  input_shp])

    #     return ''



    def __do_export_to_postgis(self,name,datastore,layer_data,shp_path,shp_fields):
        try:
            name=name.lower()
            srs=layer_data["srs"]
            mode=layer_data["creationMode"]
            encoding=layer_data["encoding"]

            if encoding not in self.supported_encodings_plain:
                raise InvalidValue(-1,"encoding : {val} is not supported".format(val=encoding))

            params=json.loads(datastore.connection_params)
            host=params.get("host")
            port=str(int(params.get("port")))
            db=params.get("database")
            schema=params.get("schema","public")
            user=params.get("user")
            password=params.get("passwd")


            if _valid_sql_name_regex.search(name) == None:
                raise InvalidValue(-1,"Invalid layer name : {layer} layer name should start with\
                    character or underscore and subsequent characters could be characters,numbers or \
                    underscore".format(layer=name))
            if _valid_sql_name_regex.search(db) == None:
                raise InvalidValue(-1,"The connection parameters contain an invalid database name : {dbname},\
                    database name should start with character or underscore and subsequent characters\
                    could be characters,numbers or underscore".format(dbname=db))
            if _valid_sql_name_regex.search(schema) == None:
                raise InvalidValue(-1,"The connection parameters contain an invalid schema name : {schemaname},\
                    schema name should start with character or underscore and subsequent characters\
                    could be characters,numbers or underscore".format(schemaname=schema))
            if _valid_sql_name_regex.search(user) == None:
                raise InvalidValue(-1,"The connection parameters contain an invalid user name : {username},\
                    user name should start with character or underscore and subsequent characters\
                    could be characters,numbers or underscore".format(username=user))
            shp_field_names=tuple(i.name for i in shp_fields)

            sql=self.__field_mapping_sql(mode,shp_path,shp_field_names,db,host,port,user,password,name,schema)
            stderr=self.shp2postgis(mode,encoding,shp_path,srs,host,port,db,schema,user,password,name,sql)
            
            if stderr.startswith("ERROR"): # some errors don't return non-0 status so will not directly raise an exception
                raise RequestError(-1,stderr)

            with Introspect(db,host=host,port=port,user=user,password=password) as i:
                db_fields=i.get_fields(name,schema=schema)

                for f in CONTROL_FIELDS:
                    has_control_field=False
                    for db_field in db_fields:
                        if f.get("name") == db_field:
                            try:
                                i.set_field_default(schema,table=name,field=f.get("name"),default_value=f.get("default"))
                            except:
                                return {
                                "message":"Error setting default value for control field %s"%(f.get("name")),
                                "status":"error"
                                }
                            has_control_field=True
                    if not has_control_field:
                        try:
                            i.add_column(schema,table_name=name,column_name=f.get("name"),sql_type=f.get("type"),nullable=f.get("nullable",True),default=f.get("default"))
                        except:
                            return {
                            "message":"Error adding control field %s"%(f.get("name")),
                            "status":"error"
                            }
                if mode == settings.MODE_OVERWRITE:
                    i.update_pk_sequences(name,schema=schema)
            # update layer feature for geoserver after update in postgres
            # for layer in Layer.objects.filter(datastore=datastore,source_name=name):
            if not stderr:
                return True
        except RequestError as e:
            return {
            "message":"exception occured while exporting layer to postgis",
            "status":"error",
            "error":str(e)
            }
        except gdaltools.GdalToolsError as e:
            if e.code > 0 and mode == settings.MODE_OVERWRITE:
                params=json.loads(datastore.connection_params)
                host=params.get("host")
                port=str(int(params.get("port")))
                db=params.get("database")
                schema=params.get("schema","public")
                user=params.get("user")
                password=params.get("passwd")

                i=Introspect(db,host=host,port=port,user=user,password=password)
                i.delete_table(schema,table_name=name)
                i.close()
                try:
                    stderr=self.shp2postgis(mode,encoding,shp_path,srs,host,port,db,schema,user,password,name)
                    if stderr:
                        raise RequestError(-1,stderr)
                    return True
                except gdaltools.GdalToolsError as e:
                    raise RequestError(e.code,str(e))
            raise RequestError(e.code,str(e))
        except Exception as e:
            message="error uploading the layer. review file format. cause: {val}".format(val=str(e))
            raise RequestError(-1,message)
        raise RequestError(-1,stderr)




    
    def get_fields_from_shp(self,shp_path):
        dbf_path=shp_path.replace(".shp",".dbf").replace(".SHP",".dbf")
        if not os.path.isfile(dbf_path):
            dbf_path=dbf_path.replace(".dbf",".DBF")
        dbf_fields=DBF(dbf_path)

        return dbf_fields.fields


    def exportShpToPostgis(self,layer_data):
        name=layer_data["name"]
        ds=layer_data["datastore"]
        shp_path=layer_data["shp_path"]

        fields=self.get_fields_from_shp(shp_path)

        if fields:
            for field in fields:
                if ' ' in field.name:
                    raise InvalidValue(-1,"Invalid field name : {value} it cannot contain whitespaces".format(value=field))
        else:
            raise InvalidValue(-1,"there is some error reading dbf file")


        if _valid_sql_name_regex.search(name) == None:
            raise InvalidValue(-1,"Invalid layer name : {name} , layer should start with either \
                character or underscore and subsequent characters could be alphabets,\
                 numbers or underscore".format(name=name))


        try:
            exported_layer = self.__do_export_to_postgis(name,ds,layer_data,shp_path,fields)
            if isinstance(exported_layer, dict):
                return exported_layer
            else:
                return True
        except Exception as e:
            return {
            "message":"exception occurred while exporting layer to postgis",
            "status":"error",
            "error":str(e)
            }
