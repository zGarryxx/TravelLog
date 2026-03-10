from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario


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