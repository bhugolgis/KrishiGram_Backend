from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(LayerGroup)
admin.site.register(Layer)
admin.site.register(Workspace)
admin.site.register(Datastore)
admin.site.register(Server)