from django import forms
from .models import Doctor, Hospital

class DoctorForm(forms.ModelForm):
    DOC_PW = forms.CharField(widget=forms.PasswordInput, label="Password")
    
    # choices 정의
    SPECIALTIES_CHOICES = [
        ('흉부외과', '흉부외과'),
        ('신경외과', '신경외과'),
    ]
    
    HOSPITAL_CHOICES = [
        ('삼성병원','1' ),
        ('서울대학교병원','2' ),
        ( '세브란스병원','3'),
        ( '한림대병원','4')
    ]

    # choices 적용
    DOC_MAJOR = forms.ChoiceField(choices=SPECIALTIES_CHOICES)
    # HOS_ID = forms.ChoiceField(choices=HOSPITAL_CHOICES)

    class Meta:
        model = Doctor
        fields = ["DOC_ID", "DOC_PW", "DOC_NAME", "DOC_CONTACT", "DOC_MAJOR", "HOS_ID"]