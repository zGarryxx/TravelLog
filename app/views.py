from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistroForm, LoginForm, RegionForm, LugarForm
from .models import Region, Lugar


# 1. Página de inicio
def inicio(request):

    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'inicio.html')

# 2. Registro
def registrar_usuario(request):

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Aventura desbloqueada! Registro completado. Ya puedes iniciar sesión.')
            return redirect('login')
        else:
            messages.error(request, 'Ocurrió un error en el registro. Revisa los datos.')
    else:
        form = RegistroForm()
    return render(request, 'register.html', {'form': form})

# 3. Login
def login_usuario(request):

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            usuario = authenticate(request, email=email, password=password)
            if usuario is not None:
                login(request, usuario)
                messages.success(request, f'¡Bienvenido de nuevo al campamento, {usuario.nombre}!')
                return redirect('home')
        messages.error(request, 'Credenciales incorrectas. ¿Has olvidado tu mapa?')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# 4. Logout
def logout_usuario(request):

    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente. ¡Buen viaje!')
    return redirect('inicio')

# 5. Dashboard
@login_required(login_url='login')
def home_view(request):

    return render(request, 'home.html')

# 6. Gestión de Regiones
@login_required(login_url='login')
def gestionar_regiones(request):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos de Administrador para entrar en esta zona.')
        return redirect('home')

    if request.method == 'POST':
        form = RegionForm(request.POST)
        if form.is_valid():
            nueva_region = form.save(commit=False)
            nueva_region.save(using='mongodb')
            messages.success(request, '¡Región añadida con éxito al mapa!')
            return redirect('gestionar_regiones')
        else:
            messages.error(request, 'Error al crear la región. Revisa los datos.')
    else:
        form = RegionForm()

    regiones = Region.objects.using('mongodb').all()
    return render(request, 'regiones.html', {'form': form, 'regiones': regiones})

# 7. Editar Región
@login_required(login_url='login')
def editar_region(request, region_nombre):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')

    try:
        region = Region.objects.using('mongodb').get(nombre=region_nombre)
    except Region.DoesNotExist:
        messages.error(request, 'La región que intentas editar no existe.')
        return redirect('gestionar_regiones')

    if request.method == 'POST':
        form = RegionForm(request.POST)
        if form.is_valid():
            nuevo_nombre = form.cleaned_data['nombre']
            nuevo_pais = form.cleaned_data['pais']

            Region.objects.using('mongodb').filter(nombre=region_nombre).update(
                nombre=nuevo_nombre,
                pais=nuevo_pais
            )

            messages.success(request, f'¡La región "{nuevo_nombre}" ha sido actualizada con éxito!')
            return redirect('gestionar_regiones')
    else:
        form = RegionForm(initial={
            'nombre': region.nombre,
            'pais': region.pais
        })

    return render(request, 'editar_region.html', {'form': form, 'region_nombre': region.nombre})

# 8. Eliminar Región
@login_required(login_url='login')
def eliminar_region(request, region_nombre):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')

    borrados, _ = Region.objects.using('mongodb').filter(nombre=region_nombre).delete()

    if borrados > 0:
        messages.success(request, f'La región "{region_nombre}" ha sido borrada del mapa.')
    else:
        messages.error(request, 'La región que intentas eliminar no existe o ya fue borrada.')

    return redirect('gestionar_regiones')

# 9. Gestión de Lugares
@login_required(login_url='login')
def gestionar_lugares(request):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos de Administrador.')
        return redirect('home')

    if request.method == 'POST':
        form = LugarForm(request.POST)
        if form.is_valid():
            nuevo_lugar = form.save(commit=False)
            nuevo_lugar.save(using='mongodb')  # Guardamos directo en Mongo
            messages.success(request, '¡Punto de interés añadido con éxito al catálogo!')
            return redirect('gestionar_lugares')
        else:
            messages.error(request, 'Error al crear el lugar. Revisa los datos.')
    else:
        form = LugarForm()

    lugares = Lugar.objects.using('mongodb').all()
    return render(request, 'lugares.html', {'form': form, 'lugares': lugares})

# 10. Editar Lugar
@login_required(login_url='login')
def editar_lugar(request, lugar_nombre):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')

    try:
        lugar = Lugar.objects.using('mongodb').get(nombre=lugar_nombre)
    except Lugar.DoesNotExist:
        messages.error(request, 'El lugar que intentas editar no existe.')
        return redirect('gestionar_lugares')

    if request.method == 'POST':
        form = LugarForm(request.POST)
        if form.is_valid():

            Lugar.objects.using('mongodb').filter(nombre=lugar_nombre).update(
                nombre=form.cleaned_data['nombre'],
                ciudad=form.cleaned_data['ciudad'],
                tipo=form.cleaned_data['tipo'],
                descripcion=form.cleaned_data['descripcion'],
                imagen=form.cleaned_data['imagen']
            )

            nuevo_nombre = form.cleaned_data['nombre']
            messages.success(request, f'¡El lugar "{nuevo_nombre}" ha sido actualizado con éxito!')
            return redirect('gestionar_lugares')
    else:
        form = LugarForm(initial={
            'nombre': lugar.nombre,
            'ciudad': lugar.ciudad,
            'tipo': lugar.tipo,
            'descripcion': lugar.descripcion,
            'imagen': lugar.imagen
        })

    return render(request, 'editar_lugar.html', {'form': form, 'lugar_nombre': lugar.nombre})

# 11. Eliminar Lugar
@login_required(login_url='login')
def eliminar_lugar(request, lugar_nombre):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')

    borrados, _ = Lugar.objects.using('mongodb').filter(nombre=lugar_nombre).delete()

    if borrados > 0:
        messages.success(request, f'El lugar "{lugar_nombre}" ha sido demolido de la base de datos.')
    else:
        messages.error(request, 'El lugar no existe o ya fue borrado.')

    return redirect('gestionar_lugares')