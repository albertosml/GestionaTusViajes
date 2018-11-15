from django.core.serializers import json
from django.forms import forms, models, SelectDateWidget
from django.shortcuts import render, render_to_response
from .forms import AnadirViajeM, AnadirCiudad, AnadirCosaQueVer, AnadirValoracion, AnadirEntrada, AnadirFoto, \
    AnadirElemento, AnadirFotoViaje, AnadirUsuario, UsuarioUpdate
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import datetime #for checking date range.
from django.http import HttpResponse, request, HttpResponseRedirect
from django.template import loader, RequestContext
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from socket import socket
import datetime
from .models import Valor, Item_Valoracion, Ciudad,PuntuacionFoto, Viaje, Valoracion, Foto, EntradaForo, ElementoPresupuesto, CosasPorVer, PagoUsuario, User


# se trata de la pagina principal de la aplicacion


def travels(request):
    ahora = datetime.datetime.now().date()
    top_ciudades = devolver_top_ciudades()
    valoraciones_pendientes = devolver_valoraciones_pendientes(request)
    mis_viajes = devolver_mis_viajes(request)
    viajes_antiguos = list()
    viajes_siguientes = list()
    for v in mis_viajes:
        if v.fecha_fin < ahora:
            viajes_antiguos.append(v)
        else:
            viajes_siguientes.append(v)
    context = {'top_ciudades': top_ciudades, 'valoraciones_pendientes': valoraciones_pendientes, 'viajes_antiguos': viajes_antiguos , 'viajes_siguientes' : viajes_siguientes}
    return render(request, 'mis_viajes.html' , context)

def devolver_top_ciudades():
    top = Ciudad.objects.filter(aceptada=True).order_by('-nota')[:5]
    return top

def devolver_valoraciones_pendientes(request):
    pendientes = list()
    viajes = devolver_mis_viajes(request)
    ahora = datetime.datetime.now().date()
    ## hay que tratar la excepcion si no tiene viajes el usuario
    for viaje in viajes:
        if viaje.fecha_fin < ahora:
            for ciudad in viaje.ciudades.all():
                valoracion = Valoracion.objects.filter(nombre_usuario=request.user.username, nombre_ciudad=ciudad, fecha_visita__range=(viaje.fecha_inicio, viaje.fecha_fin))
                if valoracion.count() == 0:
                    lista = list()
                    lista.append(ciudad)
                    lista.append(viaje.fecha_inicio)
                    lista.append(viaje.fecha_fin)
                    pendientes.append(lista)

    return pendientes

def devolver_mis_viajes(request):

    a = User.objects.filter(username=request.user.username)
    if a.count()==0:
        return ""
    for usuario in a:
        viajes = usuario.viaje_set.all().order_by('fecha_inicio')
    return viajes

def city(request,pk):
    ciudad = Ciudad.objects.get(pk=pk)
    
    page_f = request.GET.get('page_f')
    fotos = Foto.objects.filter(nombre_ciudad=pk,idViaje=None)
    valoraciones_foto = list()
    for f in fotos:
        puntuaciones = PuntuacionFoto.objects.filter(foto=f)
        for p in puntuaciones:
            valoraciones_foto.append(p)

    paginator = Paginator(fotos, 1)
    try:
        f = paginator.page(page_f)
    except PageNotAnInteger:
        f = paginator.page(1)
    except EmptyPage:
        f = paginator.page(paginator.num_pages)
    
    page_v = request.GET.get('page_v')
    valoraciones = Valoracion.objects.filter(nombre_ciudad=pk)
    paginator_v = Paginator(valoraciones, 1)
    try:
        v = paginator_v.page(page_v)
    except PageNotAnInteger:
        v = paginator_v.page(1)
    except EmptyPage:
        v = paginator_v.page(paginator_v.num_pages)

    page_e = request.GET.get('page_e')
    entradas = EntradaForo.objects.filter(nombre_ciudad=pk)
    paginator_e = Paginator(entradas, 1)
    try:
        e = paginator_e.page(page_e)
    except PageNotAnInteger:
        e = paginator_e.page(1)
    except EmptyPage:
        e = paginator_e.page(paginator_e.num_pages)

    visitantes = len(list(Viaje.objects.filter(planificacion=False,ciudades__in = [ciudad],fecha_fin__lte=datetime.datetime.now())))
    context = {'visitantes' : visitantes,'ciudad': ciudad, 'fotos': f, 'valoraciones': v, 'entradas': e, 'valoraciones_foto': valoraciones_foto}
    print(visitantes)
    return render(request,'ciudad.html',context)

