from django.shortcuts import render
from rest_framework import generics
from rest_framework.parsers import MultiPartParser
from django.contrib.auth.models import Group
from rest_framework.response import Response
from .serializers import *
from rest_framework import status
from .utils import generate_token

# Create your views here.
class UserRegister(generics.GenericAPIView):
	parser_classes=(MultiPartParser,)
	# permission_classes=[permissions.IsAdminUser,]
	serializer_class=UserRegisterSerializer

	def post(self,request,*args,**kwargs):
		request.data._mutable = True
		group_name=request.data.pop("group")[0]
		serializer=self.get_serializer(data=request.data)

		if serializer.is_valid():
			try:
				group=Group.objects.get(name=group_name)
			except Group.DoesNotExist as e:
				return Response({
					"message":"Group with name %s does not exist" %(group_name),
					"status":"error"
					})
			user=serializer.save()
			user.groups.add(group)
			data=UserSerializer(user,context=self.get_serializer_context()).data
			return Response({
				"message":"User created successfully",
				"status":"success",
				"data":data,
				})
		else:
			return Response({
				"message":"User not created",
				"status":"error",
				"error":serializer.errors
				})


class UserLogin(generics.GenericAPIView):
	serializer_class=UserLoginSerializer
	# permission_classes=[permissions.AllowAny,]
	parser_classes=[MultiPartParser]

	def post(self,request,*args,**kwargs):

		serializer=self.get_serializer(data=request.data)
		if serializer.is_valid():
			user=serializer.validated_data
			data=UserSerializer(user,context=self.get_serializer_context()).data
			data={**data,**generate_token(user)}

			return Response({
				"message":"Login successful",
				"status":"success",
				"data":data
				})
		return Response({
				"message":"Login unsuccessful",
				"status":"error",
				"data":serializer.errors
				},status=status.HTTP_400_BAD_REQUEST)