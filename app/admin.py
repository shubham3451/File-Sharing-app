from django.contrib import admin
from django.db import models

# Import all models explicitly if needed
from .models import User
from .models.file import *
from .models.membership import *
from .models.user import OTP

def get_all_field_names(model):
    return [field.name for field in model._meta.fields]

def get_searchable_fields(model):
    return [
        field.name for field in model._meta.fields
        if isinstance(field, (
            models.CharField, models.EmailField,
            models.TextField, models.GenericIPAddressField
        ))
    ]

class BaseAdmin(admin.ModelAdmin):
    def __init__(self, model, admin_site):
        self.list_display = get_all_field_names(model)
        self.search_fields = get_searchable_fields(model)
        super().__init__(model, admin_site)

# Register models with dynamic admin class
for model in [User, OTP, Folder, File, FileVersion, Trash, FileShare,
              FileAccessLog, FileScan, Plan, Membership]:
    admin.site.register(model, type(f"{model.__name__}Admin", (BaseAdmin,), {}))
