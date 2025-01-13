from django.contrib.auth.models import AbstractUser
from django.db import models
class LawSection(models.Model):
    section_number = models.CharField(max_length=20)
    act_name = models.CharField(max_length=100)
    description = models.TextField()
    keywords = models.TextField(help_text="Comma-separated keywords that trigger this section")
    punishment = models.TextField(blank=True, null=True)
    class Meta:
        # Remove unique_together and keep only UniqueConstraint
        constraints = [
            models.UniqueConstraint(
                fields=['act_name', 'section_number'], 
                name='unique_act_section'
            )
        ]
    def __str__(self):
        return f"{self.act_name} Section {self.section_number}"    
    def get_keywords_list(self):
        return [k.strip().lower() for k in self.keywords.split(',')]
class PoliceUser(AbstractUser):
    ROLES = (
        ('inspector', 'Inspector'),
        ('sub_inspector', 'Sub Inspector'),
        ('officer', 'Police Officer'),
    )    
    role = models.CharField(max_length=20, choices=ROLES)
    jurisdiction_area = models.CharField(max_length=100)
    badge_number = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.role}"
class FIR(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Closed', 'Closed'),
    ]
    suggested_sections = models.ManyToManyField(LawSection, blank=True, related_name='related_firs')
    number = models.AutoField(primary_key=True)
    date_filed = models.DateTimeField(auto_now_add=True)
    complainant_name = models.CharField(max_length=100)
    complainant_address = models.TextField()
    complainant_aadhar = models.CharField(max_length=12)
    complainant_phone = models.CharField(max_length=10)
    incident_place = models.CharField(max_length=200, blank=True, null=True)
    statement = models.TextField()
    audio_file = models.FileField(upload_to='fir_audio/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    def __str__(self):
        return f"FIR {self.number} - {self.complainant_name}"