def travel(request,pk):
    viaje = Viaje.objects.get(pk=pk)
    presupuesto = ElementoPresupuesto.objects.filter(idViaje=pk)

    diccionario = {}
    pagos_lista = list()
    despues = 0;
    pagado_antes = 0;
    if presupuesto is not None:
        if viaje.planificacion == True:
            for p in presupuesto:
                diccionario[p] = ""
                if p.pagar_antes == False:
                    despues = despues + float(p.precio) / float(viaje.num_personas)
                else:
                    if p.usuario_paga != "nadie":
                        pagado_antes = pagado_antes + float(p.precio) / float(viaje.num_personas)
        else:
            for p in presupuesto:
                #solo va a devolver 1 valor, pero quiero obtenerlo y no quiero queryset
                pagos = PagoUsuario.objects.filter(idElementoPresupuesto=p, nombre_usuario=request.user.username).all()
                for pago in pagos:
                    pagos_lista = list()
                    pagos_lista.append(pago)
                if len(pagos_lista) > 0:
                    diccionario[p] = pagos_lista[0]
                if p.pagar_antes == False:
                    despues = despues + float(p.precio) / float(viaje.num_personas)
                else:
                    if p.usuario_paga != "nadie":
                        pagado_antes = pagado_antes + float(p.precio) / float(viaje.num_personas)


    cosas = CosasPorVer.objects.filter(idViaje=pk).order_by('ciudad','visto','fecha_a_visitar')
    dias = set()
    diccionario_cosas = {}
    cosas_ = CosasPorVer.objects.filter(idViaje=pk).order_by('fecha_a_visitar','orden')

    cont = 0

    for cosa in cosas_:
        if cosa.fecha_a_visitar is not None:
            dias.add(cosa.fecha_a_visitar)
    for dia in sorted(dias):
        diccionario_cosas[cont] = CosasPorVer.objects.filter(fecha_a_visitar = dia , idViaje=pk).order_by('orden','visto')
        cont = cont + 1
        print(dia)
        print(list(CosasPorVer.objects.filter(fecha_a_visitar = dia , idViaje=pk)))
    diccionario_cosas[cont] = CosasPorVer.objects.filter(fecha_a_visitar = None , idViaje=pk).order_by('orden')
    fotos = Foto.objects.filter(idViaje=pk) 

    context = {'viaje' : viaje,'cosas_fecha':diccionario_cosas, 'diccionario' : diccionario, 'cosas' : cosas, 'fotos' : fotos,'despues':despues , 'antes' : pagado_antes}

    return render(request,'viaje.html',context)

@csrf_protect
def add_travel(request):
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request (binding):
        form = AnadirViajeM(request.POST)
        # Check if the form is valid:
        if form.is_valid():
            viaje = Viaje()
            viaje.nombre = form.cleaned_data['nombre']
            viaje.fecha_inicio = form.cleaned_data['fecha_inicio']
            viaje.fecha_fin = form.cleaned_data['fecha_fin']
            viaje.usuario_creador = str(request.user.username)

            viaje.coste_total = 0
            viaje.planificacion = form.cleaned_data['planificacion']

            viaje.save()
            variable = 0
            print(form.cleaned_data['num_personas'])

            if form.cleaned_data['planificacion']:
                viaje.num_personas = form.cleaned_data['num_personas']
                viaje.save()
                variable = 1

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            if variable == 1:
                return JsonResponse({'personas': False, 'pk' : viaje.pk})
            else:
                return JsonResponse({'personas': True, 'pk': viaje.pk})

    else:
        form = AnadirViajeM()
        
    return render(request, 'viaje_anadir_puro.html', {'form': form})

@csrf_protect
def anadir_travel(request):
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request (binding):
        form = AnadirViajeM(request.POST)
        # Check if the form is valid:
        if form.is_valid():
            viaje = Viaje()
            viaje.nombre = form.cleaned_data['nombre']
            viaje.fecha_inicio = form.cleaned_data['fecha_inicio']
            viaje.fecha_fin = form.cleaned_data['fecha_fin']
            viaje.usuario_creador = str(request.user.username)

            viaje.coste_total = 0
            viaje.planificacion = form.cleaned_data['planificacion']
            viaje.save()
            variable = 0
            print("creador")
            print(viaje.usuario_creador)
            if form.cleaned_data['planificacion']:
                viaje.num_personas = form.cleaned_data['num_personas']
                viaje.save()
                variable = 1

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            if variable == 1:
                print("la variable es 1, personas = false")
                return JsonResponse({'personas': False, 'pk': viaje.pk})
            else:
                return JsonResponse({'personas': True, 'pk': viaje.pk})


