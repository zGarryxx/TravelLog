from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario, Region, Lugar


# Formulario de registro personalizado que hereda de ModelForm para crear un nuevo usuario con el modelo personalizado "Usuario"
class RegistroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    class Meta:
        model = Usuario
        fields = ['email', 'nombre', 'password']

    # Sobrescribimos el méthod save para asegurarnos de que la contraseña se guarde correctamente utilizando el méthod set_password del modelo de usuario
    def save(self, commit=True):

        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])

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