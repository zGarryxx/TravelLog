from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
import uuid


# Modelo para gestionar la creación de usuarios personalizados, incluyendo métodos para crear usuarios regulares y superusuarios.
class UsuarioManager(BaseUserManager):

    def create_user(self, email, nombre, rol='viajero', password=None):

        if not email:
            raise ValueError("El usuario debe tener un email")
        email = self.normalize_email(email)
        usuario = self.model(email=email, nombre=nombre, rol=rol)
        if rol == 'admin':
            usuario.is_staff = True
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, nombre, password=None):

        usuario = self.create_user(email=email, nombre=nombre, rol='admin', password=password)
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save(using=self._db)
        return usuario


# Modelo de usuario personalizado que se almacena en la base de datos SQLite para gestionar la autenticación y permisos.
class Usuario(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    rol = models.CharField(max_length=20, default='viajero')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    def __str__(self):
        return self.email


# Modelo para representar las regiones turísticas, almacenados en MongoDB. Incluye campos para el nombre de la región y el país al que pertenece.
class Region(models.Model):

    nombre = models.CharField(max_length=100)
    pais = models.CharField(max_length=100)

    class Meta:
        db_table = 'regiones'
        managed = False

# Modelo para representar los lugares turísticos, almacenados en MongoDB. Incluye campos para nombre, ciudad, tipo, descripción e imagen.
class Lugar(models.Model):

    nombre = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.URLField(max_length=300, blank=True, null=True)

    class Meta:
        db_table = 'lugares'
        managed = False

    def to_dict(self):

        return {
            "id": self.id,
            "nombre": self.nombre,
            "ciudad": self.ciudad,
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "imagen": self.imagen,
        }


# Modelo para representar las valoraciones de los lugares turísticos, almacenados en MongoDB. Incluye campos para el ID del lugar, usuario, estrellas, comentario y fecha.
class Valoracion(models.Model):

    lugar_id = models.IntegerField()
    usuario = models.CharField(max_length=100)
    estrellas = models.IntegerField()
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:

        db_table = 'valoraciones'
        managed = False


# Modelo para representar las reseñas de los lugares turísticos, almacenados en MongoDB. Incluye campos para el ID del usuario, nombre del usuario, nombre del lugar, puntuación, comentario y fecha.
class Resena(models.Model):

    id = models.CharField(primary_key=True, max_length=24, editable=False)
    usuario_id = models.IntegerField()
    usuario_nombre = models.CharField(max_length=100)
    lugar_nombre = models.CharField(max_length=200)

    puntuacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'resenas'


# Modelo para representar los lugares turísticos favoritos de los usuarios, almacenados en MongoDB. Incluye campos para el ID del usuario, nombre del lugar y fecha de agregado.
class Favorito(models.Model):

    id = models.CharField(primary_key=True, max_length=100, default=uuid.uuid4, editable=False)
    usuario_id = models.IntegerField()
    lugar_nombre = models.CharField(max_length=200)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'favoritos'


# Modelo para representar los itinerarios personalizados creados por los usuarios, almacenados en MongoDB.
class Itinerario(models.Model):

    id = models.CharField(primary_key=True, max_length=100, default=uuid.uuid4, editable=False)
    usuario_id = models.IntegerField()
    titulo = models.CharField(max_length=200)

    paradas = models.JSONField(default=list)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'itinerarios'