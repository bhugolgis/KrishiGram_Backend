from rest_framework.permissions import BasePermission
from django.contrib.auth.models import Group


def _is_in_group(user,group_name):
	
	"""
	This function will return true if the user given exists in the requird group
	"""

	try:
		return Group.objects.get(name=group_name).user_set.filter(id=user.id).exists()
	except Exception as e:
		return None

def _has_group_permission(user,group_list):

	"""
	This function will return if user has any group permission for the given list
	"""
	return any([_is_in_group(user,group_name) for group_name in group_list])


class Permission(BasePermission):

	group_list=None
	def has_permission(self,request,view):
		has_group_permission = _has_group_permission(request.user,self.group_list)
		if request.user.is_superuser:
			return True
		return request.user and has_group_permission

class IsAdmin(Permission):

	group_list=["Admin"]

class IsView(Permission):

	group_list=["View"]

class IsViewAndNonSpatialEdit(Permission):

	group_list=["View_and_nonspatial_edit"]

class IsViewAndEdit(Permission):

	group_list=["View_and_edit"]