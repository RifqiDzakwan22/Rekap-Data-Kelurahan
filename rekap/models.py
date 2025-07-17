from django.db import models

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
