from bson import ObjectId
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .forms import RegistroForm, LoginForm, RegionForm, LugarForm, ImportarArchivoForm
from .models import Region, Lugar, Resena, Favorito, Itinerario
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
        email_ingresado = request.POST.get('username')
        Usuario = get_user_model()

        try:
            usuario_check = Usuario.objects.get(email=email_ingresado)
            if not usuario_check.is_active and usuario_check.banned_until:
                if timezone.now() > usuario_check.banned_until:
                    usuario_check.is_active = True
                    usuario_check.banned_until = None
                    usuario_check.save()
        except Usuario.DoesNotExist:
            pass

        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            usuario = authenticate(request, email=email, password=password)

            if usuario is not None:
                login(request, usuario)
                messages.success(request, f'¡Bienvenido de nuevo al campamento, {usuario.nombre}!')
                return redirect('home')

        try:
            usuario_fallido = Usuario.objects.get(email=email_ingresado)
            if not usuario_fallido.is_active:
                context = {
                    'nombre': usuario_fallido.nombre,
                    'banned_until': usuario_fallido.banned_until.isoformat() if usuario_fallido.banned_until else None,
                    'es_permanente': usuario_fallido.banned_until is None,
                    'nivel_castigo': usuario_fallido.ban_count
                }
                return render(request, 'banned.html', context)
            else:
                messages.error(request, 'Credenciales incorrectas. ¿Has olvidado tu mapa?')
        except Usuario.DoesNotExist:
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
    mis_rutas = []

    if request.user.is_authenticated:
        mi_resena = Resena.objects.using('mongodb').filter(
            usuario_id=request.user.id, lugar_nombre=nombre_lugar
        ).first()

        es_favorito = Favorito.objects.using('mongodb').filter(
            usuario_id=request.user.id, lugar_nombre=nombre_lugar
        ).exists()

        mis_rutas = Itinerario.objects.using('mongodb').filter(usuario_id=request.user.id)

    return render(request, 'detalle_lugar.html', {
        'lugar': lugar,
        'resenas': resenas,
        'mi_resena': mi_resena,
        'url_retorno': url_retorno,
        'es_favorito': es_favorito,
        'mis_rutas': mis_rutas
    })

# 17. Guardar reseña de un lugar (puntuación y comentario) por parte de un usuario autenticado.
@login_required
def guardar_resena(request, nombre_lugar):

    if request.method == 'POST':
        puntuacion = request.POST.get('puntuacion')
        comentario = request.POST.get('comentario')

        resena_existente = Resena.objects.using('mongodb').filter(
            usuario_id=request.user.id,
            lugar_nombre=nombre_lugar
        ).first()

        if resena_existente:
            resena_existente.puntuacion = int(puntuacion)
            resena_existente.comentario = comentario
            resena_existente.save(using='mongodb')
            messages.success(request, "¡Reseña actualizada!")
        else:
            nuevo_id_manual = str(ObjectId())

            Resena.objects.using('mongodb').create(
                id=nuevo_id_manual,
                usuario_id=request.user.id,
                usuario_nombre=request.user.nombre,
                lugar_nombre=nombre_lugar,
                puntuacion=int(puntuacion),
                comentario=comentario
            )
            messages.success(request, "¡Reseña publicada con éxito!")

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

# 20. Mostrar una lista de los itinerarios personalizados creados por el usuario autenticado, con la opción de ver detalles, editar o eliminar cada itinerario.
@login_required
def mis_itinerarios(request):

    rutas = Itinerario.objects.using('mongodb').filter(usuario_id=request.user.id).order_by('-fecha_creacion')
    return render(request, 'mis_itinerarios.html', {'rutas': rutas})

