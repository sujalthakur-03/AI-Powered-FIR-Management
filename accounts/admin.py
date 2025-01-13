from django.contrib import admin
from .models import PoliceUser, FIR, LawSection
# Register your models here.
admin.site.register(PoliceUser)
admin.site.register(FIR)
admin.site.register(LawSection)