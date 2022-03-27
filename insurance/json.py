from .models import *
from rest_framework import serializers ####### serializers: qui faire la liaison
from django.contrib.auth.models import User

class jsonPolicy(serializers.ModelSerializer):
    class Meta:
        model=Policy
        fields='__all__'######## tous le table au lieu d'ecrire le code json faire __all__

class jsonPolicyRecord(serializers.ModelSerializer):
    class Meta:
        model=PolicyRecord
        fields='__all__'

class jsonCategory(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields='__all__'

class jsonPayment(serializers.ModelSerializer):
    class Meta:
        model=Purchase
        fields='__all__'

class jsonQuestion(serializers.ModelSerializer):
    class Meta:
        model=Question
        fields='__all__'
class json_user(serializers.ModelSerializer):
    class Meta:
        model=User
        fields='__all__'