def add_city(request):
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = AnadirCiudad(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            ciudad = Ciudad()
            ciudad.nombre_ciudad = form.cleaned_data['nombre_ciudad']
            ciudad.nombre_pais = form.cleaned_data['nombre_pais']
            ciudad.save()

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('inicio'))

    # If this is a GET (or any other method) create the default form.
    else:
        form = AnadirCiudad()

    return render(request, 'ciudad_anadir.html', {'form': form})

@csrf_protect
def add_valoration_day(request,pk,dia):
    ciudad = Ciudad.objects.get(pk=pk)

    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = AnadirValoracion(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            if request.user.is_authenticated:
                usuario = User.objects.get(username=request.user.username)
            else:
                usuario = 'Anónimo'

            valoracion = Valoracion()
            valoracion.comentario = form.cleaned_data['comentario']

            valoracion.lo_mejor = form.cleaned_data['lo_mejor']
            valoracion.lo_peor = form.cleaned_data['lo_peor']
            valoracion.nombre_ciudad = ciudad
            valoracion.nombre_usuario = usuario
            valoracion.fecha_visita = dia
            valoracion.save()

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('ciudad',args=[pk]))

    # If this is a GET (or any other method) create the default form.
    else:
        form = AnadirValoracion()

        items = Item_Valoracion.objects.all()

    return render(request, 'valoracion_anadir.html', {'form': form, 'items' : items , 'ciudad' : pk, 'city' : ciudad, 'dia' : dia , 'dia_yn' : 1})

@csrf_protect
def add_valoration(request,pk):
    ciudad = Ciudad.objects.get(pk=pk)

    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = AnadirValoracion(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            if request.user.is_authenticated:
                usuario = User.objects.get(username=request.user.username)
            else:
                usuario = 'Anónimo'

            valoracion = Valoracion()
            valoracion.comentario = form.cleaned_data['comentario']

            valoracion.lo_mejor = form.cleaned_data['lo_mejor'] 
            valoracion.lo_peor = form.cleaned_data['lo_peor']
            valoracion.nombre_ciudad = ciudad
            valoracion.nombre_usuario = usuario
            valoracion.fecha_visita = datetime.datetime.now()
            valoracion.save()

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('ciudad',args=[pk]))

    # If this is a GET (or any other method) create the default form.
    else:
        form = AnadirValoracion()

        items = Item_Valoracion.objects.all()

    return render(request, 'valoracion_anadir.html', {'form': form, 'items' : items , 'ciudad' : pk, 'city' : ciudad, 'dia_yn' : 0})

def add_entrada(request,pk):
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = AnadirEntrada(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            ciudad = Ciudad.objects.get(pk=pk)
            if request.user.is_authenticated:
                usuario = User.objects.get(username=request.user.username)
            else:
                usuario = 'Anónimo'

            entrada = EntradaForo()
            entrada.descripcion = form.cleaned_data['descripcion']
            entrada.nombre_ciudad = ciudad
            entrada.nombre_usuario = usuario

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            entrada.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('ciudad',args=[pk]))

    # If this is a GET (or any other method) create the default form.
    else:
        form = AnadirEntrada()

    return render(request, 'entrada_anadir.html', {'form': form})

def add_photo(request,pk):
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = AnadirFoto(request.POST, request.FILES)

        # Check if the form is valid:
        if form.is_valid():
            ciudad = Ciudad.objects.get(pk=pk)
            if request.user.is_authenticated:
                usuario = User.objects.get(username=request.user.username)

                foto = Foto()
                foto.imagen = form.cleaned_data['imagen']
                foto.monumento = form.cleaned_data['monumento']
                foto.nombre_ciudad = ciudad
                foto.nombre_usuario = usuario

                # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
                foto.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('ciudad',args=[pk]))

    # If this is a GET (or any other method) create the default form.
    else:
        form = AnadirFoto()

    return render(request, 'foto_anadir.html', {'form': form})

# Desde aquí no hay que modificar los HTML

@csrf_protect
def add_payment_travel(request,id_viaje):
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = AnadirElemento(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            viaje = Viaje.objects.get(pk=id_viaje)

            elemento = ElementoPresupuesto()
            elemento.concepto = form.cleaned_data['concepto']
            elemento.pagar_antes = form.cleaned_data['pagar_antes']
            elemento.idViaje=viaje
            elemento.fin = form.cleaned_data['fin']
            elemento.inicio = form.cleaned_data['inicio']
            elemento.precio = form.cleaned_data['precio']
            elemento.tipo = form.cleaned_data['tipo']
            elemento.save()
            precio_cada = elemento.precio / viaje.num_personas
            print(precio_cada)
            viaje.coste_total = viaje.coste_total + ( precio_cada )
            viaje.save()
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)

            # redirect to a new URL:
            return JsonResponse({'viaje': id_viaje,'elemento' : elemento.pk})

        # If this is a GET (or any other method) create the default form.
    else:
        form = AnadirElemento()

    return render(request, 'viaje_anadir.html', {'form': form,'viaje' : Viaje.objects.get(pk=id_viaje)})