# 21. Crear un nuevo itinerario para el usuario autenticado, asegurando que el título del itinerario sea proporcionado y que la lista de paradas comience vacía.
@login_required
def crear_itinerario(request):

    if request.method == 'POST':
        nombre_ruta = request.POST.get('titulo')
        if nombre_ruta:
            nueva_ruta = Itinerario(
                usuario_id=request.user.id,
                titulo=nombre_ruta,
                paradas=[]
            )
            nueva_ruta.save(using='mongodb')
            messages.success(request, f"¡Ruta '{nombre_ruta}' creada! Ahora añade paradas.")

    return redirect('mis_itinerarios')

# 22. Agregar un lugar como parada a un itinerario específico del usuario autenticado, asegurando que el lugar no se agregue más de una vez al mismo itinerario.
@login_required
def agregar_parada(request, nombre_lugar):

    if request.method == 'POST':
        itinerario_id = request.POST.get('itinerario_id')

        if itinerario_id:
            try:
                ruta = Itinerario.objects.using('mongodb').get(id=itinerario_id, usuario_id=request.user.id)

                if nombre_lugar not in ruta.paradas:
                    ruta.paradas.append(nombre_lugar)
                    ruta.save(using='mongodb')
                    messages.success(request, f"¡Añadido a tu ruta '{ruta.titulo}'!")
                else:
                    messages.warning(request, f"Este lugar ya estaba en la ruta '{ruta.titulo}'.")

            except Itinerario.DoesNotExist:
                messages.error(request, "Hubo un error al encontrar el itinerario.")

    return redirect('detalle_lugar', nombre_lugar=nombre_lugar)

# 23. Mostrar los detalles de un itinerario específico.
@login_required
def detalle_itinerario(request, itinerario_id):

    try:
        ruta = Itinerario.objects.using('mongodb').get(id=itinerario_id, usuario_id=request.user.id)

        lugares_db = Lugar.objects.using('mongodb').filter(nombre__in=ruta.paradas)

        paradas_info = []
        for nombre in ruta.paradas:
            lugar = next((l for l in lugares_db if l.nombre == nombre), None)
            if lugar:
                paradas_info.append(lugar)

        return render(request, 'detalle_itinerario.html', {
            'ruta': ruta,
            'paradas_info': paradas_info
        })
    except Itinerario.DoesNotExist:
        messages.error(request, "No se encontró el itinerario.")
        return redirect('mis_itinerarios')

# 24. Eliminar una parada específica de un itinerario.
@login_required
def eliminar_parada(request, itinerario_id, nombre_lugar):

    try:
        ruta = Itinerario.objects.using('mongodb').get(id=itinerario_id, usuario_id=request.user.id)
        if nombre_lugar in ruta.paradas:
            ruta.paradas.remove(nombre_lugar)
            ruta.save(using='mongodb')
            messages.info(request, f"'{nombre_lugar}' se ha quitado de la ruta.")
    except Itinerario.DoesNotExist:
        pass

    return redirect('detalle_itinerario', itinerario_id=itinerario_id)

# 25. Eliminar un itinerario completo, asegurando que solo el usuario que creó el itinerario pueda eliminarlo y que se elimine de forma permanente de la base de datos.
@login_required
def eliminar_itinerario(request, itinerario_id):

    try:
        ruta = Itinerario.objects.using('mongodb').get(id=itinerario_id, usuario_id=request.user.id)
        titulo = ruta.titulo
        ruta.delete(using='mongodb')
        messages.info(request, f"El itinerario '{titulo}' ha sido eliminado para siempre.")
    except Itinerario.DoesNotExist:
        pass

    return redirect('mis_itinerarios')

# 26. Permitir al usuario mover una parada hacia arriba o hacia abajo dentro de su itinerario.
@login_required
def mover_parada(request, itinerario_id, nombre_lugar, direccion):

    try:
        ruta = Itinerario.objects.using('mongodb').get(id=itinerario_id, usuario_id=request.user.id)
        paradas = ruta.paradas

        if nombre_lugar in paradas:
            idx = paradas.index(nombre_lugar)

            if direccion == 'up' and idx > 0:
                paradas[idx], paradas[idx - 1] = paradas[idx - 1], paradas[idx]
                ruta.paradas = paradas
                ruta.save(using='mongodb')

            elif direccion == 'down' and idx < len(paradas) - 1:
                paradas[idx], paradas[idx + 1] = paradas[idx + 1], paradas[idx]
                ruta.paradas = paradas
                ruta.save(using='mongodb')

    except Itinerario.DoesNotExist:
        messages.error(request, "Error al modificar la ruta.")

    return redirect('detalle_itinerario', itinerario_id=itinerario_id)

