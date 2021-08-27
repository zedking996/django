from django.contrib import admin
from .models import Device
from import_export.admin import ImportExportModelAdmin

@admin.register(Device)

class DeviceAdmin(ImportExportModelAdmin):
    list_display = ('id', 'ip_address', 'hostname', 'vendor')