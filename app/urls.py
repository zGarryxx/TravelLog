from django.urls import path
from . import views

# Define las URL para la aplicación
urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.login_usuario, name='login'),
    path('register/', views.registrar_usuario, name='register'),
    path('logout/', views.logout_usuario, name='logout'),
    path('home/', views.home_view, name='home'),
]