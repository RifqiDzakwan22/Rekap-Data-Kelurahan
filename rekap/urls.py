from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.list_penduduk, name='list_penduduk'),
    path('tambah/', views.tambah_penduduk, name='tambah_penduduk'),
    path('edit/<int:pk>/', views.edit_penduduk, name='edit_penduduk'),
    path('hapus/<int:pk>/', views.hapus_penduduk, name='hapus_penduduk'),
    path('register/', views.register, name='register'),
    path('daftar-user/', views.daftar_user, name='daftar_user'),
    path('login/', auth_views.LoginView.as_view(template_name='rekap/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('hapus-user/<int:user_id>/', views.hapus_user, name='hapus_user'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('export-pdf/', views.export_pdf, name='export_pdf'),
    path('grafik-penduduk/', views.grafik_penduduk, name='grafik_penduduk'),
]
