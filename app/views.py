from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistroForm, LoginForm, RegionForm, LugarForm, ImportarArchivoForm
from .models import Region, Lugar, Resena, Favorito
import json
import csv
import io


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
            user = form.save(commit=False)

            user.nombre = form.cleaned_data.get('nombre')

            user.rol = 'viajero'
            user.is_superuser = False
            user.is_staff = False

            user.save()
            messages.success(request, '¡Registro completado con éxito!')
            return redirect('login')
        else:
            messages.error(request, 'Revisa los errores en el formulario.')
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
            nuevo_lugar.save(using='mongodb')
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

# 12. Sincronizar Datos desde Archivo
@login_required(login_url='login')
def sincronizar_datos(request):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        form = ImportarArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            nombre_archivo = archivo.name.lower()
            contador = 0

            try:
                # --- CASO 1: ARCHIVO JSON -> PUNTOS DE INTERÉS ---
                if nombre_archivo.endswith('.json'):
                    data = json.load(archivo)
                    lista_lugares = data if isinstance(data, list) else [data]
                    for item in lista_lugares:
                        if not Lugar.objects.using('mongodb').filter(nombre=item['nombre']).exists():
                            Lugar.objects.using('mongodb').create(
                                nombre=item['nombre'],
                                ciudad=item.get('ciudad', 'Desconocida'),
                                tipo=item.get('tipo', 'Otros'),
                                descripcion=item.get('descripcion', ''),
                                imagen=item.get('imagen', '')
                            )
                            contador += 1
                    messages.success(request, f'✅ {contador} lugares sincronizados.')
                    return redirect('gestionar_lugares')

                # --- CASO 2: ARCHIVO CSV -> REGIONES ---
                elif nombre_archivo.endswith('.csv'):
                    decoded_file = archivo.read().decode('utf-8')
                    io_string = io.StringIO(decoded_file)
                    reader = csv.DictReader(io_string)
                    for row in reader:
                        if not Region.objects.using('mongodb').filter(nombre=row['nombre']).exists():
                            Region.objects.using('mongodb').create(
                                nombre=row['nombre'],
                                pais=row.get('pais', 'Desconocido')
                            )
                            contador += 1
                    messages.success(request, f'✅ {contador} regiones sincronizadas.')
                    return redirect('gestionar_regiones')

                # --- CASO 3: ARCHIVO NO VÁLIDO ---
                else:
                    messages.error(request, '❌ Formato no válido. Solo se acepta .json (Lugares) o .csv (Regiones).')

            except Exception as e:
                messages.error(request, f'❌ Error en la carga: {e}')
    else:
        form = ImportarArchivoForm()

    return render(request, 'sincronizar.html', {'form': form})

# 13. Borrado masivo de lugares y regiones (solo para admin)
@login_required(login_url='login')
def borrar_todo_lugares(request):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        return redirect('home')

    Lugar.objects.using('mongodb').all().delete()
    messages.success(request, "💥 Catálogo de lugares vaciado por completo.")
    return redirect('gestionar_lugares')

# 14. Borrado masivo de lugares y regiones (solo para admin)
@login_required(login_url='login')
def borrar_todo_regiones(request):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        return redirect('home')

    Region.objects.using('mongodb').all().delete()
    messages.success(request, "💥 Lista de regiones vaciada por completo.")
    return redirect('gestionar_regiones')