def gestionar_elemento_presupuesto(request):
    via = request.GET.get('viaje', None)
    el = request.GET.get('elemento', None)
    elemento = ElementoPresupuesto.objects.get(pk = el)
    val = request.GET.get('valor', None)
    usuarios_viaje = Viaje.objects.get(pk=via).usuarios.all()
    #si no se trata de un viaje de planificacion
    if len(usuarios_viaje) > 1:

        if val == "nadie":
            elemento.usuario_paga = "nadie"
            elemento.save()
            for us in usuarios_viaje:
                pago = PagoUsuario()
                pago.nombre_usuario = us
                pago.estado = "Por pagar"
                pago.idElementoPresupuesto = elemento
                pago.save()
        else:
            usuario = User.objects.get(username=val)
            elemento.usuario_paga = usuario.username
            elemento.save()
            for us in usuarios_viaje:
                pago = PagoUsuario()
                pago.nombre_usuario = us
                if us == usuario:
                    pago.estado = "Usuario compra"
                else:
                    pago.estado = "Pagado"

                pago.idElementoPresupuesto = elemento
                pago.save()
    else:
        elemento.usuario_paga = "nadie"
        elemento.save()
    return JsonResponse({'resultado' : True})

@csrf_protect
def add_thing(request,id_viaje):
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request (binding):
        form = AnadirCosaQueVer(request.POST)

        if form.is_valid():
            viaje = Viaje.objects.get(pk=id_viaje)
            elemento = CosasPorVer()
            elemento.descripcion = form.cleaned_data['descripcion']
            elemento.idViaje=viaje
            elemento.orden = form.cleaned_data['orden']
            elemento.nombre = form.cleaned_data['nombre']
            elemento.fecha_a_visitar = form.cleaned_data['fecha_a_visitar']
            elemento.fecha_visitado = form.cleaned_data['fecha_visitado']
            elemento.visto = form.cleaned_data['visto']
            elemento.save()
            print("llega aqui")
            return JsonResponse({'id': elemento.pk})

        # If this is a GET (or any other method) create the default form.
    else:
        form = AnadirCosaQueVer()
        viaje = Viaje.objects.get(pk=id_viaje)

    return render(request, 'viaje_elemento_anadir_V2.html', {'viaje' : id_viaje, 'form': form , 'ciudades' : viaje.ciudades})


@csrf_protect
def add_thing_city(request):
        # Create a form instance and populate it with data from the request (binding):

        id = request.GET.get('id_cosa', None)
        ciudad = request.GET.get('ciudad_', None)


        elemento = list(CosasPorVer.objects.filter(pk=int(id)))[0]
        for c in  Ciudad.objects.filter(pk=ciudad):
            elemento.ciudad=c


        elemento.save()
        # process the data in form.cleaned_data as required (here we just write it to the model due_back field)

        # redirect to a new URL:
        data = {
            'result' : True
        }
        return JsonResponse(data)

def edit_thing(request, id_viaje, id_cosa):
    cosa= CosasPorVer.objects.filter(idViaje=id_viaje, pk=id_cosa)

    for c in cosa:
        devolver=c
    return render(request, 'elemento_viaje.html', {'detalle': devolver})

def pagar(request):
    elemento = request.GET.get('elemento', None)
    pago = request.GET.get('pago', None)

    e = ElementoPresupuesto.objects.get(pk=elemento)
    e.usuario_paga = request.user.username
    e.save()

    for p in PagoUsuario.objects.filter(idElementoPresupuesto =e):
        if p.nombre_usuario == request.user.username:
            p.estado="Usuario compra"
        else:
            p.estado = "Pagado"

        p.save()
    data = {
        'exito': True
    }
    return JsonResponse(data)

def visitar(request):
    estado = request.GET.get('estado', None)
    elemento = request.GET.get('elemento', None)
    print("Valores= estado %s elemento id %s" % (estado, elemento))
    for i in CosasPorVer.objects.filter(pk=elemento):
        item = i

    if int(estado) is int(1):
        item.fecha_visitado = datetime.datetime.now()
        item.visto = True
        item.save()
        print("Entra aquiii")

    else:
        item.fecha_visitado = None
        item.visto = False
        item.save()

    data = {
        'exito': True,
        'estado' : int(estado),
        'nombre' : item.nombre,
        'descripcion': item.descripcion,
        'fecha_visitado': item.fecha_visitado,
        'fecha_a_visitar' : item.fecha_a_visitar,
        'ciudad' : item.ciudad.nombre_ciudad,
        'pk' : item.pk,
    }

    return JsonResponse(data)

