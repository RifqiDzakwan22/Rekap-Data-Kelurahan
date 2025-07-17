from django.contrib import admin
from .models import DataPenduduk

@admin.register(DataPenduduk)
class DataPendudukAdmin(admin.ModelAdmin):
    list_display = ('nik', 'no_kk', 'nama', 'alamat', 'rt', 'rw', 'tanggal_lahir')
    search_fields = ('nik', 'no_kk', 'nama', 'alamat')
    list_filter = ('rt', 'rw')