# 15. Explorar Destinos (filtro por nombre, ciudad, tipo y región)
def explorar_destinos(request):

    request.session['ultima_busqueda'] = request.get_full_path()

    query_nombre = request.GET.get('nombre', '')
    query_ciudad = request.GET.get('ciudad', '')
    query_categoria = request.GET.get('categoria', '')

    solo_favoritos = request.GET.get('solo_favoritos')
    destinos = Lugar.objects.using('mongodb').all()

    if query_nombre:
        destinos = destinos.filter(nombre__icontains=query_nombre)

    if query_ciudad:
        destinos = destinos.filter(ciudad=query_ciudad)

    if query_categoria:
        destinos = destinos.filter(tipo=query_categoria)

    if solo_favoritos == '1' and request.user.is_authenticated:
        mis_favoritos = Favorito.objects.using('mongodb').filter(usuario_id=request.user.id)
        nombres_fav = [fav.lugar_nombre for fav in mis_favoritos]
        destinos = destinos.filter(nombre__in=nombres_fav)

    ciudades = Lugar.objects.using('mongodb').values_list('ciudad', flat=True).distinct().order_by('ciudad')
    categorias = Lugar.objects.using('mongodb').values_list('tipo', flat=True).distinct().order_by('tipo')

    context = {
        'destinos': destinos,
        'ciudades': ciudades,
        'categorias': categorias,
        'nombre_actual': query_nombre,
        'ciudad_actual': query_ciudad,
        'categoria_actual': query_categoria,
        'solo_favoritos_actual': solo_favoritos,
    }

    return render(request, 'explorar.html', context)

# 16. Detalle de Lugar para mostrar toda su información
def detalle_lugar(request, nombre_lugar):

    lugar = Lugar.objects.using('mongodb').get(nombre=nombre_lugar)
    resenas = Resena.objects.using('mongodb').filter(lugar_nombre=nombre_lugar).order_by('-fecha')
    url_retorno = request.session.get('ultima_busqueda', '/explorar/')

    mi_resena = None
    es_favorito = False

    if request.user.is_authenticated:
        mi_resena = Resena.objects.using('mongodb').filter(
            usuario_id=request.user.id, lugar_nombre=nombre_lugar
        ).first()

        es_favorito = Favorito.objects.using('mongodb').filter(
            usuario_id=request.user.id, lugar_nombre=nombre_lugar
        ).exists()

    return render(request, 'detalle_lugar.html', {
        'lugar': lugar,
        'resenas': resenas,
        'mi_resena': mi_resena,
        'url_retorno': url_retorno,
        'es_favorito': es_favorito
    })

# 17. Guardar reseña de un lugar (puntuación y comentario) por parte de un usuario autenticado.
@login_required
def guardar_resena(request, nombre_lugar):

    if request.method == 'POST':
        puntuacion = request.POST.get('puntuacion')
        comentario = request.POST.get('comentario')

        existe = Resena.objects.using('mongodb').filter(
            usuario_id=request.user.id,
            lugar_nombre=nombre_lugar
        ).exists()

        resena, created = Resena.objects.using('mongodb').update_or_create(
            usuario_id=request.user.id,
            lugar_nombre=nombre_lugar,
            defaults={
                'usuario_nombre': request.user.nombre,
                'puntuacion': int(puntuacion),
                'comentario': comentario,
            }
        )

        if existe:
            messages.success(request, "¡Reseña actualizada correctamente!")
        else:
            messages.success(request, "¡Tu reseña ha sido publicada con éxito!")

    return redirect('detalle_lugar', nombre_lugar=nombre_lugar)

# 18. Borrar la reseña de un lugar por parte del usuario que la creó, asegurando que solo el autor pueda eliminar su reseña.
@login_required
def borrar_resena(request, nombre_lugar):

    resena = Resena.objects.using('mongodb').filter(
        usuario_id=request.user.id,
        lugar_nombre=nombre_lugar
    )

    if resena.exists():
        resena.delete()
        messages.info(request, "Tu reseña ha sido eliminada correctamente.")

    return redirect('detalle_lugar', nombre_lugar=nombre_lugar)

# 19. Marcar o desmarcar un lugar como favorito por parte de un usuario autenticado, asegurando que solo el usuario pueda gestionar sus favoritos.
@login_required
def toggle_favorito(request, nombre_lugar):

    if request.method == 'POST':
        favorito = Favorito.objects.using('mongodb').filter(
            usuario_id=request.user.id,
            lugar_nombre=nombre_lugar
        ).first()

        if favorito:
            favorito.delete()
            messages.info(request, "Eliminado de tu lista de favoritos.")
        else:
            nuevo_favorito = Favorito(
                usuario_id=request.user.id,
                lugar_nombre=nombre_lugar
            )
            nuevo_favorito.save(using='mongodb')
            messages.success(request, "¡Añadido a tus favoritos!")

    return redirect('detalle_lugar', nombre_lugar=nombre_lugar)