# from django.utils.deprecation import MiddlewareMixin
# from .models import LayerApiHits


# class ApiHitsMiddleware(MiddlewareMixin):

# 	def __init__(self,get_response):
# 		self.get_response=get_response


# 	def __call__(self,request):
# 		response=self.get_response(request)

# 		id=request.path_info.split("/")[-2].strip()

# 		url_path=["/nmscdcl/services/GetLayerList/",
# 				"/nmscdcl/services/GetDetailedLayerList/",
# 				"/nmscdcl/services/PostLayerApi/",
# 				"/nmscdcl/services/UpdateLayerApi/{}/".format(id),
# 				"/nmscdcl/services/GetLayer/{}/".format(id),
# 				"/nmscdcl/services/DeleteLayer/{}/".format(id)]

# 		if request.user.is_authenticated and request.path_info in url_path:
# 			layer_hit

# 		return response