import django.dispatch as signal_dispatcher
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Datastore,Layer
from nmscdcl_filemanager.models import ExportHistory
from krishi_auth.models import User
from KrushiGram.settings import MODE_CREATE,DEBUG
from pathlib import Path
import json

@receiver(post_save,sender = Datastore)
def export_to_history(sender,instance,created,**kwargs):
	if created:
		exprted_history = ExportHistory.objects.filter(datastore = instance,
			layerName = instance.name)
		user = User.objects.get(username = instance.created_by)
		if not exprted_history and instance.type.startswith("c"):
			file_path = json.loads(instance.connection_params).get("url")
			fileName = Path(file_path).name.split(".")[0]
			created_by = kwargs.get("created_by",user)
			eh = ExportHistory.objects.create(
				fileName = fileName,
				creationMode = MODE_CREATE,
				name = instance.name,
				layerName = fileName,
				datastore = instance,
				created_by = created_by
				)
			if DEBUG == True:
				print("geotiff history is exported")

@receiver(post_save,sender = Layer)
def update_published_status(sender,instance,created,**kwargs):
	if created:
		try:
			exported_history = ExportHistory.objects.get(datastore = instance.datastore,
				layerName = instance.source_name)
			exported_history.is_published = True
			exported_history.save()
			if DEBUG == True:
				print("%s published successfully"%(instance.name))
		except ExportHistory.DoesNotExist as e:
			user = User.objects.get(username = instance.datastore.created_by)
			ExportHistory.objects.create(
				fileName = instance.source_name,
				creationMode = MODE_CREATE,
				name = instance.source_name,
				layerName = instance.source_name,
				datastore = instance.datastore,
				created_by = user.username,
				is_published = True
				)