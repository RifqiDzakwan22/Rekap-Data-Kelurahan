from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import pandas as pd
from io import BytesIO
from .models import DataPenduduk
from django.db.models import Count


# ---------------------- Custom Register Form ----------------------
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


# ---------------------- Penduduk Views ----------------------
@login_required
def list_penduduk(request):
    query = request.GET.get('q')
    penduduk = DataPenduduk.objects.filter(nama__icontains=query) if query else DataPenduduk.objects.all()
    return render(request, 'rekap/list_penduduk.html', {'penduduk': penduduk})


@login_required
def export_excel(request):
    penduduk = DataPenduduk.objects.all().values()
    df = pd.DataFrame(penduduk)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=data_penduduk.xlsx'
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data Penduduk')
    return response


@login_required
def export_pdf(request):
    penduduk = DataPenduduk.objects.all()
    html_string = render_to_string('rekap/export_pdf.html', {'penduduk': penduduk})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=data_penduduk.pdf'
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse('Terjadi kesalahan saat membuat PDF')
    return response


@login_required
def grafik_penduduk(request):
    data = DataPenduduk.objects.values('rt').annotate(jumlah=Count('id')).order_by('rt')
    rt_labels = [str(item['rt']) for item in data]
    rt_counts = [item['jumlah'] for item in data]
    return render(request, 'rekap/grafik_penduduk.html', {'rt_labels': rt_labels, 'rt_counts': rt_counts})


@login_required
def tambah_penduduk(request):
    if request.method == 'POST':
        nik = request.POST['nik']
        no_kk = request.POST['no_kk']
        nama = request.POST['nama']
        alamat = request.POST['alamat']
        rt = request.POST['rt']
        rw = request.POST['rw']
        tanggal_lahir = request.POST['tanggal_lahir']
        foto = request.FILES.get('foto')

        if DataPenduduk.objects.filter(nik=nik).exists():
            messages.error(request, 'NIK sudah terdaftar.')
            return redirect('tambah_penduduk')

        DataPenduduk.objects.create(
            nik=nik,
            no_kk=no_kk,
            nama=nama,
            alamat=alamat,
            rt=rt,
            rw=rw,
            tanggal_lahir=tanggal_lahir,
            foto=foto
        )
        messages.success(request, 'Data penduduk berhasil ditambahkan.')
        return redirect('list_penduduk')
    return render(request, 'rekap/tambah_penduduk.html')


@login_required
def edit_penduduk(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk mengedit.')
        return redirect('list_penduduk')

    penduduk = get_object_or_404(DataPenduduk, pk=pk)
    if request.method == 'POST':
        penduduk.nik = request.POST['nik']
        penduduk.no_kk = request.POST['no_kk']
        penduduk.nama = request.POST['nama']
        penduduk.alamat = request.POST['alamat']
        penduduk.rt = request.POST['rt']
        penduduk.rw = request.POST['rw']
        penduduk.tanggal_lahir = request.POST['tanggal_lahir']
        if request.FILES.get('foto'):
            penduduk.foto = request.FILES.get('foto')
        penduduk.save()
        messages.success(request, 'Data penduduk berhasil diperbarui.')
        return redirect('list_penduduk')
    return render(request, 'rekap/edit_penduduk.html', {'penduduk': penduduk})


@login_required
def hapus_penduduk(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus.')
        return redirect('list_penduduk')
    penduduk = get_object_or_404(DataPenduduk, pk=pk)
    penduduk.delete()
    messages.success(request, 'Data penduduk berhasil dihapus.')
    return redirect('list_penduduk')


# ---------------------- Register, User Management ----------------------
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Pendaftaran berhasil, silakan login.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'rekap/register.html', {'form': form})


@login_required
def daftar_user(request):
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk melihat daftar user.')
        return redirect('list_penduduk')
    users = User.objects.all()
    return render(request, 'rekap/daftar_user.html', {'users': users})


@user_passes_test(lambda u: u.is_superuser)
def hapus_user(request, user_id):
    user = User.objects.get(id=user_id)
    if user.username != 'admin':
        user.delete()
        messages.success(request, f'User {user.username} berhasil dihapus.')
    else:
        messages.error(request, 'Akun admin tidak dapat dihapus.')
    return redirect('daftar_user')
