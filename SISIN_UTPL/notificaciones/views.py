from django.shortcuts import render

# Create your views here.

def notificaciones(request):
    return render(request, 'asesora/notificaciones.html')