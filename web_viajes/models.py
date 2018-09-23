# Create your models here.
from django.db import models

from django.contrib.auth.models import User

# Create your models here.

class Pais(models.Model):
    nombre_pais = models.CharField(max_length=20,primary_key=True)

    def __str__(self):
       return self.nombre_pais

class Ciudad(models.Model):
    nombre_ciudad = models.CharField(max_length=20)
    nombre_pais = models.ForeignKey(Pais, on_delete=models.CASCADE,null=False)
    nota = models.DecimalField(max_digits=2,decimal_places=1,default=0)
    num_valoraciones = models.IntegerField(default=0)
    aceptada = models.BooleanField(default=False)

    class Meta:
       unique_together = ('nombre_ciudad','nombre_pais')

    def __str__(self):
       return '{0}, {1}'.format(self.nombre_ciudad,self.nombre_pais)

class Viaje(models.Model):
    nombre = models.CharField(max_length=50)
    fecha_inicio = models.DateField(null=False)
    fecha_fin = models.DateField(null=False)
    coste_total = models.DecimalField(max_digits=6,decimal_places=2)
    usuarios = models.ManyToManyField(User)
    ciudades = models.ManyToManyField(Ciudad)
    num_personas = models.IntegerField(null=True , blank=True)
    planificacion = models.BooleanField()
    usuario_creador = models.CharField(max_length=150,default='')

    def __str__(self):
        return self.nombre

class EntradaForo(models.Model):
    descripcion = models.CharField(null=False, max_length=280)
    nombre_usuario = models.CharField(max_length=150)
    fecha_realizacion = models.DateTimeField(null=False,auto_now_add=True)
    nombre_ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE,null=False)

    def __str__(self):
        return self.descripcion

    class Meta:
        ordering = ['-fecha_realizacion']

class Valoracion(models.Model):
    fecha_visita = models.DateTimeField(null=False,auto_now_add=True)
    comentario = models.CharField(null=False, max_length=280)
    lo_mejor = models.CharField(max_length=140)
    lo_peor = models.CharField(max_length=140)
    nombre_usuario = models.CharField(max_length=150)
    nombre_ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE,null=True)
    media = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    def __str__(self):
        return '{0}, {1}, {2}'.format(self.nombre_ciudad,self.nombre_usuario, self.comentario)

    class Meta:
        ordering = ['-fecha_visita']

class Item_Valoracion(models.Model):
    parametro = models.CharField(max_length=20,null=False, primary_key=True)

    def __str__(self):
        return self.parametro

class Valor(models.Model):
    valoracion = models.ForeignKey(Valoracion, on_delete=models.CASCADE,null=False)
    parametro = models.ForeignKey(Item_Valoracion, on_delete=models.CASCADE,null=False)
    nota = models.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
       unique_together = ('valoracion','parametro')

    def __str__(self):
       return '{0}, {1}, {2}'.format(self.valoracion, self.parametro, self.nota)

class ElementoPresupuesto(models.Model):
    concepto = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=6,decimal_places=2)
    idViaje = models.ForeignKey(Viaje, on_delete=models.CASCADE,null=False)
    inicio = models.DateTimeField(null=True,blank = True)
    fin = models.DateTimeField(null=True, blank=True)
    usuario_paga = models.CharField(max_length=150,default='',null=True, blank=True)
    pagar_antes = models.BooleanField(default=False)
    tipo = models.CharField(
        choices={('Alojamiento', 'Alojamiento'), ('Transporte', 'Transporte'), ('Transporte Publico', 'Transporte Publico'), ('Comida', 'Comida'),
                 ('Monumento-Museo', 'Monumento-Museo'),('Otro', 'Otro')}, null=False, max_length=20, default='Otro')

    class Meta:
       unique_together = ('idViaje','concepto')
       ordering = ['tipo']

    def __str__(self):
        return '{0}, {1}'.format(self.idViaje,self.concepto)

class PagoUsuario(models.Model):
    nombre_usuario = models.CharField(max_length=150)
    idElementoPresupuesto = models.ForeignKey(ElementoPresupuesto, on_delete=models.CASCADE,null=False)
    estado = models.CharField(
        choices={('Pagado', 'Pagado'), ('Por pagar', 'Por pagar'), ('Usuario compra', 'Usuario compra')}, null=False, max_length=20, default='Por pagar')
    fecha_modificacion = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('idElementoPresupuesto','nombre_usuario')

    def __str__(self):
        return '{0}, {1} , {2}'.format(self.idElementoPresupuesto,self.nombre_usuario,self.estado)

class CosasPorVer(models.Model):
    idViaje = models.ForeignKey(Viaje, on_delete=models.CASCADE,null=False)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=10000, null=True, blank=True)
    fecha_a_visitar = models.DateField(null=True, blank=True)
    visto = models.BooleanField()
    fecha_visitado = models.DateField(null=True,blank=True)
    ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE,null=True)
    orden = models.IntegerField(default=100)
    def __str__(self):
        return '{0}, {1}'.format(self.id,self.idViaje)

    class Meta:
       ordering = ['visto','fecha_a_visitar']

class Foto(models.Model):
    nota = models.DecimalField(max_digits=3,decimal_places=2,default=0)
    num_valoraciones = models.IntegerField(default=0)
    nombre_usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre_ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE,null=True)
    idViaje = models.ForeignKey(Viaje, on_delete=models.CASCADE,blank = True,null=True)
    monumento = models.CharField(max_length=200)
    imagen = models.ImageField()

    def __str__(self):
        return '{0}'.format(self.monumento)

class PuntuacionFoto(models.Model):
    foto = models.ForeignKey(Foto, on_delete=models.CASCADE)
    puntuacion = models.DecimalField(max_digits=3,decimal_places=2,default=0)
    nombre_usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return '{0}'.format(self.foto)
