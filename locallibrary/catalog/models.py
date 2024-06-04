from django.db import models
from django.urls import reverse
import uuid
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
# Create your models here.
from django.db import models

class Hospital(models.Model):
    HOS_ID = models.IntegerField(primary_key=True)
    HOS_NAME = models.TextField()
    HOS_ADDRESS = models.TextField()
    HOS_CONTACT = models.TextField()
    
    def __str__(self):
        return self.HOS_NAME


class Doctor(models.Model):
    DOC_ID = models.CharField(primary_key=True, max_length=255)
    DOC_PW = models.TextField()
    DOC_NAME = models.TextField()
    DOC_CONTACT = models.TextField()
    DOC_MAJOR = models.TextField()
    HOS_ID = models.ForeignKey(Hospital, on_delete=models.CASCADE)

    def __str__(self):
        return self.DOC_NAME


class Patient(models.Model):
    PAT_ID = models.AutoField(primary_key=True)
    PAT_NAME = models.TextField()
    PAT_BIRTH = models.TextField()
    PAT_ADDRESS = models.TextField(null=True, blank=True)
    PAT_CONTACT = models.TextField(null=True, blank=True)
    DOC_ID = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.PAT_NAME


class XImage(models.Model):
    XIMAGE_ID = models.AutoField(primary_key=True)
    PAT_ID = models.ForeignKey(Patient, on_delete=models.CASCADE)
    POSITION = models.TextField(null=True, blank=True)
    XIMAGE_GENDER = models.TextField(null=True, blank=True)
    XIMAGE_AGE = models.IntegerField(null=True, blank=True)
    XIMAGE_PATH = models.ImageField(upload_to='ximages/', null=True, blank=True)

    def __str__(self):
        return f"XImage {self.XIMAGE_ID} for {self.PAT_ID}"
    
    # IMG_PATH = models.ImageField(upload_to='ximages/', null=True, blank=True)

    # def __str__(self):
    #     return f"XImage {self.XIMAGE_ID} for {self.PAT_ID.PAT_NAME}"


class MIR(models.Model):
    XIMAGE_ID = models.OneToOneField(XImage, on_delete=models.CASCADE, primary_key=True)
    MIR_RESULT = models.FloatField()
    MIR_MIR = models.TextField()
    MIR_DATE = models.DateTimeField(auto_now_add=True)
    DOC_ID = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    def __str__(self):
        return f"MIR result for {self.MIR_DATE}"

    





