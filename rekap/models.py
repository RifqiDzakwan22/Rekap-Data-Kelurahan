from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class DataPenduduk(models.Model):
    nik = models.CharField(max_length=16, unique=True)
    no_kk = models.CharField(max_length=20, blank=True, null=True)
    nama = models.CharField(max_length=100)
    alamat = models.TextField()
    rt = models.CharField(max_length=3)
    rw = models.CharField(max_length=3)
    tanggal_lahir = models.DateField()
    foto = models.ImageField(upload_to='foto_penduduk/', blank=True, null=True)

    def __str__(self):
        return f"{self.nama} - {self.nik}"

class Histori(models.Model):
    ACTION_CHOICES = [
        ('add', 'Add'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Pengguna yang melakukan aksi
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)  # Jenis aksi
    object_type = models.CharField(max_length=100)  # Jenis objek yang diubah
    object_id = models.PositiveIntegerField()  # ID objek yang diubah
    timestamp = models.DateTimeField(default=timezone.now)  # Waktu tindakan dilakukan
    details = models.TextField(null=True, blank=True)  # Rincian tentang tindakan

    def __str__(self):
        return f'{self.user} - {self.action} - {self.object_type}'
