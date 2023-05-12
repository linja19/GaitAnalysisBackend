from django.db import models

# Create your models here.

class User(models.Model):
    userID = models.CharField(unique=True,max_length=15,primary_key=True)
    signal = models.TextField(blank=True)
    last_update = models.CharField(max_length=15,default="0")

    def __str__(self):
        return str(self.userID)

class DoubleSupportTime(models.Model):
    userID = models.ForeignKey(User,on_delete=models.CASCADE)
    timestamp = models.CharField(max_length=15)
    value = models.CharField(max_length=10,null=True)

    def __str__(self):
        return str(self.userID)+" "+str(self.value)

class Asymmetry(models.Model):
    userID = models.ForeignKey(User,on_delete=models.CASCADE)
    timestamp = models.CharField(max_length=15)
    value = models.CharField(max_length=10,null=True)

    def __str__(self):
        return str(self.userID)+" "+str(self.value)

class SwingVariance(models.Model):
    userID = models.ForeignKey(User,on_delete=models.CASCADE)
    timestamp = models.CharField(max_length=15)
    value = models.CharField(max_length=10,null=True)

    def __str__(self):
        return str(self.userID)+" "+str(self.value)