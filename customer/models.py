from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/Customer/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
    email = models.CharField(max_length=100,null=False,default='')
    profession = models.CharField(max_length=100,null=False,default='')
    email_notifications = models.BooleanField(default=False)
    sms_notifications = models.BooleanField(default=False)
    call_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=False)
    fb = models.CharField(max_length=100,null=False,default='')
    ig = models.CharField(max_length=100,null=False,default='')
    twitter = models.CharField(max_length=100,null=False,default='')
   
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_instance(self):
        return self
    def __str__(self):
        return self.user.first_name