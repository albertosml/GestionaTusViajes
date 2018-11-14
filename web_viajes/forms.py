import datetime

from django import forms
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.views import generic
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy

from .models import  Viaje, Ciudad, Valoracion, EntradaForo, Foto, ElementoPresupuesto, CosasPorVer, User

class AnadirViajeM(forms.ModelForm):
    class Meta:
        model = Viaje
        exclude =['usuarios','ciudades','coste_total','usuario_creador']
        fields = '__all__'
        widgets = { 'nombre': forms.TextInput(attrs={'style': 'border-color: #17a2b8;'}),
                    'fecha_inicio': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: #17a2b8;'}),
                    'fecha_fin': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: #17a2b8;'}),
                    'num_personas': forms.NumberInput(attrs={'min': 0 ,'style': 'border-color: #17a2b8;'}), }

    def clean(self):
        cleaned_data = super(AnadirViajeM, self).clean()
        fecha_i = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if fecha_i > fecha_fin :
            raise forms.ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin")

        return cleaned_data
 
    
class AnadirCiudad(forms.ModelForm):
    class Meta:
        model = Ciudad
        fields = ['nombre_ciudad','nombre_pais']
        widgets = {'nombre_ciudad': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'nombre_pais': forms.Select(attrs={'style': 'border-color: orange;'}),}

    def clean_nombre_ciudad(self):
        ciudad = self.cleaned_data["nombre_ciudad"]
        return ciudad


class AnadirValoracion(forms.ModelForm):
    class Meta:
        model = Valoracion
        fields = ['comentario','lo_mejor','lo_peor']
        widgets = {'comentario': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                   'lo_mejor': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                   'lo_peor': forms.TextInput(attrs={'style': 'border-color: orange;'}),}
 

class AnadirEntrada(forms.ModelForm):
    class Meta:
        model = EntradaForo
        fields = ['descripcion']
        widgets = {'descripcion': forms.TextInput(attrs={'style': 'border-color: orange;'}),}


class AnadirFoto(forms.ModelForm):
    class Meta:
        model = Foto
        fields = ['imagen','monumento']
        help_texts = { 'monumento': 'Debe contener 200 caracteres como máximo', }
        widgets = {'monumento': forms.TextInput(attrs={'style': 'border-color: orange;','class':'form-control'}),
                   'imagen': forms.FileInput(attrs={'accept':'image/*'}),}


class AnadirFotoViaje(forms.Form):
    imagen = forms.ImageField(widget=forms.FileInput(attrs={'accept':'image/*'}))
    monumento = forms.CharField(help_text="Introduzca un monumento de la ciudad",widget=forms.TextInput(attrs={'style': 'border-color: orange;','class':'form-control'}))
    nombre_ciudad = forms.ModelChoiceField(queryset=Ciudad.objects.all(),widget=forms.Select(attrs={'style': 'border-color: orange;','class':'form-control'}))

    def __init__(self, *args, **kwargs):
        idViaje = kwargs.pop('pk',None)
        super(AnadirFotoViaje, self).__init__(*args, **kwargs)

        if idViaje:
            viaje = Viaje.objects.get(id=idViaje)
            self.fields['nombre_ciudad'].queryset = viaje.ciudades.all()

class AnadirElemento(forms.ModelForm):
    class Meta:
        model = ElementoPresupuesto
        fields = '__all__'
        exclude = ['idViaje','usuario_paga']
        widgets = { 'concepto': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'inicio': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}),
                    'fin': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}), 
                    'usuario_paga': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'precio': forms.NumberInput(attrs={'min': 0 ,'style': 'border-color: orange;'}), 
                    'tipo': forms.Select(attrs={'style': 'border-color: orange;'}),}

    def clean(self):
        cleaned_data = super(AnadirElemento, self).clean()
        fecha_i = cleaned_data.get("inicio")
        fecha_fin = cleaned_data.get("fin")
        if fecha_i and fecha_fin is not None:
            if fecha_i > fecha_fin :
                raise forms.ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin")

        return cleaned_data

class AnadirCosaQueVer(forms.ModelForm):
    class Meta:
        model = CosasPorVer
        fields = '__all__'
        exclude = ['idViaje','ciudad']
        widgets = { 'descripcion': forms.Textarea(attrs={'style': 'border-color: #17a2b8;'}),
                    'fecha_a_visitar': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}),
                    'fecha_visitado': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}), 
                    'nombre': forms.TextInput(attrs={'style': 'border-color: orange;'}), }

class EditarCosaForm(forms.ModelForm):
    class Meta:
        model = CosasPorVer
        fields = ['nombre','descripcion','fecha_a_visitar','fecha_visitado','orden','visto']
        widgets = { 'descripcion': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'fecha_a_visitar': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}),
                    'fecha_visitado': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}), 
                    'nombre': forms.TextInput(attrs={'style': 'border-color: orange;'}), 
                    'visto': forms.CheckboxInput(attrs={'style': 'border-color: orange;'})}

