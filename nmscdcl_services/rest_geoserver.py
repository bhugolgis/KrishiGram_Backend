import requests
from lxml import etree as ET
import json



class Geoserver():

	def __init__(self,rest_url,gwc_url,user=None,password=None):
		self.session=requests.Session()
		self.session.verify = False
		self.service_url=rest_url
		self.gwc_url=gwc_url
		self.session.auth=(user,password)


	def get_session(self):
		return self.session

	def get_service_url(self):
		return self.service_url

	def get_gwc_url(self):
		return self.gwc_url

	def reload(self,node_url,user=None,password=None):
		url=node_url + "/rest/reload"
		if user and password:
			auth=(user,password)
		else:
			auth=self.session.auth

		req=self.get_session().post(url,auth=auth)

		if req.status_code==200:
			return True
		raise FailedRequestError(req.status_code,req.content)

	def add_style(self,layer,style_name,user=None,password=None):
		url=self.get_service_url()+"/layers/"+layer+"/styles"

		if user and password:
			auth=(user,password)
		else:
			auth=self.get_session().auth

		headers={"content-type":"application/xml"}
		data_xml=f"<style><name>{style_name}</name></style>"

		req=self.get_session().post(url,data=data_xml,headers=headers,auth=auth)
		if req.status_code==201:
			return True
		raise FailedRequestError(req.status_code,req.content)


	def get_layer_style_configuration(self,layer,user=None,password=None):
		url=self.get_gwc_url()+"/layers/"+layer+".xml"
		if user and password:
			auth=(user,password)
		else:
			auth=self.get_session().auth

		req=self.get_session().get(url,json={},auth=auth)
		if req.status_code==200:
			return req.content
		raise FailedRequestError(req.status_code,req.content)
		# print(req.content,req.status_code,"this is where we get layer style")


	def update_layer_style_configuration(self,layer,style_name,default_style,style_list,user=None,password=None):
		xml=self.get_layer_style_configuration(layer,user,password)
		tree=ET.fromstring(xml)

		url = self.gwc_url + '/layers/'+layer+'.xml'

		if user and password:
			auth=(user,password)
		else:
			auth=self.get_session().auth

		headers = {'content-type': 'text/xml'}

		for parameterFiltersElem in tree.findall("./parameterFilters"):
			for styleParameterFilterElem in parameterFiltersElem.findall("./styleParameterFilter"):
				styleParameterFilterElem.getparent().remove(styleParameterFilterElem)
			styleParameterFilterElem=ET.SubElement(parameterFiltersElem,"styleParameterFilter")
			keyElem=ET.SubElement(styleParameterFilterElem,"key")
			keyElem.text="STYLES"
			defaultElem=ET.SubElement(styleParameterFilterElem,"defaultValue")
			if default_style:
				defaultElem.text=default_style
			elif len(style_list)>0:
				defaultElem.text=style_list[0]

		req=self.get_session().post(url,data=ET.tostring(tree,encoding="utf-8"),headers=headers,auth=auth)

		if req.status_code==200:
			return True
		raise UploadError(req.status_code,req.text)


	def update_style(self,style_name,sld_body,user=None,password=None):
		url=self.service_url + "/styles/" + style_name + ".sld"

		if user and password:
			auth=(user,password)
		else:
			auth=self.session.auth

		headers={"content-type":"application/vnd.ogc.se+xml"}

		req=self.get_session().put(url,data=sld_body,headers=headers,auth=auth)

		if req.status_code==200:
			return True
		raise UploadError(req.status_code,req.text)


	def get_style(self,layer_name,user=None,password=None):
		url=self.service_url + "/layers/" + layer_name + "/styles"

		if user and password:
			auth=(user,password)
		else:
			auth=self.session.auth

		req=self.get_session().get(url,auth=auth)

		if req.status_code==200:
			return json.loads(req.text)
		raise FailedRequestError(req.status_code,req.content)


	def delete_style(self,style_name,purge,recurse,user=None,password=None):
		url=self.service_url + "/styles/" + style_name
		if user and password:
			auth=(user,password)
		else:
			auth=self.session.auth

		params=[]

		headers={"content-type":"application/json"}
		if purge:
			params.append(f"purge={str(purge)}")
		if recurse:
			params.append("recurse=true")

		if params:
			url=f"{url}?{'&'.join(params)}"

		resp=self.get_session().delete(url,headers=headers,auth=auth)
		
		if resp.status_code==200:
			return True
		raise FailedRequestError(resp.status_code,resp.content)


	def delete_layer(self,layer_url,recurse,user=None,password=None):
		url = layer_url

		if user and password:
			auth=(user,password)
		else:
			auth=self.session.auth

		params = []
		headers={"content-type":"application/json"}

		if recurse:
			params.append("recurse=true")

		if url:

			if params:
				url = f"{url}?{'&'.join(params)}"

			resp=self.get_session().delete(url,headers=headers,auth=auth)
		else:
			raise FailedRequestError(404,"Tile Server url is not passsed or incorrect")
		
		if resp.status_code==200:
			return True
		raise FailedRequestError(resp.status_code,resp.content)


	def create_feature_type(self,workspace,datastore,layer_name,title,srs=None,user=None,password=None):
		url = f"{self.service_url}/workspaces/{workspace}/datastores/{datastore}/featuretypes"
		qualified_store = workspace + ":" + datastore

		ft = {
		"name":layer_name,
		"title":title,
		"enabled":True,
		"store":{"@class":"dataStore","name":qualified_store}
		}

		if srs is not None:
			ft["nativeBoundingBox"] = {"minx": 0, "maxx": 1, "miny": 0, "maxy":1 , "crs":srs}
			ft["srs"] = srs

		data = {"featureType":ft}

		data = json.dumps(data)

		if user and password:
			auth=(user,password)
		else:
			auth=self.session.auth

		headers={"content-type":"application/json"}

		req=self.get_session().post(url,data=data,headers=headers,auth=auth)

		if req.status_code==201:
			return True
		raise FailedRequestError(req.status_code,req.content)



	def delete_feature_type(self,workspace,datastore,layer_name,recurse,user=None,password=None):
		url = f"{self.service_url}/workspaces/{workspace}/datastores/{datastore}/featuretypes/{layer_name}"
		try:
			self.delete_layer(url,recurse,user,password)
			return True
		except Exception as e:
			raise e


	def create_coverage(self,workspace,datastore,layer_name,title,srs=None,user=None,password=None):
		url = f"{self.service_url}/workspaces/{workspace}/coveragestores/{datastore}/coverages"

		ct = {
		"name":layer_name,
		"title":title,
		"enabled":True,
		}

		data = {"coverage":ct}

		data = json.dumps(data)

		if user and password:
			auth=(user,password)
		else:
			auth=self.session.auth

		headers={"content-type":"application/json"}

		req=self.get_session().post(url,data=data,headers=headers,auth=auth)

		if req.status_code==201:
			return True
		raise FailedRequestError(req.status_code,req.content)


	def delete_coverage(self,workspace,datastore,layer_name,recurse,user=None,password=None):
		url = f"{self.service_url}/workspaces/{workspace}/coveragestores/{datastore}/coverages/{layer_name}"
		try:
			self.delete_layer(url,recurse,user,password)
			return True
		except Exception as e:
			raise e


class RequestError(Exception):

	def __init__(self,status=-1,server_message=""):
		self.status=status
		self.server_message=server_message
		self.message=None

	def __str__(self):
		if self.message:
			return self.message
		else:
			return self.server_message

	def set_message(self,val):
		self.message=val

	def get_message(self):
		return self.__str__()

	def get_detailed_message(self):
		from builtins import str as text
		msg="Status: "+text(self.status)
		if isinstance(self.server_message,str):
			msg += "\nServer Message: "+self.server_message
		else:
			msg += "\nServer Message: "+self.server_message.decode("utf-8","replace")

		if isinstance(self.message,str):
			msg += "\nMessage: "+self.message
		else:
			msg += "\nMessage: "+self.message.decode("utf-8","replace")

		return msg

class UploadError(RequestError):
	# print("there is some issue in uploading in rest_geoserver")
	pass

class FailedRequestError(RequestError):
	# print("there is some issue in request in rest_geoserver")
	pass
