import datetime

from django import template
register = template.Library()

primero = 0
almacenado =""
contador=-1
@register.filter
def dividir(value, arg):
    """Removes all values of arg from the given string"""
    return int(value) /int(arg)

@register.filter
def almacenar(value):
    global almacenado
    if value != almacenado:
        almacenado = value
        return True
    else:
        return False

@register.filter
def get_contador(value):
    global contador
    return contador


@register.filter
def incrementar_contador(value):
    global contador
    contador = contador +1

@register.filter
def reiniciar_contador(value):
    global contador
    contador =-1

@register.filter
def dias_restantes(value):
    ahora = datetime.datetime.now().date()
    return (value - ahora).days

@register.filter
def valorada(foto,valoraciones):
    variable = False
    for v in valoraciones:
        if v.foto == foto:
            variable = True
            break
    return variable

@register.filter
def restar(uno,dos):
    return float(uno)-float(dos)

@register.filter
def primero(value):
    global primero
    return primero == 0
@register.filter
def primero_(value):
    global primero
    primero = primero+1

@register.filter
def reiniciar(value):
    global primero
    primero = 0

@register.filter
def comparar(uno,dos):
    print(str(uno))
    print(str(dos))
    return str(uno) == str(dos)

@register.filter
def en_curso(inicio,fin):
    if inicio == datetime.datetime.now().date() or fin == datetime.datetime.now().date() or (inicio < datetime.datetime.now().date() and fin > datetime.datetime.now().date()):
        return True
    return False