class EditarCosaViaje(UpdateView):
    model = CosasPorVer
    template_name = 'cosasporver_form.html'
    form_class = EditarCosaForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return redirect('viaje',self.object.idViaje.pk)

class CiudadListView(generic.ListView):
    model = Ciudad
    template_name = 'index.html'
    paginate_by = 2

    def get_queryset(self):
        return Ciudad.objects.filter(aceptada=True)

class AnadirUsuario(forms.ModelForm):
    repeat_password = forms.CharField(widget=forms.TextInput(attrs={'type':'password','style': 'border-color: orange'}))

    class Meta:
        model = User
        fields = ['username','first_name','last_name','email','password']
        widgets = { 'username': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'first_name': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'last_name': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'email': forms.EmailInput(attrs={'type':'email','style': 'border-color: orange;'}),
                    'password': forms.TextInput(attrs={'type':'password','style': 'border-color: orange;'}), }
        help_texts = { 'password': 'Debe contener al menos 8 caracteres', }

    def clean(self):
        cleaned_data = super(AnadirUsuario, self).clean()
        contrasenia = cleaned_data.get("password")
        contrasenia_rep = cleaned_data.get("repeat_password")

        if contrasenia != contrasenia_rep :
            raise forms.ValidationError("Las contraseñas no son iguales")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(AnadirUsuario, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

class UsuarioUpdate(forms.ModelForm):
    repeat_password = forms.CharField(required=False,widget=forms.TextInput(attrs={'type':'password','style': 'border-color: orange'}))

    class Meta:
        model = User
        fields = ['first_name','last_name','email','password']
        widgets = { 'first_name': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'last_name': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'email': forms.EmailInput(attrs={'type':'email','style': 'border-color: orange;'}),
                    'password': forms.TextInput(attrs={'type':'password','style': 'border-color: orange;'}), }
        help_texts = { 'password': 'Debe contener al menos 8 caracteres', }

    def clean(self):
        cleaned_data = super(UsuarioUpdate, self).clean()
        contrasenia = cleaned_data.get("password")
        contrasenia_rep = cleaned_data.get("repeat_password")

        if contrasenia != contrasenia_rep :
            raise forms.ValidationError("Las contraseñas no son iguales")

        return cleaned_data

class TravelForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = ['nombre','fecha_inicio','fecha_fin','coste_total','planificacion','num_personas']
        widgets = { 'nombre': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'fecha_inicio': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}),
                    'fecha_fin': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}), 
                    'coste_total': forms.NumberInput(attrs={'min': 0 ,'style': 'border-color: orange;'}), }

    def clean(self):
        cleaned_data = super(TravelForm, self).clean()
        fecha_i = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if fecha_i > fecha_fin :
            raise forms.ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin")

        return cleaned_data

class ViajeUpdate(UpdateView):
    model = Viaje
    form_class = TravelForm
    template_name = 'editar_viaje.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return JsonResponse({'pk' : self.object.pk})

class FotoDelete(DeleteView):
    model = Foto
    template_name = 'eliminar_foto.html'
    success_url = reverse_lazy('inicio')

class CosaDelete(DeleteView):
    model = CosasPorVer
    template_name = 'eliminar_cosaver.html'

    def get_success_url(self):
        return reverse_lazy('viaje',args=[self.object.idViaje.pk])

class PresupuestoDelete(DeleteView):
    model = ElementoPresupuesto
    template_name = 'eliminar_elementopresupuesto.html'

    def get_success_url(self):
        return reverse_lazy('viaje',args=[self.object.idViaje.pk])

class ViajeDelete(DeleteView):
    model = Viaje
    template_name = 'eliminar_viaje.html'
    success_url = reverse_lazy('mis_viajes')

class EditarElementoForm(forms.ModelForm):
    class Meta:
        model = ElementoPresupuesto
        fields = '__all__'
        exclude = ['idViaje']
        widgets = { 'precio': forms.NumberInput(attrs={'min': 0 ,'style': 'border-color: orange;'}),
                    'concepto': forms.TextInput(attrs={'style': 'border-color: orange;'}),
                    'inicio': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}),
                    'fin': forms.DateInput(format = '%Y-%m-%d',attrs={'type': 'date','style': 'border-color: orange;'}), 
                    'nombre': forms.TextInput(attrs={'style': 'border-color: orange;'}), 
                    'usuario_paga': forms.TextInput(attrs={'style': 'border-color: orange;'}), 
                    'tipo': forms.Select(attrs={'style': 'border-color: orange;'}),}

class EditarElementoViaje(UpdateView):
    model = ElementoPresupuesto
    template_name = 'elementopresupuesto_form.html'
    form_class = EditarElementoForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        return redirect('viaje',self.object.idViaje.pk)