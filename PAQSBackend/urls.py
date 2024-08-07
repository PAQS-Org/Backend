"""PAQSBackend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
import PAQSBackend.view_config as example_views


urlpatterns = [
    path('', include('entry.urls')),
    path('admin/', admin.site.urls),
    path('account/', include('accounts.urls')),
    path('payment/', include('payments.urls')),
    path('social/', include('social_auth.urls')),
    path("healthcheck/", example_views.health_check, name="health_check"),
    path("test-task/", example_views.test_task, name="test_task"),
] 
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

