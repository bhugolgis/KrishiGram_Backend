from django.db import models
from django.contrib.gis.db import models

# Create your models here.


# Sensorproperty
class devices(models.Model):

    SENSOR_CHOICES = (
        ('Soil Sensor', 'Soil Sensor'),
        ('Weather Sensor', 'Weather Sensor'),
    )
    location = models.PointField(blank = True , null= True)
    device_id = models.CharField(max_length=255 , unique= True )
    sensor_type = models.CharField(max_length=255, choices = SENSOR_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)



# Sensor
class SoilSensor(models.Model):
    Battery = models.FloatField(blank = True , null = True)
    EC_S1 = models.FloatField(blank = True , null = True)
    EC_S2 = models.FloatField(blank = True , null = True)
    Moisture_S1 = models.FloatField(blank = True , null = True)
    Moisture_S2 = models.FloatField(blank = True , null = True)
    Temperature_S1 = models.FloatField(blank = True , null = True)
    Temperature_S2 = models.FloatField(blank = True , null = True)
    Raw_S1 = models.FloatField(blank = True , null = True)
    Raw_S2 = models.FloatField(blank = True , null = True)
    devices = models.ForeignKey(devices,on_delete=models.CASCADE, related_name ='Sensor_Sensorproperty')
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    # created_at = models.DateField(auto_now_add=True)
    Timestamp = models.DateTimeField(blank = True , null = True)
    



class WeatherSensor(models.Model):
    Timestamp = models.DateTimeField(blank = True , null = True)
    Wind_dir = models.FloatField(blank = True , null = True)
    Solar_rad = models.FloatField(blank = True , null = True)
    Leaf_up = models.FloatField(blank = True , null = True)
    Leaf_down = models.FloatField(blank = True , null = True)
    Battery_voltage =models.FloatField(blank = True , null = True)
    Voltage_power_supply =models.FloatField(blank = True , null = True)
    Wind_speed = models.FloatField(blank = True , null = True)
    Wind_gust = models.FloatField(blank = True , null = True)
    Max_rain = models.FloatField(blank = True , null = True)
    Daily_rain = models.FloatField(blank = True , null = True)
    Rain_counter = models.FloatField(blank = True , null = True)
    Temperature = models.FloatField(blank = True , null = True)
    Relative_Humidity =models.FloatField(blank = True , null = True)
    Dew_point = models.FloatField(blank = True , null = True)
    Soil_temp = models.FloatField(blank = True , null = True)
    water_content = models.FloatField(blank = True , null = True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)









class Advisory(models.Model):
    crop_name = models.CharField(max_length=100 , blank= True , null = True)
    Stage = models.CharField(max_length=100 , blank = True , null = True )
    Agromet_Advisory = models.TextField(blank= True , null= True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    Advisory_date = models.DateField(blank = True , null = True)
    # excel_file = models.FileField(upload_to='uploads/', null=True, blank=True)






class Layers(models.Model):
    layer_name = models.CharField(max_length=100 , blank= True , null = True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)














    