def ciudades_viaje(id):
    ciudades = list()
    for v in Viaje.objects.filter(pk=id):
        viaje = v
    for c in viaje.ciudades.all():
        ciudades.append(c)
    return ciudades

def cargar_formulario_anadir_foto(request, id_viaje):
    print("se cargan los datos del formulario")
    ciudades = ciudades_viaje(id_viaje)
    return render(request, 'foto_anadirv2.html', {'ciudades': ciudades, 'id': id_viaje})

def anadir_foto(request):
    usuario = User.objects.get(username=request.user.username)

    ciudad =  request.GET.get('ciudad', None)
    URL = request.GET.get('url', None)
    id_viaje = request.GET.get('viaje', None)

    foto = Foto()
    viaje = list(Viaje.objects.filter(pk=id_viaje))[0]
    # foto.nombre_ciudad = form.cleaned_data['nombre_ciudad']
    foto.nombre_usuario = usuario
    foto.idViaje = viaje
    foto.URL = URL
    for c in Ciudad.objects.filter(pk=int(ciudad)):
        foto.nombre_ciudad = c

    foto.save()
    data = {
        'exito': True
    }

    return JsonResponse(data)

def buscar_usuarios(request):
    nueva_lista = list()
    usuario = request.GET.get('usuario', None)

    users = User.objects.filter(username__contains=usuario)

    for u in users:
        nueva_lista.append(u.username)
    lista = list()
    for l in nueva_lista:
        lista.append(l)
    data = {
        'usuarios': lista
    }

    return JsonResponse(data)


def buscar_ciudades(request):
    nueva_lista = list()
    ciudad = request.GET.get('ciudad', None).title()

    ciudades = Ciudad.objects.filter(nombre_ciudad__contains=(ciudad))

    for u in ciudades:
        nueva_lista.append(u.nombre_ciudad)
    lista = list()
    for l in nueva_lista:
        lista.append(l)
    data = {
        'ciudades': lista
    }

    return JsonResponse(data)


def anadir_usuarios_viaje(request):
    viaje = Viaje.objects.get(pk=request.GET.get('pk', None))
    print("ey")
    usuarios = request.GET.get('usuarios', None)

    usus = usuarios.split(",")
    print("adios")
    cantidad = len(usus)

    print("cantidad")
    print(cantidad)
    viaje.usuarios.add(request.user)
    viaje.save()
    print("primero")
    print(request.GET.get('primero', None))
    primero = request.GET.get('primero', None)


    if int(primero) != 0:
        print("se estan enviando los usuarios, no deberia al ser planificacion")
        for c in usus:
            if c != "":
                resultado = list(User.objects.filter(username=c))[0]
                viaje.usuarios.add(resultado)
        viaje.num_personas = cantidad
        print("entra a añadir usuaarios")
        print(cantidad)
    else:
        print("no puto entra")
        print("primero depsues del if")
    print(primero)
    viaje.save()

    data = {
        'exito': True
    }

    return JsonResponse(data)

def anadir_ciudades_viaje(request):
    viaje = Viaje.objects.get(pk=request.GET.get('pk', None))

    ciudades = request.GET.get('ciudades', None)
    ciud = ciudades.split(",")
    for c in range(0,len(ciud)-1):
        if c !='':
            resultado = list(Ciudad.objects.filter(nombre_ciudad__iexact=ciud[c]))[0]
            viaje.ciudades.add(resultado)

    viaje.save()

    data = {
        'exito': True,
        'pk' : request.GET.get('pk', None)
    }

    return JsonResponse(data)

def add_photo_viaje(request,pk):
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = AnadirFotoViaje(request.POST, request.FILES)

        # Check if the form is valid:
        if form.is_valid():
            viaje = Viaje.objects.get(pk=pk)
            usuario = User.objects.get(username=request.user.username)

            foto = Foto()
            foto.imagen = form.cleaned_data['imagen']
            foto.monumento = form.cleaned_data['monumento']
            foto.idViaje = viaje
            foto.nombre_usuario = usuario
            foto.ciudad = form.cleaned_data['nombre_ciudad']

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            foto.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('viaje',args=[pk]))

    # If this is a GET (or any other method) create the default form.
    else:
        form = AnadirFotoViaje(pk=pk)


    return render(request, 'foto_anadir.html', {'form': form, 'viaje': pk})

