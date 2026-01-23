<<<<<<< Updated upstream
"""
URL configuration for SISIN_UTPL project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path("siniestros/", include("siniestros.urls")),
    path("aseguradora/", include("aseguradora.urls")),
    path("polizas/", include("polizas.urls")),
    path('', RedirectView.as_view(url='/polizas/polizas/')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
=======
"""
URL configuration for SISIN_UTPL project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.views.generic import RedirectView
from usuarios.views import logout_then_home


urlpatterns = [
    path('admin/', admin.site.urls),
    # Rutas estándar de autenticación (login, logout, password change, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    # Shortcut logout route that redirects to site root
    path('logout/', logout_then_home),
    path('', include('usuarios.urls')),
    path("gerencia/", include("gerencia.urls")),
    path("siniestros/", include(("siniestros.urls", "siniestros"), namespace="siniestros")),
    path("aseguradora/", include("aseguradora.urls")),
    path("polizas/", include(("polizas.urls", "polizas"), namespace="polizas")),
    path("notificaciones/", include(("notificaciones.urls", "notificaciones"), namespace="notificaciones")),
    # Redirige la raíz al dashboard de la asesora
    path('dashboard/', RedirectView.as_view(url='/siniestros/dashboard/', permanent=False), name='dashboard_redirect'),
]
>>>>>>> Stashed changes
