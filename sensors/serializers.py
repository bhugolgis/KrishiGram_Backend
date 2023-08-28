
from numpy import generic
from rest_framework import serializers
from .models import *
from rest_framework_gis.serializers import GeoFeatureModelSerializer



class PostDevicesAPISerailzer(serializers.ModelSerializer):
    latitude=serializers.CharField(max_length=10,required=False)
    longitude=serializers.CharField(max_length=10,required=False)
    class Meta:
        model = devices
        fields = ('device_id' , 'sensor_type' , 'latitude' , 'longitude')
    
    def create(self, data):
        data.pop('latitude')
        data.pop('longitude')
        return devices.objects.create(**data)
        



# class SensorpropertySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = devices
#         fields = ('latitude', 'longitude','device_id')

# class SensorExcelSerializer(serializers.ModelSerializer):
#     property = SensorpropertySerializer()

#     class Meta:
#         model = SoilSensor
#         fields = '__all__'






# class SensorpropertySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = devices
#         fields = ('latitude', 'longitude','device_id')

# class SensorSerializerss(serializers.ModelSerializer):
#     property = SensorpropertySerializer()
#     class Meta:
#         model = SoilSensor
#         fields = ('Battery', 'EC_S1', 'EC_S2', 'Moisture_S1', 'Moisture_S2', 
#                   'Temperature_S1', 'Temperature_S2', 'created_at', 'property','Timestamp')
        


# class SensorpropertydataviewSerializer(serializers.ModelSerializer):
#     model = devices
#     fields = ('latitude','longitude','device_id')

class SensordataviewSerializer(serializers.ModelSerializer):
    class Meta :
        model = SoilSensor
        fields = ('Battery','EC_S1','EC_S2','Moisture_S1','Moisture_S2','Temperature_S1','Temperature_S2','Raw_S1','Raw_S2','created_at','devices','Timestamp') 
        depth = 1


        


# excel download geojson data SensorSerialize
class SensorlistSerializer(serializers.ModelSerializer):
    device_id =serializers.SerializerMethodField()
    class Meta:
        model = SoilSensor
        fields = ('Battery', 'EC_S1', 'EC_S2', 'Moisture_S1', 'Moisture_S2', 
                  'Temperature_S1', 'Temperature_S2','device_id','Timestamp','Raw_S1','Raw_S2')
    
    def get_device_id(self,obj):
        device_id = obj.devices.device_id
        return device_id



class GeosensorExcelListSerialzier(serializers.Serializer):
    device_id = serializers.CharField(max_length = 255 , required = False)
    sensor_type = serializers.CharField(max_length = 50 , required = True)
    start_date = serializers.DateField(required = True)
    end_date = serializers.DateField(required = True)
    class Meta:
        fields = ('device_id' , 'sensor_type' , 'start_date' , 'end_date')

    def validate(self, data):
        if data["sensor_type"] == "" or data["sensor_type"] == None:
            raise serializers.ValidationError("This Fields can not be empty !!")
        if data["start_date"] == "" or data["start_date"] == None:
            raise serializers.ValidationError("This field can not be empty !!")
        if data["end_date"] == "" or data["end_date"] == None:
            raise serializers.ValidationError("This field can not be empty !!")
        return data



# ADVISORY



class AdvisorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Advisory
        fields = ('crop_name', 'Stage', 'Agromet_Advisory','created_at' , 'Advisory_date')


class uploadExcelserializer(serializers.Serializer):
    excel_file =serializers.FileField( required=False)
    Advisory_date = serializers.DateField(required = True)




class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layers
        fields = "__all__"
        





class JsonuploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)


    class Meta:
        fields = ('file',)





# class SensorpropertySerializerlast7days(serializers.ModelSerializer):
#     class Meta:
#         model = devices
#         fields = ('latitude', 'longitude','device_id')

# class SensorSerializerslast7days(serializers.ModelSerializer):
#     property = SensorpropertySerializer()
#     class Meta:
#         model = SoilSensor
#         fields = ('Battery', 'EC_S1', 'EC_S2', 'Moisture_S1', 'Moisture_S2', 
#                   'Temperature_S1', 'Temperature_S2', 'created_at', 'property','Timestamp')






# from rest_framework import serializers
# from .models import SoilSensor

# class SensorpropertySerializerlatestdays(serializers.ModelSerializer):
#     class Meta:
#         model = devices
#         fields = ('latitude', 'longitude','device_id')

# class SensorSerializerslatestdays(serializers.ModelSerializer):
#     property = SensorpropertySerializer()
#     class Meta:
#         model = SoilSensor
#         fields = ('Battery', 'EC_S1', 'EC_S2', 'Moisture_S1', 'Moisture_S2', 
#                   'Temperature_S1', 'Temperature_S2', 'created_at', 'property','Timestamp')






class WeatherUploadCSVSerializer(serializers.Serializer):
    csv_file = serializers.FileField(required=False)


    class Meta:
        fields = ('csv_file',)





class SensorSerializerSheet(serializers.ModelSerializer):
    class Meta:
        model = SoilSensor
        fields = '__all__'


# ////////////







class SoilSensorGraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilSensor
        fields = ['Battery', 'EC_S1', 'EC_S2', 'Moisture_S1', 'Moisture_S2', 'Temperature_S1', 'Temperature_S2','Timestamp','Raw_S1','Raw_S2']