def create_user(request):
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = AnadirUsuario(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            usuario = User()
            usuario.username = form.cleaned_data['username']
            usuario.set_password(form.cleaned_data['password'])
            usuario.first_name = form.cleaned_data['first_name']
            usuario.last_name = form.cleaned_data['last_name']
            usuario.email = form.cleaned_data['email']

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            usuario.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('inicio'))

    # If this is a GET (or any other method) create the default form.
    else:
        form = AnadirUsuario()

    return render(request, 'registrar.html', {'form': form})

def update_user(request,pk):
    if len(request.user.username) == 0:
        return HttpResponseRedirect(reverse('inicio'))

    usuario = User.objects.get(username=request.user.username)

    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = UsuarioUpdate(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            usuario.set_password(form.cleaned_data['password'])
            if usuario.first_name != form.cleaned_data['first_name']: 
                usuario.first_name = form.cleaned_data['first_name']
            if usuario.last_name != form.cleaned_data['last_name']: 
                usuario.last_name = form.cleaned_data['last_name']
            if usuario.email != form.cleaned_data['email']: 
                usuario.email = form.cleaned_data['email']

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            usuario.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('inicio'))

    # If this is a GET (or any other method) create the default form.
    else:
        form = UsuarioUpdate(initial={'first_name': request.user.first_name, 'last_name': request.user.last_name, 
            'email': request.user.email, 'password': request.user.password})

    return render(request, 'perfil.html', {'form': form})

def puntuar_foto(request):
    foto = request.GET.get('foto', None)
    valor = request.GET.get('puntuacion', None)

    foto_o = Foto.objects.get(pk=foto)
    usuario = request.user
    p = PuntuacionFoto()
    p.nombre_usuario = usuario
    p.foto = foto_o
    p.puntuacion = valor
    p.save()

    media = (float(foto_o.nota) * float(foto_o.num_valoraciones) + float(valor)) / (float(foto_o.num_valoraciones) + 1)
    foto_o.nota = media
    foto_o.num_valoraciones = foto_o.num_valoraciones+1
    foto_o.save()

    data = {
        'exito': True
    }

    return JsonResponse(data)

@csrf_protect
def add_valoracion(request):
    if request.method == "POST":
        # Create a form instance and populate it with data from the request (binding):
        form = AnadirValoracion(request.POST)
        # Check if the form is valid:
        if form.is_valid():
            if request.user.is_authenticated:
                usuario = User.objects.get(username=request.user.username)
            else:
                usuario = 'Anónimo'

            valoracion = Valoracion()
            valoracion.comentario = form.cleaned_data['comentario']

            valoracion.lo_mejor = form.cleaned_data['lo_mejor']
            valoracion.lo_peor = form.cleaned_data['lo_peor']

            valoracion.nombre_usuario = usuario
            valoracion.fecha_visita = datetime.datetime.now()
            valoracion.save()

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            data = {
                'exito' : True,
                'valoracion' : valoracion.pk,

            }
        return JsonResponse(data)

@csrf_protect
def add_valoracion_dia(request):
    if request.method == "POST":
        # Create a form instance and populate it with data from the request (binding):
        form = AnadirValoracion(request.POST)
        # Check if the form is valid:
        if form.is_valid():
            if request.user.is_authenticated:
                usuario = User.objects.get(username=request.user.username)
            else:
                usuario = 'Anónimo'

            valoracion = Valoracion()
            valoracion.comentario = form.cleaned_data['comentario']

            valoracion.lo_mejor = form.cleaned_data['lo_mejor']
            valoracion.lo_peor = form.cleaned_data['lo_peor']

            valoracion.nombre_usuario = usuario
            valoracion.fecha_visita = dia
            valoracion.save()

            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            data = {
                'exito' : True,
                'valoracion' : valoracion.pk,

            }
        return JsonResponse(data)

@csrf_protect
def add_parametres_valoration(request):
    idVal = request.GET.get('idValoracion', None)
    datos = request.GET.get('datos', None)
    ciu = request.GET.get('ciudad', None)
    dia = request.GET.get('dia', None)
    ciudad = Ciudad.objects.get(pk=ciu)
    valoracion = Valoracion.objects.get(pk=idVal)
    valoracion.nombre_ciudad = ciudad
    print(dia)
    if dia != "":
        valoracion.fecha_visita = dia


    valoracion.save()

    split = datos.split(",")
    nota_media = 0
    contador = 0;
    for valor in split:
        if valor =="":
            break
        contador = contador +1

        items = valor.split(":")

        v = Valor()
        v.nota = float(items[1])
        nota_media = nota_media +v.nota
        p = Item_Valoracion.objects.get(parametro=items[0])
        v.parametro=p
        v.valoracion = valoracion
        v.save()
    media_valoracion = nota_media / contador
    valoracion.media = media_valoracion
    valoracion.save()
    media = (float(ciudad.nota) * float(ciudad.num_valoraciones) + float(media_valoracion)) / (
                float(ciudad.num_valoraciones) + 1)

    ciudad.num_valoraciones = ciudad.num_valoraciones +1
    ciudad.nota = media
    ciudad.save()

    data = {
        'exito': True,
        'ciudad' : request.GET.get('ciudad', None)
    }

    return JsonResponse(data)

