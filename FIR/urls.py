"""
URL configuration for FIR project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# MAJOR/FIR/FIR/urls.py
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from accounts import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),  # Add this line for root URL
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('submit_fir/', views.submit_fir, name='submit_fir'),
    path('fir/<int:fir_number>/', views.view_fir, name='view_fir'),
    path('serve_audio/<int:fir_number>/', views.serve_audio, name='serve_audio'),
    path('verify_password/', views.verify_password, name='verify_password'),
    path('update_fir_status/', views.update_fir_status, name='update_fir_status'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