# 27. Mostrar estadísticas globales sobre los lugares, como el número total de valoraciones, los lugares mejor valorados, el promedio de puntuación por categoría y las rutas más populares basadas en las paradas más comunes.
@login_required
def estadisticas_globales(request):

    total_rutas_creadas = Itinerario.objects.using('mongodb').count()
    total_valoraciones = Resena.objects.using('mongodb').count()
    usuarios_unicos = len(set(Resena.objects.using('mongodb').values_list('usuario_id', flat=True)))

    mejores_lugares = Resena.objects.using('mongodb').values('lugar_nombre').annotate(
        puntuacion_media=Avg('puntuacion'),
        total_votos=Count('id')
    ).order_by('-puntuacion_media')[:5]

    lugares = Lugar.objects.using('mongodb').all()
    mapa_categorias = {lugar.nombre: lugar.tipo for lugar in lugares}
    resenas = Resena.objects.using('mongodb').all()
    stats_categorias = {}

    for resena in resenas:
        categoria = mapa_categorias.get(resena.lugar_nombre, 'Otros')
        if categoria not in stats_categorias:
            stats_categorias[categoria] = {'suma': 0, 'conteo': 0}
        stats_categorias[categoria]['suma'] += resena.puntuacion
        stats_categorias[categoria]['conteo'] += 1

    promedio_categorias = []
    for cat, data in stats_categorias.items():
        promedio = data['suma'] / data['conteo']
        porcentaje_entero = int((promedio / 5.0) * 100)

        promedio_categorias.append({
            'categoria': cat,
            'promedio': round(promedio, 1),
            'porcentaje': porcentaje_entero
        })

    promedio_categorias = sorted(promedio_categorias, key=lambda x: x['promedio'], reverse=True)

    rutas = Itinerario.objects.using('mongodb').all()
    conteo_paradas = {}
    for ruta in rutas:
        for parada in ruta.paradas:
            if parada in conteo_paradas:
                conteo_paradas[parada] += 1
            else:
                conteo_paradas[parada] = 1

    top_rutas_raw = sorted(conteo_paradas.items(), key=lambda item: item[1], reverse=True)[:10]

    top_rutas = [{'nombre': k, 'cantidad': v} for k, v in top_rutas_raw]

    return render(request, 'estadisticas.html', {
        'total_rutas_creadas': total_rutas_creadas,
        'total_valoraciones': total_valoraciones,
        'usuarios_unicos': usuarios_unicos,
        'mejores_lugares': mejores_lugares,
        'promedio_categorias': promedio_categorias,
        'top_rutas': top_rutas
    })

# 28. Panel de administración para gestionar usuarios, revisar reseñas recientes y mostrar estadísticas globales, asegurando que solo los usuarios con rol de administrador puedan acceder a esta sección.
@login_required(login_url='login')
def panel_administracion(request):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Acceso denegado.')
        return redirect('home')

    Usuario = get_user_model()
    usuarios = Usuario.objects.all().order_by('-id')
    resenas_recientes_crudas = Resena.objects.using('mongodb').all().order_by('-fecha')[:10]

    resenas_recientes = []
    for r in resenas_recientes_crudas:
        mongo_id = str(r.pk)
        resenas_recientes.append({
            'safe_id': mongo_id,
            'lugar_nombre': r.lugar_nombre,
            'usuario_nombre': r.usuario_nombre,
            'puntuacion': r.puntuacion,
            'fecha': r.fecha,
        })

    return render(request, 'admin_panel.html', {
        'usuarios': usuarios,
        'resenas_recientes': resenas_recientes,
        'total_usuarios': usuarios.count(),
        'total_lugares': Lugar.objects.using('mongodb').count(),
        'total_rutas': Itinerario.objects.using('mongodb').count(),
        'total_resenas': Resena.objects.using('mongodb').count(),
    })

