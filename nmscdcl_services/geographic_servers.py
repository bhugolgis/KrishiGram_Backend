from . import backend_geoserver
from .models import Server


class GeographicServer():

	def __init__(self):
		self.servers = []
		for s in Server.objects.all():
			gs=backend_geoserver.Geoserver(s.id,s.default,s.name,s.user,s.password,s.frontend_url)
			self.servers.append(gs)

	def get_servers(self):
		return self.servers

	def get_server_by_name(self,name):
		for s in self.servers:
			if s.name==name:
				return s

	def get_server_by_id(self,id):
		for s in self.servers:
			if s.id==id:
				return s

	def get_default_server(self):
		for s in self.servers:
			if s.default:
				return s

	def get_server_model(self,id):
		try:
			s=Server.objects.get(id=int(id))
		except Server.DoesNotExist as e:
			print(e) #need to fixed
		return s


__geographic_servers=None

def get_instance():
	global __geographic_servers
	if __geographic_servers is None:
		__geographic_servers=GeographicServer()
	return __geographic_servers

def reset_instance():
	global __geographic_servers
	__geographic_servers=GeographicServer()
	return __geographic_servers