def editar_viaje(request):
    #atributos que se pasan por parametros
    nombre = request.GET.get('nombre', None)
    num_personas = request.GET.get('num_personas', None)
    fecha_inicio = request.GET.get('fecha_inicio', None)
    fecha_fin = request.GET.get('fecha_fin', None)
    coste_total = request.GET.get('coste_total', None)
    planificacion = request.GET.get('planificacion', None)
    if planificacion == "False":
        planificacion = False
    else:
        planificacion = True
    ciudades_eliminar = request.GET.get('ciudades_eliminar', None)
    ciudades_anadir = request.GET.get('ciudades_anadir', None)
    usuarios_eliminar = request.GET.get('usuarios_eliminar', None)
    usuarios_anadir = request.GET.get('usuarios_anadir', None)
    pk = request.GET.get('pk', None)
    #viaje a editar
    viaje = Viaje.objects.get(pk = pk)
    viaje.nombre = nombre
    viaje.fecha_inicio = fecha_inicio
    viaje.fecha_fin = fecha_fin
    viaje.coste_total = coste_total
    planificacion_anterior = viaje.planificacion
    planificacion_actual = planificacion

    # se tienen que añadir los usuarios solamente, funciona correctamente
    if planificacion_anterior == True and planificacion_actual==False:
        anadir_usuarios_viaje_e(usuarios_anadir,viaje)
    elif planificacion_anterior == True and planificacion_actual==True:
        viaje.num_personas = num_personas
        elementos = ElementoPresupuesto.objects.filter(idViaje=viaje)
        suma = 0
        for el in elementos:
            suma = suma + float(el.precio) / float(viaje.num_personas)

        viaje.coste_total = suma
        viaje.save()

    elif planificacion_anterior == False and planificacion_actual == True:
        viaje.num_personas = num_personas
        eliminar_usuarios_viaje(request,viaje)

    else:
        gestionar_usuarios_viaje(usuarios_anadir,usuarios_eliminar,viaje)

    viaje.planificacion = planificacion
    gestionar_ciudades(ciudades_eliminar,ciudades_anadir,viaje)
    data = {'hola' : True}
    return JsonResponse(data)

def gestionar_usuarios_viaje(usuarios_anadir,usuarios_eliminar,viaje):
    usuarios_eliminar = usuarios_eliminar.split(",")


    for u in usuarios_eliminar:
        if u != "":
            usuario = User.objects.get(username = u)
            for el in ElementoPresupuesto.objects.filter(idViaje=viaje):
                if len(PagoUsuario.objects.filter(idElementoPresupuesto=el, nombre_usuario=usuario))>0:
                    pago.delete()
            viaje.usuarios.remove(usuario)
    viaje.save()
    usuarios_anadir = usuarios_anadir.split(",")
    for c in usuarios_anadir:
        if c != "":
            usuario = User.objects.get(username=c)
            viaje.usuarios.add(usuario)

    viaje.save()
    viaje.num_personas = viaje.usuarios.count()
    viaje.save()

    # ahora se tienen que asociar los pagos que hay en este viaje a los usuarios que se van a añadir
    elementos = ElementoPresupuesto.objects.filter(idViaje=viaje)
    suma = 0
    for el in elementos:
        suma = suma + float(el.precio) / float(viaje.num_personas)
        for u in usuarios_anadir:
            if u != "":
                pago = PagoUsuario()
                pago.idElementoPresupuesto = el
                pago.estado = "Por pagar"
                pago.nombre_usuario = User.objects.get(username=u)
                pago.save()

    viaje.coste_total = suma
    viaje.save()


def eliminar_usuarios_viaje(request,viaje):

    suma = 0
    for el in ElementoPresupuesto.objects.filter(idViaje = viaje):
        suma = suma + float(el.precio) / float(viaje.num_personas)
        for u in viaje.usuarios.all():
            if u != "" :
                if  len(PagoUsuario.objects.filter(idElementoPresupuesto = el,nombre_usuario = u))!=0:
                    pago.delete()
    usuario_actual = request.user.username
    for usuario in viaje.usuarios.all():
        if usuario.username != usuario_actual:
            viaje.usuarios.remove(usuario)

    viaje.coste_total = suma
    viaje.save()

