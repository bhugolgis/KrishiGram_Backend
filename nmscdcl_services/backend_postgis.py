import psycopg2
from psycopg2 import sql as sqlbuilder
from psycopg2.extensions import quote_ident
import re
import random, string
from .utils import FormSQL
from KrushiGram.settings import EDIT_TYPE_SPATIAL,EDIT_TYPE_NON_SPATIAL,EDIT_TYPE_ALL,\
GEOMETRY_TYPE_POLYGON,GEOMETRY_TYPE_LINESTRING
import logging

logger = logging.getLogger("nmscdcl")


plainIdentifierPattern = re.compile("^[a-zA-Z][a-zA-Z0-9_]*$")
plainSchemaIdentifierPattern = re.compile("^[a-zA-Z][a-zA-Z0-9_]*(.[a-zA-Z][a-zA-Z0-9_]*)?$")

class Introspect:
    def __init__(self, database, host='localhost', port='5432', user='postgres', password='postgres'):
        self.conn = None
        self.database = database
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.__enter__()

    def __enter__(self):
        if not self.conn:
            self.conn = psycopg2.connect(database=self.database, user=self.user, password=self.password, host=self.host, port=self.port)
            delattr(self, 'user')
            delattr(self, 'password')
            self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
        return exc_type is None

    def get_geoserver_view_pk_columns(self, schema, table):
        try:
            query = sqlbuilder.SQL("""
            SELECT pk_column FROM {schema}.gt_pk_metadata WHERE table_name = %s AND table_schema = %s
            """).format(schema=sqlbuilder.Identifier(schema))
            self.cursor.execute(query, [table, schema])
            return [r[0] for r in self.cursor.fetchall()]
        except:
            # the table may not exist, this is not an error
            return []

    def get_pk_columns(self, table, schema='public'):
        qualified_table = quote_ident(schema, self.conn) + "." + quote_ident(table, self.conn) 

        query = sqlbuilder.SQL("""
        SELECT a.attname AS field_name
                        FROM pg_index i
                        JOIN pg_attribute a ON a.attrelid = i.indrelid
                        AND a.attnum = ANY(i.indkey)
                        WHERE
                        i.indrelid = ({schema_table})::regclass
                        AND i.indisprimary
        """).format(schema_table=sqlbuilder.Literal(qualified_table))
        self.cursor.execute(query)
        pks = self.cursor.fetchall()
        if len(pks) == 0 and self.is_view(schema, table):
            return self.get_geoserver_view_pk_columns(schema, table)
        return [r[0] for r in pks]

    def is_view(self, schema, table):
        query = "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = %s AND table_name = %s"
        self.cursor.execute(query, [schema, table])
        r = self.cursor.fetchone()
        return r[0] > 0


    #Data Introspection queries for downloading
    def get_attr_data(self,table, geometry_field , schema = "public"):
        try:
            
            
            columns = self.get_fields(table , schema='public')

            query = sqlbuilder.SQL("""
                SELECT row_to_json(dt) FROM (
                SELECT *, ST_AsText(ST_Multi(ST_GeomFromText(ST_AsText({geometry_field})))) as geometry
                FROM {schema}.{table} ) AS dt
                """).format(
                schema = sqlbuilder.Identifier(schema),
                table = sqlbuilder.Identifier(table),
                geometry_field = sqlbuilder.Identifier(geometry_field)
                )

            self.cursor.execute(query)

            data = self.cursor.fetchall()
            

            return [r[0] for r in data],columns
        except Exception as e:
            print(e)
            return {
            "message":"There is some error occured while executing the query",
            "status":"error"
            }

    def get_attr_geojson(self,json_stmt,geometry_field , table,schema = "public"):
        try:
            self.cursor.execute(f"""SELECT row_to_json(fc)
                FROM (SELECT 'FeatureCollection' AS type, array_to_json(array_agg(f)) AS features
                FROM (SELECT 'Feature' AS type,
                ST_AsGeoJSON(l.{geometry_field})::json AS geometry,
                (SELECT json_build_object({json_stmt})) AS properties
                FROM {schema}.{table} AS l) AS f) AS fc;""")

            row = self.cursor.fetchone()
            return row
        except Exception as e:
            print(e)
            return {
            "message":"There is some error occured while executing the query",
            "status":"error"
            }


    def get_fields(self, table, schema='public'):
        self.cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s 
        """, [schema, table])
        
        return [r[0] for r in self.cursor.fetchall()]


    def get_geometry_field(self,table,schema="public"):
        self.cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND udt_name = %s
            """, [schema, table, "geometry"])

        return [r[0] for r in self.cursor.fetchall()]

    def get_attribute_fields(self,table,schema="public"):
        self.cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND udt_name != %s
            """, [schema, table, "geometry"])

        return [r[0] for r in self.cursor.fetchall()]


    def get_table_names(self,schema = "public"):
        self.cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = %s and table_type = %s;
            """,[schema,'BASE TABLE'])

        return [r[0] for r in self.cursor.fetchall()]

    def get_unique_values(self,column_name,table,schema = "public"):
        query = sqlbuilder.SQL("""
            SELECT DISTINCT {column} FROM {schema}.{table}
            WHERE {column} IS NOT NULL;
            """).format(
            column = sqlbuilder.Identifier(column_name),
            table = sqlbuilder.Identifier(table),
            schema = sqlbuilder.Identifier(schema)
            )

        self.cursor.execute(query)

        return [r[0] for r in self.cursor.fetchall()]

    def get_count(self,table,schema = "public"):
        query = sqlbuilder.SQL("""
            SELECT COUNT(*) FROM {schema}.{table}
            """).format(
            schema = sqlbuilder.Identifier(schema),
            table = sqlbuilder.Identifier(table)
            )

        self.cursor.execute(query)

        data = self.cursor.fetchall()[0][0]

        return data


    def get_geometry_type(self,geo_field,table,schema = "public"):
        """
        This function will take the table name and schema and will return
        the geometry type of the geometry column of that table
        """
        query = sqlbuilder.SQL("""
            SELECT type
            FROM geometry_columns
            WHERE f_table_schema = {schema} AND
            f_table_name = {table} AND
            f_geometry_column = {geo_field};
            """).format(
            schema = sqlbuilder.Literal(schema),
            table = sqlbuilder.Literal(table),
            geo_field = sqlbuilder.Literal(geo_field)
            )

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while getting the geometry type of layer %s"%(table),
            "status":"error"
            }


    def get_attribute_data(self,fields,pk_field,limit,offset,table,schema = "public"):
        query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            row_to_json(data) AS properties FROM
            (SELECT {columns} FROM {schema}.{table}
            ORDER BY {pk_field} ASC
            OFFSET {offset} LIMIT {limit}) AS data
            ) AS geojson
            ) AS ft
            """).format(
            columns = sqlbuilder.SQL(", ").join(map(sqlbuilder.Identifier,fields)),
            table = sqlbuilder.Identifier(table),
            schema = sqlbuilder.Identifier(schema),
            pk_field = sqlbuilder.Identifier(pk_field),
            limit = sqlbuilder.Literal(limit),
            offset = sqlbuilder.Literal(offset)
            )

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while getting the attribute data",
            "status":"error"
            }


    def get_attribute_data_json(self,fields,pk_field,limit,offset,table,schema = "public"):
        query = sqlbuilder.SQL("""
            SELECT row_to_json(data) FROM
            (SELECT {columns} FROM {schema}.{table}
            ORDER BY {pk_field} ASC
            OFFSET {offset} LIMIT {limit}) AS data
            """).format(
            columns = sqlbuilder.SQL(", ").join(map(sqlbuilder.Identifier,fields)),
            table = sqlbuilder.Identifier(table),
            schema = sqlbuilder.Identifier(schema),
            pk_field = sqlbuilder.Identifier(pk_field),
            limit = sqlbuilder.Literal(limit),
            offset = sqlbuilder.Literal(offset)
            )

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while getting the attribute data",
            "status":"error"
            }


    def get_intersect(self,crs,table1,geom1,table2,geom2,schema = "public"):
        query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_AsGeoJson(ST_Transform(ST_Intersection(table1.{geom1},table2.{geom2}),{crs}))::json AS geometry
            FROM {schema}.{table1} AS table1 INNER JOIN
            {schema}.{table2} AS table2 ON 
            ST_Intersects(table1.{geom1},table2.{geom2})) AS geojson
            ) AS ft
            """).format(
            geom1 = sqlbuilder.Identifier(geom1),
            geom2 = sqlbuilder.Identifier(geom2),
            schema = sqlbuilder.Identifier(schema),
            table1 = sqlbuilder.Identifier(table1),
            table2 = sqlbuilder.Identifier(table2),
            crs = sqlbuilder.Literal(crs)
            )

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the function",
            "status":"error"
            }


    def are_within(self,crs,distance,table1,geom1,table2,geom2,schema = "public"):
        if distance is not None:
            query = sqlbuilder.SQL("""
                SELECT row_to_json(ft) FROM
                (
                SELECT 'FeatureCollection' AS type,
                array_to_json(array_agg(geojson)) AS features FROM
                (
                SELECT 'Feature' AS type,
                ST_AsGeoJson(ST_Transform((SELECT DISTINCT layer1.{geom1}),{crs}))::json AS geometry
                FROM {schema}.{table1} AS layer1
                JOIN {schema}.{table2} AS layer2
                ON ST_DWithin(layer1.{geom1},layer2.{geom2},{distance})
                ) AS geojson
                ) AS ft
                """).format(
                geom1 = sqlbuilder.Identifier(geom1),
                geom2 = sqlbuilder.Identifier(geom2),
                schema = sqlbuilder.Identifier(schema),
                table1 = sqlbuilder.Identifier(table1),
                table2 = sqlbuilder.Identifier(table2),
                distance = sqlbuilder.Literal(distance),
                crs = sqlbuilder.Literal(crs)
                )
        else:
            query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_AsGeoJson(ST_Transform((SELECT DISTINCT layer1.{geom1}),{crs}))::json AS geometry
            FROM {schema}.{table1} AS layer1
            JOIN {schema}.{table2} AS layer2
            ON ST_Within(layer1.{geom1},layer2.{geom2})
            ) AS geojson
            ) AS ft
            """).format(
            geom1 = sqlbuilder.Identifier(geom1),
            geom2 = sqlbuilder.Identifier(geom2),
            schema = sqlbuilder.Identifier(schema),
            table1 = sqlbuilder.Identifier(table1),
            table2 = sqlbuilder.Identifier(table2),
            crs = sqlbuilder.Literal(crs)
            )

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            print(e)
            return {
            "message":"There is some exception occured while executing the function",
            "status":"error"
            }


    def contains(self,crs,complete,table1,geom1,table2,geom2,schema = "public"):

        params = {"geom1" : sqlbuilder.Identifier(geom1),
            "geom2" : sqlbuilder.Identifier(geom2),
            "schema" : sqlbuilder.Identifier(schema),
            "table1" : sqlbuilder.Identifier(table1),
            "table2" : sqlbuilder.Identifier(table2),
            "crs" : sqlbuilder.Literal(crs)}

        if complete:
            query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_AsGeoJson(ST_Transform((SELECT DISTINCT layer1.{geom1}),{crs}))::json AS geometry
            FROM {schema}.{table1} AS layer1
            JOIN {schema}.{table2} AS layer2
            ON ST_ContainsProperly(layer1.{geom1},layer2.{geom2})
            ) AS geojson
            ) AS ft
            """).format(**params)
        else:
            query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_AsGeoJson(ST_Transform((SELECT DISTINCT layer1.{geom1}),{crs}))::json AS geometry
            FROM {schema}.{table1} AS layer1
            JOIN {schema}.{table2} AS layer2
            ON ST_Contains(layer1.{geom1},layer2.{geom2})
            ) AS geojson
            ) AS ft
            """).format(**params)

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the function",
            "status":"error"
            }


    def layer_touches(self,crs,table1,geom1,table2,geom2,schema = "public"):
        query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_AsGeoJson(ST_Transform((SELECT DISTINCT layer1.{geom1}),{crs}))::json AS geometry
            FROM {schema}.{table1} AS layer1
            JOIN {schema}.{table2} AS layer2
            ON ST_Touches(layer1.{geom1},layer2.{geom2})
            ) AS geojson
            ) AS ft
            """).format(
            geom1 = sqlbuilder.Identifier(geom1),
            geom2 = sqlbuilder.Identifier(geom2),
            schema = sqlbuilder.Identifier(schema),
            table1 = sqlbuilder.Identifier(table1),
            table2 = sqlbuilder.Identifier(table2),
            crs = sqlbuilder.Literal(crs)
            )

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the function",
            "status":"error"
            }



    def layer_identical(self,crs,table1,geom1,table2,geom2,schema = "public"):
        query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_AsGeoJson(ST_Transform((SELECT DISTINCT layer1.{geom1}),{crs}))::json AS geometry
            FROM {schema}.{table1} AS layer1
            JOIN {schema}.{table2} AS layer2
            ON ST_Equals(layer1.{geom1},layer2.{geom2})
            ) AS geojson
            ) AS ft
            """).format(
            geom1 = sqlbuilder.Identifier(geom1),
            geom2 = sqlbuilder.Identifier(geom2),
            schema = sqlbuilder.Identifier(schema),
            table1 = sqlbuilder.Identifier(table1),
            table2 = sqlbuilder.Identifier(table2),
            crs = sqlbuilder.Literal(crs)
            )

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the function",
            "status":"error"
            }


    def layer_centroid_in(self,crs,table1,geom1,table2,geom2,schema = "public"):
        query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
            FROM {schema}.{table1} AS layer1
            JOIN {schema}.{table2} AS layer2
            ON ST_Centroid(layer1.{geom1}) && layer2.{geom2}
            AND ST_Intersects(ST_Centroid(layer1.{geom1}),layer2.{geom2})
            ) AS geojson
            ) AS ft
            """).format(
            geom1 = sqlbuilder.Identifier(geom1),
            geom2 = sqlbuilder.Identifier(geom2),
            schema = sqlbuilder.Identifier(schema),
            table1 = sqlbuilder.Identifier(table1),
            table2 = sqlbuilder.Identifier(table2),
            crs = sqlbuilder.Literal(crs)
            )

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the function",
            "status":"error"
            }


    def layer_shares_line_segment(self,crs,table1,geom1,geomType1,table2,geom2,geomType2,schema = "public"):
        if geomType1 == geomType2 == GEOMETRY_TYPE_POLYGON:
            query = sqlbuilder.SQL("""
                SELECT row_to_json(ft) FROM
                (
                SELECT 'FeatureCollection' AS type,
                array_to_json(array_agg(geojson)) AS features FROM
                (
                SELECT 'Feature' AS type,
                ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
                FROM {schema}.{table1} AS layer1
                JOIN {schema}.{table2} AS layer2
                ON layer1.{geom1} && layer2.{geom2}
                AND ST_Relate(layer1.{geom1},layer2.{geom2},'****1***2')
                ) AS geojson
                ) AS ft
                """).format(
                geom1 = sqlbuilder.Identifier(geom1),
                geom2 = sqlbuilder.Identifier(geom2),
                schema = sqlbuilder.Identifier(schema),
                table1 = sqlbuilder.Identifier(table1),
                table2 = sqlbuilder.Identifier(table2),
                crs = sqlbuilder.Literal(crs)
                )
        elif geomType1 == geomType2 == GEOMETRY_TYPE_LINESTRING:
            query = sqlbuilder.SQL("""
                SELECT row_to_json(ft) FROM
                (
                SELECT 'FeatureCollection' AS type,
                array_to_json(array_agg(geojson)) AS features FROM
                (
                SELECT 'Feature' AS type,
                ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
                FROM {schema}.{table1} AS layer1
                JOIN {schema}.{table2} AS layer2
                ON layer1.{geom1} && layer2.{geom2}
                AND ST_Relate(layer1.{geom1},layer2.{geom2},'1**F****2')
                ) AS geojson
                ) AS ft
                """).format(
                geom1 = sqlbuilder.Identifier(geom1),
                geom2 = sqlbuilder.Identifier(geom2),
                schema = sqlbuilder.Identifier(schema),
                table1 = sqlbuilder.Identifier(table1),
                table2 = sqlbuilder.Identifier(table2),
                crs = sqlbuilder.Literal(crs)
                )
        else:
            if geomType2 == GEOMETRY_TYPE_POLYGON:
                query = sqlbuilder.SQL("""
                    SELECT row_to_json(ft) FROM
                    (
                    SELECT 'FeatureCollection' AS type,
                    array_to_json(array_agg(geojson)) AS features FROM
                    (
                    SELECT 'Feature' AS type,
                    ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
                    FROM {schema}.{table1} AS layer1
                    JOIN {schema}.{table2} AS layer2
                    ON layer1.{geom1} && layer2.{geom2}
                    AND ST_Relate(layer2.{geom2},layer1.{geom1},'**2101**2')
                    ) AS geojson
                    ) AS ft
                    """).format(
                    geom1 = sqlbuilder.Identifier(geom1),
                    geom2 = sqlbuilder.Identifier(geom2),
                    schema = sqlbuilder.Identifier(schema),
                    table1 = sqlbuilder.Identifier(table1),
                    table2 = sqlbuilder.Identifier(table2),
                    crs = sqlbuilder.Literal(crs)
                    )
            else:
                query = sqlbuilder.SQL("""
                    SELECT row_to_json(ft) FROM
                    (
                    SELECT 'FeatureCollection' AS type,
                    array_to_json(array_agg(geojson)) AS features FROM
                    (
                    SELECT 'Feature' AS type,
                    ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
                    FROM {schema}.{table1} AS layer1
                    JOIN {schema}.{table2} AS layer2
                    ON layer1.{geom1} && layer2.{geom2}
                    AND ST_Relate(layer1.{geom1},layer2.{geom2},'**2101**2')
                    ) AS geojson
                    ) AS ft
                    """).format(
                    geom1 = sqlbuilder.Identifier(geom1),
                    geom2 = sqlbuilder.Identifier(geom2),
                    schema = sqlbuilder.Identifier(schema),
                    table1 = sqlbuilder.Identifier(table1),
                    table2 = sqlbuilder.Identifier(table2),
                    crs = sqlbuilder.Literal(crs)
                    )
        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the function",
            "status":"error"
            }


    # def layers_are_crossed_by_the_line_of(self,crs,table1,geom1,geomType1,table2,geom2,geomType2,schema = "public"):
    #     if geomType1 == geomType2 == GEOMETRY_TYPE_POLYGON:
    #         query = sqlbuilder.SQL("""
    #             SELECT row_to_json(ft) FROM
    #             (
    #             SELECT 'FeatureCollection' AS type,
    #             array_to_json(array_agg(geojson)) AS features FROM
    #             (
    #             SELECT 'Feature' AS type,
    #             ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
    #             FROM {schema}.{table1} AS layer1
    #             JOIN {schema}.{table2} AS layer2
    #             ON layer1.{geom1} && layer2.{geom2}
    #             AND ST_Relate(layer1.{geom1},layer2.{geom2},'**2*01**2')
    #             ) AS geojson
    #             ) AS ft
    #             """).format(
    #             geom1 = sqlbuilder.Identifier(geom1),
    #             geom2 = sqlbuilder.Identifier(geom2),
    #             schema = sqlbuilder.Identifier(schema),
    #             table1 = sqlbuilder.Identifier(table1),
    #             table2 = sqlbuilder.Identifier(table2),
    #             crs = sqlbuilder.Literal(crs)
    #             )
    #     elif geomType1 == geomType2 == GEOMETRY_TYPE_LINESTRING:
    #         query = sqlbuilder.SQL("""
    #             SELECT row_to_json(ft) FROM
    #             (
    #             SELECT 'FeatureCollection' AS type,
    #             array_to_json(array_agg(geojson)) AS features FROM
    #             (
    #             SELECT 'Feature' AS type,
    #             ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
    #             FROM {schema}.{table1} AS layer1
    #             JOIN {schema}.{table2} AS layer2
    #             ON layer1.{geom1} && layer2.{geom2}
    #             AND ( ST_Relate(layer1.{geom1},layer2.{geom2},'0*1***1*2')
    #                 OR ST_Relate(layer1.{geom1},layer2.{geom2},'*01***1*2')
    #                 OR ST_Relate(layer1.{geom1},layer2.{geom2},'**10**1*2')
    #                 OR ST_Relate(layer1.{geom1},layer2.{geom2},'**1*0*1*2'))
    #             ) AS geojson
    #             ) AS ft
    #             """).format(
    #             geom1 = sqlbuilder.Identifier(geom1),
    #             geom2 = sqlbuilder.Identifier(geom2),
    #             schema = sqlbuilder.Identifier(schema),
    #             table1 = sqlbuilder.Identifier(table1),
    #             table2 = sqlbuilder.Identifier(table2),
    #             crs = sqlbuilder.Literal(crs)
    #             )
    #     else:
    #         if geomType2 == GEOMETRY_TYPE_POLYGON:
    #             query = sqlbuilder.SQL("""
    #                 SELECT row_to_json(ft) FROM
    #                 (
    #                 SELECT 'FeatureCollection' AS type,
    #                 array_to_json(array_agg(geojson)) AS features FROM
    #                 (
    #                 SELECT 'Feature' AS type,
    #                 ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
    #                 FROM {schema}.{table1} AS layer1
    #                 JOIN {schema}.{table2} AS layer2
    #                 ON layer1.{geom1} && layer2.{geom2}
    #                 AND ( ST_Relate(layer2.{geom2},layer1.{geom1},'***0*1**2')
    #                     OR ST_Relate(layer2.{geom2},layer1.{geom1},'****01**2'))
    #                 ) AS geojson
    #                 ) AS ft
    #                 """).format(
    #                 geom1 = sqlbuilder.Identifier(geom1),
    #                 geom2 = sqlbuilder.Identifier(geom2),
    #                 schema = sqlbuilder.Identifier(schema),
    #                 table1 = sqlbuilder.Identifier(table1),
    #                 table2 = sqlbuilder.Identifier(table2),
    #                 crs = sqlbuilder.Literal(crs)
    #                 )
    #         else:
    #             query = sqlbuilder.SQL("""
    #                 SELECT row_to_json(ft) FROM
    #                 (
    #                 SELECT 'FeatureCollection' AS type,
    #                 array_to_json(array_agg(geojson)) AS features FROM
    #                 (
    #                 SELECT 'Feature' AS type,
    #                 ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
    #                 FROM {schema}.{table1} AS layer1
    #                 JOIN {schema}.{table2} AS layer2
    #                 ON layer1.{geom1} && layer2.{geom2}
    #                 AND ( ST_Relate(layer1.{geom1},layer2.{geom2},'***0*1**2')
    #                     OR ST_Relate(layer1.{geom1},layer2.{geom2},'****01**2'))
    #                 ) AS geojson
    #                 ) AS ft
    #                 """).format(
    #                 geom1 = sqlbuilder.Identifier(geom1),
    #                 geom2 = sqlbuilder.Identifier(geom2),
    #                 schema = sqlbuilder.Identifier(schema),
    #                 table1 = sqlbuilder.Identifier(table1),
    #                 table2 = sqlbuilder.Identifier(table2),
    #                 crs = sqlbuilder.Literal(crs)
    #                 )
    #     try:
    #         self.cursor.execute(query)
    #         data = self.cursor.fetchall()

    #         return [r[0] for r in data]
    #     except Exception as e:
    #         print(e)
    #         return {
    #         "message":"There is some exception occured while executing the function",
    #         "status":"error"
    #         }


    def layers_are_crossed_by_the_line_of(self,crs,table1,geom1,table2,geom2,schema = "public"):
        query = sqlbuilder.SQL("""
                SELECT row_to_json(ft) FROM
                (
                SELECT 'FeatureCollection' AS type,
                array_to_json(array_agg(geojson)) AS features FROM
                (
                SELECT 'Feature' AS type,
                ST_AsGeoJson(ST_Transform((SELECT layer1.{geom1}),{crs}))::json AS geometry
                FROM {schema}.{table1} AS layer1
                JOIN {schema}.{table2} AS layer2
                ON ST_Crosses(layer1.{geom1},layer2.{geom2})
                ) AS geojson
                ) AS ft
                """).format(
                geom1 = sqlbuilder.Identifier(geom1),
                geom2 = sqlbuilder.Identifier(geom2),
                schema = sqlbuilder.Identifier(schema),
                table1 = sqlbuilder.Identifier(table1),
                table2 = sqlbuilder.Identifier(table2),
                crs = sqlbuilder.Literal(crs)
                )
        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            print(e)
            return {
            "message":"There is some exception occured while executing the function",
            "status":"error"
            }



    def get_buffer(self,crs,size,pk_field,geo_field,table,schema = "public",features=None):

        if features is not None:
            query = sqlbuilder.SQL("""
                SELECT row_to_json(ft) FROM
                (
                SELECT 'FeatureCollection' AS type,
                array_to_json(array_agg(geojson)) AS features FROM
                (
                SELECT 'Feature' AS type,
                ST_AsGeoJson(
                    CASE WHEN {size_bool}::bool THEN
                    ST_Transform(ST_Buffer(
                    (SELECT {geo_field}),{buffer_size}
                    ),{crs})
                    ELSE ST_Transform((SELECT {geo_field}),{crs})
                    END
                    )::json AS geometry
                FROM {schema}.{table} WHERE {pk_field} IN ({features})
                ) AS geojson
                ) AS ft
                """).format(
                schema = sqlbuilder.Identifier(schema),
                table = sqlbuilder.Identifier(table),
                pk_field = sqlbuilder.Identifier(pk_field),
                features = sqlbuilder.SQL(", ").join(map(sqlbuilder.Literal,features)),
                buffer_size = sqlbuilder.Literal(size),
                geo_field = sqlbuilder.Identifier(geo_field),
                crs = sqlbuilder.Literal(crs),
                size_bool = sqlbuilder.Literal(bool(size))
                )
        else:
            query = sqlbuilder.SQL("""
                SELECT row_to_json(ft) FROM
                (
                SELECT 'FeatureCollection' AS type,
                array_to_json(array_agg(geojson)) AS features FROM
                (
                SELECT 'Feature' AS type,
                ST_AsGeoJson(
                    CASE WHEN {size_bool}::bool THEN
                    ST_Transform(ST_Buffer(
                    (SELECT {geo_field}),{buffer_size}
                    ),{crs})
                    ELSE ST_Transform((SELECT {geo_field}),{crs})
                    END
                    )::json AS geometry
                FROM {schema}.{table}
                ) AS geojson
                ) AS ft
                """).format(
                schema = sqlbuilder.Identifier(schema),
                table = sqlbuilder.Identifier(table),
                buffer_size = sqlbuilder.Literal(size),
                geo_field = sqlbuilder.Identifier(geo_field),
                crs = sqlbuilder.Literal(crs),
                size_bool = sqlbuilder.Literal(bool(size))
                )

        try:
            # print(query.as_string(self.cursor))
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the Buffer function",
            "status":"error"
            }


    def get_clip(self,geometry_field,srs,clip_geom,native_srs,table,schema="public"):

        query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_Transform((SELECT ST_Intersection({geo_field},ST_GeomFromText({clip_geom},{native_srs}))),{srs}) AS geometry
            FROM {schema}.{table}
            WHERE {geo_field} && ST_GeomFromText({clip_geom},{native_srs})
            AND ST_Intersects({geo_field},ST_GeomFromText({clip_geom},{native_srs}))    
            ) AS geojson
            ) AS ft
            """).format(
            schema = sqlbuilder.Identifier(schema),
            table = sqlbuilder.Identifier(table),
            geo_field = sqlbuilder.Identifier(geometry_field),
            clip_geom = sqlbuilder.Literal(clip_geom),
            srs = sqlbuilder.Literal(srs),
            native_srs = sqlbuilder.Literal(native_srs)
            )

        try:
            # print(query.as_string(self.cursor))
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the Clip function",
            "status":"error"
            }


    def get_erase(self,geometry_field,srs,erase_geom,native_srs,table,schema="public"):

        query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_Transform((SELECT {geo_field}),{srs}) AS geometry
            FROM {schema}.{table}
            WHERE NOT (
                {geo_field} && ST_GeomFromText({erase_geom},{native_srs})
                AND ST_Intersects({geo_field},ST_GeomFromText({erase_geom},{native_srs}))
                )
            ) AS geojson
            ) AS ft;
            """).format(
            schema = sqlbuilder.Identifier(schema),
            table = sqlbuilder.Identifier(table),
            geo_field = sqlbuilder.Identifier(geometry_field),
            erase_geom = sqlbuilder.Literal(erase_geom),
            srs = sqlbuilder.Literal(srs),
            native_srs = sqlbuilder.Literal(native_srs)
            )

        try:
            # print(query.as_string(self.cursor))
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the Erase function",
            "status":"error"
            }


    def get_split(self,geo_field,srs,split_geom,native_srs,table,schema = "public"):

        query = sqlbuilder.SQL("""
            SELECT row_to_json(ft) FROM
            (
            SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(geojson)) AS features FROM
            (
            SELECT 'Feature' AS type,
            ST_Transform((SELECT ST_Split({geo_field},ST_GeomFromText({split_geom},{native_srs}))),{srs})
            FROM {schema}.{table}
            ) AS data ;
            """).format(
            schema = sqlbuilder.Identifier(schema),
            table = sqlbuilder.Identifier(table),
            geo_field = sqlbuilder.Identifier(geo_field),
            split_geom = sqlbuilder.Literal(split_geom),
            srs = sqlbuilder.Literal(srs),
            native_srs = sqlbuilder.Literal(native_srs)
            )

        try:
            # print(query.as_string(self.cursor))
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the Split function",
            "status":"error"
            }


    def set_field_default(self, schema, table, field, default_value=None):
        """
        Sets a column default value. Use None to drop the default value of a column.
        Warning: 'default_value' parameter is not protected against SQL injection.
        Always validate user input to feed this parameter.
        """
        if default_value is None:
            sql = "ALTER TABLE {schema}.{table} ALTER COLUMN {field} DROP DEFAULT"
        else:
            sql = "ALTER TABLE {schema}.{table} ALTER COLUMN {field} SET DEFAULT " + default_value
        query = sqlbuilder.SQL(sql).format(
            schema=sqlbuilder.Identifier(schema),
            table=sqlbuilder.Identifier(table),
            field=sqlbuilder.Identifier(field))
        self.cursor.execute(query)

    def validate_data_type(self, data_type_def):
        """
        Returns a PostgreSQL data type if the provided data_type_def is valid,
        or None otherwise.
        """
        if data_type_def == 'character_varying' or data_type_def == 'character varying':
            return 'character varying'
        elif data_type_def == 'integer':
            return 'integer'
        elif data_type_def == 'double' or data_type_def == 'double precision':
            return 'double precision'
        elif data_type_def == 'boolean':
            return 'boolean'
        elif data_type_def == 'date':
            return 'date'
        elif data_type_def == 'time':
            return 'time'
        elif data_type_def == 'timestamp':
            return 'timestamp'
        elif data_type_def == 'timestamp_with_time_zone' or data_type_def == 'timestamp with time zone':
            return 'timestamp with time zone'
        elif data_type_def == 'cd_json':
            return 'character varying'
        elif data_type_def == 'enumeration' or \
                data_type_def == 'multiple_enumeration' or \
                data_type_def == 'form':
            return 'character varying'

    def add_column(self, schema, table_name, column_name, sql_type, nullable=True, default=None):
        """
        Warning: 'default' parameter is not protected against SQL injection. Always validate
        user input to feed this parameter.
        """
        data_type = self.validate_data_type(sql_type)
        if not data_type:
            raise Exception('Invalid data type')
        if not nullable:
            nullable_query = sqlbuilder.SQL("NOT NULL")
        else:
            nullable_query = sqlbuilder.SQL("")
        if default:
            default_query = sqlbuilder.SQL("DEFAULT " + default)
        else:
            default_query = sqlbuilder.SQL("")
        query = sqlbuilder.SQL("ALTER TABLE {schema}.{table} ADD COLUMN {column_name} {sql_type} {nullable} {default}").format(
            schema=sqlbuilder.Identifier(schema),
            table=sqlbuilder.Identifier(table_name),
            column_name=sqlbuilder.Identifier(column_name),
            sql_type=sqlbuilder.SQL(data_type),
            nullable=nullable_query,
            default=default_query)
        self.cursor.execute(query,  [])

    def _parse_sql_identifier(self, s, expected_next_char, pattern=plainIdentifierPattern):
        """
        Parses the provided string an returns a tuple with the parsed identifier and the rest of the string.
        Returns a tuple of empty strings if the provided string could not be properly parsed
        """
        if len(s) > 0 and s[0] != '"':
            # unquoted, normal identifier
            
            pos = s.find(expected_next_char)
            if pos > 0:
                identifier = s[:pos]
                if pattern.match(identifier):
                    return (identifier, s[pos+1:])
        else:
            s = s[1:]
            prev_escape_char = ''
            seq_name_list = []
            for idx, c in enumerate(s):
                if c == '"':
                    if prev_escape_char == '"':
                        seq_name_list.append('"')
                        prev_escape_char = ''
                    else:
                        prev_escape_char = '"'
                elif prev_escape_char != '"':
                    seq_name_list.append(c)
                else:
                    seq_name = ''.join(seq_name_list)
                    str_end = s[idx:]
                    break
            if len(str_end) > 0 and str_end[0] == expected_next_char:
                return (seq_name, str_end[1:])
        return ('', '')
    
    def _parse_sequence_name(self, definition):
        schema, seq_name, _ = self._parse_qualified_identifier(definition, "'", "nextval('")
        return (schema, seq_name)
    
    def _parse_function_def(self, definition):
        return self._parse_qualified_identifier(definition, "(", 'CREATE OR REPLACE FUNCTION ')
    
    def _parse_function_call(self, definition):
        (schema, func_name, end_str) = self._parse_qualified_identifier(definition, '(', 'EXECUTE PROCEDURE ')
        params = end_str[:-1]
        return (schema, func_name, params)

    def _parse_qualified_identifier(self, definition, end_char, skip_string):
        s = definition[len(skip_string):]
        
        # faster check for plain unquoted identifiers (common case)
        (schema_seq_name, str_end) =  self._parse_sql_identifier(s, end_char, plainSchemaIdentifierPattern)
        if len(schema_seq_name) > 0:
            parts = schema_seq_name.split(".")
            if len(parts) > 1:
                return (parts[0], parts[1], str_end)
            else:
                return ('', parts[0], str_end)

        # deep check for quoted identifiers
        (schema, str_end) =  self._parse_sql_identifier(s, '.')
        if schema != '':
            (seq_name, str_end) =  self._parse_sql_identifier(str_end, end_char)
        else:
            (seq_name, str_end) =  self._parse_sql_identifier(s, end_char)
        return (schema, seq_name, str_end)

    def get_sequences(self, table, schema='public'):
        """
        Returns a list of tuples, each tuple containing:
        (col_name, full_sequence_name, schema, sequence_name)
        """
        query = """SELECT column_name, column_default FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        AND column_default LIKE %s
        """
        self.cursor.execute(query, [schema, table, 'nextval%'])

        result = []
        for (col, col_default) in self.cursor.fetchall():
            try:
                seq_schema, seq_name = self._parse_sequence_name(col_default)
                if seq_name != '':
                    if seq_schema == '': # for non qualified sequences
                        seq_schema = schema
                    result.append((col, seq_schema, seq_name))
            except:
              pass

        return result

    def get_pk_sequences(self, table, schema='public'):
        seqs = self.get_sequences(table, schema)
        pks = self.get_pk_columns(table, schema)
        result = []
        for (col, schema, seq_name) in seqs:
            if col in pks:
              result.append((col, schema, seq_name))
        return result

    def update_pk_sequences(self, table, schema='public'):
        """
        Ensures the sequence start value is higher than any existing value for the column.
        We combine max(id) and last_value because we want to modify the sequence ONLY if
        'last_value' is smaller than the maximum id value.
        """
        seqs = self.get_pk_sequences(table, schema)
        sql = """SELECT setval({seq}, s3.next_val) FROM
                    (SELECT GREATEST(max_id, last_value) next_val from
                    (SELECT last_value from {seq_schema}.{seq_name}) s1,
                    (SELECT MAX({col}) max_id from {schema}.{table}) s2) s3"""
        for (col, seq_schema, seq_name) in seqs:
            full_sequence = quote_ident(seq_schema, self.conn) + "." + quote_ident(seq_name, self.conn)
            query = sqlbuilder.SQL(sql).format(
                seq=sqlbuilder.Literal(full_sequence),
                seq_schema=sqlbuilder.Identifier(seq_schema),
                seq_name=sqlbuilder.Identifier(seq_name),
                col=sqlbuilder.Identifier(col),
                schema=sqlbuilder.Identifier(schema),
                table=sqlbuilder.Identifier(table))
            self.cursor.execute(query)

    def delete_table(self, schema, table_name):
        query = sqlbuilder.SQL("DROP TABLE IF EXISTS {schema}.{table}").format(
            schema=sqlbuilder.Identifier(schema),
            table=sqlbuilder.Identifier(table_name))
        self.cursor.execute(query,  [])


    def check_exist(self,schema,table_name,kwargs):

        query = sqlbuilder.SQL("""
            SELECT CASE WHEN EXISTS ( SELECT * FROM {schema}.{table} 
                WHERE {conditions} LIMIT 1)
            THEN 1::bool
            ELSE 0::bool
            END
            """).format(
            schema  = sqlbuilder.Identifier(schema),
            table = sqlbuilder.Identifier(table_name),
            conditions = sqlbuilder.SQL(" AND ").join(
                map(sqlbuilder.Composed,tuple(
                    (sqlbuilder.Identifier(key),sqlbuilder.SQL(" = "),sqlbuilder.Literal(val))
                    for key,val in kwargs.items()
                    ))
                ),
            )

        self.cursor.execute(query)

        row = self.cursor.fetchone()

        return row[0]



    def query_db(self,crs,query,attributes,geometry_field):
        """
        This function will query the database based on the query given
        and it will return geojson of fetched data
        """
        query = sqlbuilder.SQL("""
            SELECT row_to_json(data) FROM
            (SELECT 'FeatureCollection' AS type,
            array_to_json(array_agg(f)) AS features FROM
            (SELECT 'Feature' AS type,
            ST_AsGeoJSON(
                ST_Transform((SELECT {geometry_field}),{crs})
                )::json AS geometry,
            (SELECT row_to_json(property) FROM
            (SELECT {attributes}) AS property) AS properties
            FROM ("""+ query +""") AS query ) AS f
            ) As data
            """).format(
            geometry_field = sqlbuilder.Identifier(geometry_field),
            attributes = sqlbuilder.SQL(", ").join(map(sqlbuilder.Identifier,attributes)),
            crs = sqlbuilder.Literal(crs)
            )

        try:
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return [r[0] for r in data]
        except Exception as e:
            return {
            "message":"There is some exception occured while executing the Non-Spatial query",
            "status":"error"
            }

    def insert_data(self,data,srs,geo_field,table,schema = "public"):

        """
        This function will take geojson and insert the data according
        to the geojson in the database
        """

        try:

            geo_value = data.pop(geo_field,None)

            query = sqlbuilder.SQL("""
                INSERT INTO {schema}.{table}
                ({fields},{geo_field})
                VALUES ({values},ST_GeomFromText({geo_value},{srs}))
                """).format(
                schema  = sqlbuilder.Identifier(schema),
                table = sqlbuilder.Identifier(table),
                fields = sqlbuilder.SQL(", ").join(map(sqlbuilder.Identifier,data.keys())),
                values = sqlbuilder.SQL(", ").join(map(sqlbuilder.Literal,data.values())),
                geo_field = sqlbuilder.Identifier(geo_field),
                geo_value = sqlbuilder.Literal(geo_value),
                srs = sqlbuilder.Literal(srs[5:]),
                )

            # print(query.as_string(self.cursor))

            self.cursor.execute(query)

            count = self.cursor.rowcount

            if count:
                return True
            else:
                return {
                "message":"Insert failed!!!",
                "status":"error"
                }

        except Exception as err:
            if err.pgcode.startswith("42"):
                return {
                "message":"There is some Syntax Error or Access Rule Violation While performing the query",
                "status":"error"
                }
            elif err.pgcode.startswith("22"):
                return {
                "message":"Either The data is invalid or data is not proper",
                "status":"error"
                }
            else:
                return {
                "message":"Oops an exception has occured : %s"%(err.pgerror),
                "status":"error"
                }


    def update_data(self,data,pk,editType,srs,geo_field,table,schema = "public"):

        """
        This function will take geojson and update the data according
        to the geojson in the database
        """

        try:

            pk_value = data[pk]
            data.pop(pk,None)

            kwargs = {pk:pk_value}

            if not self.check_exist(schema,table_name=table,kwargs=kwargs):
                return {
                "message":"The ogc field %s you are trying to update does not exist"%(pk_value),
                "status":"error"
                }

            if editType == EDIT_TYPE_SPATIAL:
                query = sqlbuilder.SQL("""
                    UPDATE {schema}.{table}
                    SET {fields} = ST_GeomFromText({values},{srs})
                    WHERE {pk} = {pk_value}
                    """).format(
                    schema  = sqlbuilder.Identifier(schema),
                    table = sqlbuilder.Identifier(table),
                    fields = sqlbuilder.SQL(", ").join(map(sqlbuilder.Identifier,data.keys())),
                    values = sqlbuilder.SQL(", ").join(map(sqlbuilder.Literal,data.values())),
                    srs = sqlbuilder.Literal(srs[5:]),
                    pk = sqlbuilder.Identifier(pk),
                    pk_value = sqlbuilder.Literal(pk_value)
                    )
            elif editType == EDIT_TYPE_NON_SPATIAL:
                query = sqlbuilder.SQL("""
                    UPDATE {schema}.{table}
                    SET ({fields}) = ({values})
                    WHERE {pk} = {pk_value}
                    """).format(
                    schema  = sqlbuilder.Identifier(schema),
                    table = sqlbuilder.Identifier(table),
                    fields = sqlbuilder.SQL(", ").join(map(sqlbuilder.Identifier,data.keys())),
                    values = sqlbuilder.SQL(", ").join(map(sqlbuilder.Literal,data.values())),
                    pk = sqlbuilder.Identifier(pk),
                    pk_value = sqlbuilder.Literal(pk_value)
                    )
            else:
                geo_value = data.pop(geo_field,None)
                query = sqlbuilder.SQL("""
                    UPDATE {schema}.{table}
                    SET {geo_field} = ST_GeomFromText({geo_value},{srs}) , 
                    ({fields}) = ({values})
                    WHERE {pk} = {pk_value}
                    """).format(
                    schema  = sqlbuilder.Identifier(schema),
                    table = sqlbuilder.Identifier(table),
                    fields = sqlbuilder.SQL(", ").join(map(sqlbuilder.Identifier,data.keys())),
                    values = sqlbuilder.SQL(", ").join(map(sqlbuilder.Literal,data.values())),
                    geo_field = sqlbuilder.Identifier(geo_field),
                    geo_value = sqlbuilder.Literal(geo_value),
                    srs = sqlbuilder.Literal(srs[5:]),
                    pk = sqlbuilder.Identifier(pk),
                    pk_value = sqlbuilder.Literal(pk_value)
                    )


            # print(query.as_string(self.cursor))

            self.cursor.execute(query)
            # data=self.cursor.fetchone()

            count = self.cursor.rowcount

            if count:
                return True
            else:
                return {
                "message":"Update failed!!!",
                "status":"error"
                }

        except Exception as err:
            if err.pgcode.startswith("42"):
                return {
                "message":"There is some Syntax Error or Access Rule Violation While performing the query",
                "status":"error"
                }
            elif err.pgcode.startswith("22"):
                return {
                "message":"Either The data is invalid or data is not proper",
                "status":"error"
                }
            else:
                return {
                "message":"Oops an exception has occured : %s"%(err.pgerror),
                "status":"error"
                }

    def delete_data(self,data,pk,table,schema = "public"):

        """
        This function will take Primary key and delete the data accordingly in the database
        """

        try:

            pk_value = data.pop(pk,None)

            kwargs = {pk:pk_value}

            if not self.check_exist(schema,table_name=table,kwargs=kwargs):
                return {
                "message":"The ogc field %s you are trying to delete does not exist"%(pk_value),
                "status":"error"
                }

            query = sqlbuilder.SQL("""
                DELETE FROM {schema}.{table}
                WHERE {pk} = {pk_value}
                """).format(
                schema  = sqlbuilder.Identifier(schema),
                table = sqlbuilder.Identifier(table),
                pk = sqlbuilder.Identifier(pk),
                pk_value = sqlbuilder.Literal(pk_value)
                )


            # print(query.as_string(self.cursor))

            self.cursor.execute(query)
            # data=self.cursor.fetchone()

            count = self.cursor.rowcount

            if count:
                return True
            else:
                return {
                "message":"Delete failed!!!",
                "status":"error"
                }

        except Exception as err:
            if err.pgcode.startswith("42"):
                return {
                "message":"There is some Syntax Error or Access Rule Violation While performing the query",
                "status":"error"
                }
            elif err.pgcode.startswith("22"):
                return {
                "message":"Either The data is invalid or data is not proper",
                "status":"error"
                }
            else:
                return {
                "message":"Oops an exception has occured : %s"%(err.pgerror),
                "status":"error"
                }

    def close(self):
        """
        Closes the connection. The Introspect object can't be used afterwards
        """
        self.conn.close()

# #Postgres manipulation
# class DBManagement(PGConnection):

#     """
#     This class will be used for managing the database i.e manipulating the database,
#     querying the db as well as adding some extra table in db
#     """
    
#     