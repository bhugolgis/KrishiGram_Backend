from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(SoilSensor)
admin.site.register(devices)
admin.site.register(Advisory)
admin.site.register(WeatherSensor)

# @admin.register(Sensor)
# class SensorAdmin(admin.ModelAdmin):
#     readonly_fields = ('created_at', )