def anadir_usuarios_viaje_e(usuarios,viaje):
    usus = usuarios.split(",")
    print("adios")
    cantidad = len(usus)

    print("cantidad")
    print(cantidad)
    for c in usus:
        if c != "":
            resultado = list(User.objects.filter(username=c))[0]
            viaje.usuarios.add(resultado)
    viaje.num_personas = cantidad
    print(cantidad)

    # ahora se tienen que asociar los pagos que hay en este viaje a los usuarios que se van a añadir
    elementos = ElementoPresupuesto.objects.filter(idViaje=viaje)
    suma = 0
    for el in elementos:
        suma = suma + el.precio / viaje.num_personas
        for u in usus:
            if u != "" :
                pago = PagoUsuario()
                pago.idElementoPresupuesto = el
                pago.estado = "Por pagar"
                pago.nombre_usuario = User.objects.get(username = u)
                pago.save()

    viaje.coste_total = suma
    viaje.save()

def gestionar_ciudades(ciudades_eliminar,ciudades_anadir,viaje):
    ciudades_antiguas = ciudades_eliminar.split(",")
    print("adios")
    cantidad = len(ciudades_antiguas) -1

    print("cantidad")
    print(cantidad)
    for c in ciudades_antiguas:
        if c != "":
            resultado = list(Ciudad.objects.filter(pk=c))[0]
            viaje.ciudades.remove(resultado)

    ciudades_nuevas = ciudades_anadir.split(",")
    print("adios")
    cantidad = len(ciudades_nuevas) - 1

    print("cantidad")
    print(cantidad)
    for c in ciudades_nuevas:
        if c != "":
            resultado = list(Ciudad.objects.filter(nombre_ciudad=c))[0]
            viaje.ciudades.add(resultado)
    viaje.save()

def obtener_datos_ciudad(request):
    clave = request.GET.get('pk', None)

    city = Ciudad.objects.get(pk=clave)

    data = {
        'ciudad': city.nombre_ciudad,
        'nota': city.nota,
        'num_valoraciones': city.num_valoraciones,
    }

    return JsonResponse(data)

def editar_elemento(request):
    pk = request.GET.get('pk', None)
    concepto = request.GET.get('concepto', None)
    precio = request.GET.get('precio', None)
    inicio = request.GET.get('inicio', None)
    fin = request.GET.get('fin', None)
    usuario_paga = request.GET.get('usuario_paga', None)
    pagar_antes = request.GET.get('pagar_antes', None)
    tipo = request.GET.get('tipo', None)

    elemento = ElementoPresupuesto.objects.get(pk=pk)
    elemento.concepto = concepto
    if inicio is None:
        elemento.inicio = None
    if fin is None:
        elemento.fin = None
    elemento.usuario_paga = usuario_paga
    if pagar_antes == "False":
        elemento.pagar_antes = False
    else:
        elemento.pagar_antes = True
    elemento.tipo = tipo

    if elemento.precio != precio:
        viaje = Viaje.objects.get(pk = elemento.idViaje.pk)
        viaje.coste_total = float(viaje.coste_total) - (float(elemento.precio)/viaje.num_personas) + (float(precio)/viaje.num_personas)
        viaje.save()

    elemento.precio = precio
    elemento.save()


    data = {
        'exito' : True,
        'id' : viaje.pk,
    }

    return JsonResponse(data)

def eliminar_elemento_presupuesto(request):
    viaje = Viaje.objects.get(pk=request.GET.get('viaje', None))
    elemento = ElementoPresupuesto.objects.get(pk=request.GET.get('elemento', None))
    viaje.coste_total = float(viaje.coste_total) - (float(elemento.precio)/viaje.num_personas)
    viaje.save()
    pagos = PagoUsuario.objects.filter(idElementoPresupuesto=elemento)
    for pago in pagos:
        pago.delete()
    elemento.delete()
    data = {
        'exito': True,
        'id': viaje.pk,
    }

    return JsonResponse(data)

def comprobar_usuarios_viaje(request):
    usuario = request.GET.get('usuario', None)
    id_viaje = request.GET.get('viaje', None)

    user = User.objects.filter(username__contains=usuario)
    viaje = Viaje.objects.get(pk=id_viaje)

    bandera = False

    for u in viaje.usuarios.all():
        if u.username == usuario: 
            bandera = True

    data = { 'bandera': bandera }
    return JsonResponse(data)

def comprobar_usuario_foto(request):
    usuario = request.GET.get('usuario', None)
    pk = request.GET.get('foto', None)

    u = User.objects.filter(username__contains=usuario)
    foto = Foto.objects.filter(pk=pk)

    bandera = (u.get().username == foto.get().nombre_usuario)
    
    data = { 'bandera': bandera }
    return JsonResponse(data)