from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import pandas as pd
from io import BytesIO
from . models import DataPenduduk, Histori
from django.db.models import Count
from django.core.paginator import Paginator



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


# ---------------------- Login View ----------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('list_penduduk')
        else:
            messages.error(request, 'Nama pengguna atau kata sandi salah.')

    return render(request, 'rekap/login.html')


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

        penduduk = DataPenduduk.objects.create(
            nik=nik,
            no_kk=no_kk,
            nama=nama,
            alamat=alamat,
            rt=rt,
            rw=rw,
            tanggal_lahir=tanggal_lahir,
            foto=foto
        )

        # simpan histori
        log_aktivitas(request.user, 'add', 'Penduduk', penduduk.id, f"Menambahkan penduduk dengan NIK {penduduk.nik}")

        messages.success(request, 'Data penduduk berhasil ditambahkan.')
        return redirect('list_penduduk')
    return render(request, 'rekap/tambah_penduduk.html')

# fungsi untuk menyimpan histori aktivitas
def log_aktivitas(user, action, object_type, object_id, details):
    Histori.objects.create(
        user=user,
        action=action,
        object_type=object_type,
        object_id=object_id,
        details=details
    )

@login_required
def histori_aktivitas(request):
    # ambil data histori aktivitas
    if request.GET.get('q'):
        historis = Histori.objects.filter(details__icontains=request.GET['q']).order_by('-timestamp')  # jika ingin filter pencarian
    else:
        historis = Histori.objects.all().order_by('-timestamp')  # untuk ambil semua data histori yang ada

    # paginasi: Menampilkan 10 item per halaman
    paginator = Paginator(historis, 10)
    page = request.GET.get('page')
    historis = paginator.get_page(page)

    return render(request, 'rekap/histori.html', {'historis': historis})


@login_required
def edit_penduduk(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk mengedit.')
        return redirect('list_penduduk')

    penduduk = get_object_or_404(DataPenduduk, pk=pk)
    if request.method == 'POST':
        old_data = penduduk

        penduduk.nik = request.POST.get('nik')
        penduduk.no_kk = request.POST.get('no_kk')
        penduduk.nama = request.POST.get('nama')
        penduduk.alamat = request.POST.get('alamat')
        penduduk.rt = request.POST.get('rt')
        penduduk.rw = request.POST.get('rw')
        penduduk.tanggal_lahir = request.POST.get('tanggal_lahir')
        if request.FILES.get('foto'):
            penduduk.foto = request.FILES.get('foto')
        penduduk.save()

        # simpan histori setelah perubahan
        log_aktivitas(request.user, 'edit', 'Penduduk', penduduk.id, f"Memperbarui penduduk dengan NIK {old_data.nik}, mengubah data: {old_data.nama} -> {penduduk.nama}")


        messages.success(request, 'Data penduduk berhasil diperbarui.')
        return redirect('list_penduduk')
    return render(request, 'rekap/edit_penduduk.html', {'penduduk': penduduk})

@login_required
def hapus_histori(request, pk):
    # khusus admin yang bisa menghapus histori
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus histori aktivitas.')
        return redirect('histori_aktivitas')  # Ganti dengan URL histori yang sesuai

    # mencari histori berdasarkan primary key (ID)
    histori = get_object_or_404(Histori, pk=pk)
    
    # hapus histori
    histori.delete()
    messages.success(request, 'Histori aktivitas berhasil dihapus.')
    
    return redirect('histori_aktivitas')  # Kembali ke halaman histori aktivitas

@login_required
def hapus_penduduk(request, pk):
    # periksa apakah user memiliki izin admin
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus.')
        return redirect('list_penduduk')

    try:
        # mencari penduduk berdasarkan pk
        penduduk = DataPenduduk.objects.get(pk=pk)

        # menyimpan histori sebelum menghapus data
        log_aktivitas(request.user, 'delete', 'Penduduk', penduduk.id, f"Menghapus penduduk dengan NIK {penduduk.nik}")

        # menghapus data penduduk
        penduduk.delete()
        messages.success(request, 'Data penduduk berhasil dihapus.')
    except DataPenduduk.DoesNotExist:
        # jika data penduduk tidak ditemukan, berikan pesan error
        messages.error(request, 'Data penduduk tidak ditemukan.')
    
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
            messages.error(request, 'Pendaftaran gagal, cek kembali data Anda.')

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
