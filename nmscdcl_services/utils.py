from KrushiGram.settings import DEFAULT_CRS

def FormSQL(item):
    if isinstance(item,str):
        return "'%s'"%(item)
    else:
        return str(item)

def deep_flatten(lst):
    
    flat = []
    
    while lst:
        val = lst.pop()
        if isinstance(val,list):
            lst.extend(val)
        else:
            flat.append(val)

    return flat


def error_simplifier(error_dict):
    error_key = error = ""
    value = []
    for key,val in error_dict.items():
        error_key = key
        error = val
        break

    if isinstance(error,str):
        if "field" in error:
            return error_key + ", " + error
        return error
    else:
        value = deep_flatten(error)
        if "field" in value:
            return error_key + ", " + value[0]
        return value[0]


# def convert_geojson(json):
#     data = json["geometry"]["coordinates"]
#     if not isinstance(data[0],(float,int)):
#         for i in range(len(data)):
#             data[i] = data[i][0]
#     elif isinstance(data[0],list) and not isinstance(data[0][0],(float,int)):
#         for i in range(len(data)):
#             data[i] = data[i][0]
#     result = str(data).replace("[","(").replace("]",")").replace(" ","")
    
#     for i in range(len(result)):
#         if result[i] == ",":
#             try:
#                 isinstance(int(result[i+1]),int)
#                 result = result[:i] + " " + result[i+1:]
#             except:
#                 pass
#     return {
#         "data_type":json["geometry"]["type"],
#         "geometry":json["geometry"]["type"].upper()+result,
#         "properties":json["properties"]
#     }

def convert_geojson(json):
    if "geometry" in json:
        # try:
        #     crs = int(json.get("crs",DEFAULT_CRS).get("properties",DEFAULT_CRS).get("name",DEFAULT_CRS).split(":")[1])
        # except Exception as e:
        #     crs = int(DEFAULT_CRS.split(":")[1])
        data = json["geometry"]["coordinates"]
        result = ""
        to_be_removed = "(,)"
        if isinstance(data[0],(float,int)):
            result = str(data).replace("[","(").replace("]",")").replace(","," ")
        else:
            result = str(data).replace("[","(").replace("]",")").replace(" ","")
        
            for i in range(len(result)-1):
                if result[i] in to_be_removed:
                    try:
                        isinstance(int(result[i+1]),int)
                        result = result[:i] + " " + result[i+1:]
                    except:
                        pass
                    try:
                        isinstance(int(result[i-1]),int)
                        result = result[:i] + " " + result[i+1:]
                    except:
                        pass
        return {
            "data_type":json["geometry"]["type"],
            # "geojson_crs":crs,
            "geometry":json["geometry"]["type"].upper()+result,
            "properties":json.get("properties",{}),
        }
    else:
        return {
            "properties":json["properties"]
        }

def read_geojson(geojson):
    final_data = []
    if geojson["type"] == "Feature":
        result = convert_geojson(geojson)
        final_data.append(result)
    elif geojson["type"] == "FeatureCollection":
        for item in geojson["features"]:
            result = convert_geojson(item)
            final_data.append(result)
    return final_data