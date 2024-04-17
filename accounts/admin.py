from django.contrib import admin
from .models import User, Company, AbstractUserProfile

# Register your models here.
admin.site.register(User)
admin.site.register(Company)
admin.site.register(AbstractUserProfile)