# 29. Banear a un usuario por un período determinado (15 días para el primer baneo, 30 días para el segundo baneo y permanente para el tercer baneo), asegurando que solo los administradores puedan realizar esta acción y que no se puedan banear otros administradores.
@login_required(login_url='login')
def banear_usuario(request, user_id):

    if request.method == 'POST':
        if request.user.rol != 'admin' and not request.user.is_superuser:
            return redirect('home')

        Usuario = get_user_model()
        usuario_target = get_object_or_404(Usuario, id=user_id)

        if usuario_target.is_superuser or usuario_target.rol == 'admin':
            messages.error(request, "Error: No tienes permisos para banear a un administrador.")
            return redirect('panel_admin')

        tipo_baneo = request.POST.get('tipo_baneo')

        if tipo_baneo == '15':
            usuario_target.ban_count += 1
            usuario_target.is_active = False
            usuario_target.banned_until = timezone.now() + timedelta(days=15)
            messages.warning(request, f"Se ha aplicado una suspensión de 15 días a {usuario_target.nombre}.")

        elif tipo_baneo == '30':
            usuario_target.ban_count += 1
            usuario_target.is_active = False
            usuario_target.banned_until = timezone.now() + timedelta(days=30)
            messages.warning(request, f"Se ha aplicado una suspensión de 30 días a {usuario_target.nombre}.")

        elif tipo_baneo == 'perma':
            usuario_target.ban_count += 1
            usuario_target.is_active = False
            usuario_target.banned_until = None
            messages.info(request, f"La cuenta de {usuario_target.nombre} ha sido suspendida PERMANENTEMENTE.")

        usuario_target.save()

    return redirect('panel_admin')

# 30. Desbanear a un usuario, asegurando que solo los administradores puedan realizar esta acción y que se restablezca el acceso total a la cuenta del usuario.
@login_required(login_url='login')
def desbanear_usuario(request, user_id):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        return redirect('home')

    Usuario = get_user_model()
    usuario_target = get_object_or_404(Usuario, id=user_id)

    usuario_target.is_active = True
    usuario_target.banned_until = None
    usuario_target.ban_count = 0
    usuario_target.save()

    messages.info(request, f"La cuenta de {usuario_target.nombre} ha sido restaurada. Vuelve a tener acceso total.")

    return redirect('panel_admin')

# 31. Eliminar un usuario de forma permanente, asegurando que solo los administradores puedan realizar esta acción y que no se puedan eliminar otros administradores.
@login_required(login_url='login')
def eliminar_usuario(request, user_id):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        return redirect('home')

    Usuario = get_user_model()
    usuario_target = get_object_or_404(Usuario, id=user_id)

    if not usuario_target.is_superuser and usuario_target.rol != 'admin':
        usuario_target.delete()
        messages.info(request, f"La cuenta de {usuario_target.nombre} ha sido eliminada de la base de datos.")

    return redirect('panel_admin')

# 32. Eliminar una reseña de forma permanente, asegurando que solo los administradores puedan realizar esta acción y que se elimine de forma permanente de la base de datos.
@login_required(login_url='login')
def eliminar_resena_admin(request, resena_id):

    if request.user.rol != 'admin' and not request.user.is_superuser:
        return redirect('home')

    try:
        Resena.objects.using('mongodb').filter(id=resena_id).delete()

        messages.info(request, "Reseña eliminada correctamente de la plataforma.")
    except Exception as e:
        messages.error(request, f"Error al eliminar la reseña: {e}")

    return redirect('panel_admin')