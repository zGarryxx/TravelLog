from django.urls import path
from . import views

# Define las URL para la aplicación
urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.login_usuario, name='login'),
    path('register/', views.registrar_usuario, name='register'),
    path('logout/', views.logout_usuario, name='logout'),
    path('home/', views.home_view, name='home'),
    path('regiones/', views.gestionar_regiones, name='gestionar_regiones'),
    path('regiones/eliminar/<str:region_nombre>/', views.eliminar_region, name='eliminar_region'),
    path('regiones/editar/<str:region_nombre>/', views.editar_region, name='editar_region'),
    path('lugares/', views.gestionar_lugares, name='gestionar_lugares'),
    path('lugares/eliminar/<str:lugar_nombre>/', views.eliminar_lugar, name='eliminar_lugar'),
    path('lugares/editar/<str:lugar_nombre>/', views.editar_lugar, name='editar_lugar'),
    path('sincronizar/', views.sincronizar_datos, name='sincronizar_datos'),
    path('lugares/borrar-todo/', views.borrar_todo_lugares, name='borrar_todo_lugares'),
    path('regiones/borrar-todo/', views.borrar_todo_regiones, name='borrar_todo_regiones'),
]