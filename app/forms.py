from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario, Region, Lugar
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
import re

# Obtenemos el modelo de usuario actual (tu app.Usuario)
UsuarioActivo = get_user_model()

# Formulario de registro personalizado que hereda de ModelForm para crear un nuevo usuario con el modelo personalizado "Usuario"
class RegistroForm(forms.ModelForm):

    nombre = forms.CharField(
        label="Nombre Completo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@gmail.com'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '********'})
    )

    class Meta:
        model = get_user_model()
        fields = ['nombre', 'email', 'password']

    # --- TUS VALIDACIONES (clean_email y clean_password) ---
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        dominios_permitidos = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'icloud.com']

        if UsuarioActivo.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")

        dominio = email.split('@')[-1]
        if dominio not in dominios_permitidos:
            raise ValidationError(f"Dominio no permitido. Solo se aceptan: {', '.join(dominios_permitidos)}.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8 or len(password) > 30:
            raise ValidationError("La contraseña debe tener entre 8 y 30 caracteres.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Debe incluir al menos una mayúscula.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Debe incluir al menos una minúscula.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Debe incluir al menos un número.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.nombre = self.cleaned_data["nombre"]
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# Personalizamos el formulario de autenticación para que use el campo de correo electrónico en lugar del nombre de usuario
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Correo Electrónico")

# Formulario para crear o editar una región, utilizando el modelo Region y personalizando los campos con widgets para mejorar la apariencia del formulario en la interfaz de usuario
class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['nombre', 'pais']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Europa del Sur'}),
            'pais': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Italia'}),
        }

# Formulario para crear o editar un lugar, utilizando el modelo Lugar y personalizando los campos con widgets para mejorar la apariencia del formulario en la interfaz de usuario
class LugarForm(forms.ModelForm):
    class Meta:
        model = Lugar
        fields = ['nombre', 'ciudad', 'tipo', 'descripcion', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Museo del Prado'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Madrid'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Museo, Parque, Playa...'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Breve historia o descripción...'}),
            'imagen': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL de una foto (opcional)'}),
        }

# Formulario para importar un archivo, con un campo de tipo FileField que permite al usuario seleccionar un archivo desde su dispositivo.
class ImportarArchivoForm(forms.Form):
    archivo = forms.FileField(
        label="Selecciona archivo",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json, .csv'
        })
    )