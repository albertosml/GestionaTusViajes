from django.contrib import admin

# Register your models here.
from .models import PuntuacionFoto,Pais,Ciudad,Item_Valoracion,Valor,EntradaForo,Valoracion,Viaje,ElementoPresupuesto,PagoUsuario,CosasPorVer,Foto
admin.site.register(Ciudad)
admin.site.register(EntradaForo)
admin.site.register(Valoracion)
admin.site.register(Viaje)
admin.site.register(ElementoPresupuesto)
admin.site.register(PagoUsuario)
admin.site.register(CosasPorVer)
admin.site.register(Foto)
admin.site.register(Item_Valoracion)
admin.site.register(Valor)
admin.site.register(Pais)
admin.site.register(PuntuacionFoto)

