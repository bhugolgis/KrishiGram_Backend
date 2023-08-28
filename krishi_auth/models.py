from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin
from datetime import date
# Create your models here.
class UserManager(BaseUserManager):

	def _create_user(self,username,password,is_active,is_staff,is_superuser,**extra_fields):
		if not username:
			raise ValueError("username cannot be empty!")
		if not password:
			raise ValueError("password cannot be empty!")
		user=self.model(username=username,is_active=is_active,is_staff=is_staff,
			is_superuser=is_superuser,date_joined=date.today(),**extra_fields)
		user.set_password(password)
		user.save()

		return user

	def create_user(self,username,password,is_active=True,is_staff=False,is_superuser=False,**extra_fields):
		return self._create_user(username=username,password=password,is_active=is_active,is_staff=is_staff,
			is_superuser=is_superuser,**extra_fields)

	def create_superuser(self,username,password,is_active=True,is_staff=True,is_superuser=True,**extra_fields):
		return self._create_user(username=username,password=password,is_active=is_active,is_staff=is_staff,
			is_superuser=is_superuser,**extra_fields)


class User(AbstractBaseUser,PermissionsMixin):
	name=models.CharField(max_length=50,blank=True)
	email=models.EmailField(blank=True)
	username=models.CharField(max_length=20,unique=True,db_index=True)
	is_active=models.BooleanField(default=True)
	is_staff=models.BooleanField(default=False)
	is_superuser=models.BooleanField(default=False)
	is_delete=models.BooleanField(default=False)
	date_joined=models.DateField(auto_now_add=True)
	date_updated=models.DateField(auto_now=True)


	USERNAME_FIELD="username"

	objects=UserManager()

	def __str__(self):
		return self.username

	def has_perm(self,perm_list,obj=None):
		return True

	def has_module_perm(self,app_label):
		return True