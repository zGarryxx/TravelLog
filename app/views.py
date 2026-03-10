from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, LoginForm

# 1. Página de inicio (Landing page pública)
def inicio(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'inicio.html')

# 2. Registro de nuevos viajeros
def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'register.html', {'form': form})

# 3. Inicio de sesión
def login_usuario(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            usuario = authenticate(request, email=email, password=password)
            if usuario is not None:
                login(request, usuario)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# 4. Cerrar sesión
def logout_usuario(request):
    logout(request)
    return redirect('inicio')

# 5. Dashboard principal (Solo para usuarios autenticados)
@login_required(login_url='login')
def home_view(request):
    return render(request, 'home.html')