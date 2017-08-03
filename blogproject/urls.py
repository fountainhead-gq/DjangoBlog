"""blogproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.conf.urls import include, url
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from blog.views import PostViewSet, AuthorViewSet, CategoryViewSet, TagViewSet
from django.conf.urls import (handler400, handler403, handler404, handler500)
from rest_framework_swagger.views import get_swagger_view

handler400 = 'blog.views.handler400'
handler403 = 'blog.views.handler403'
handler404 = 'blog.views.handler404'
handler500 = 'blog.views.handler500'

router = DefaultRouter()
router.register(r'posts', PostViewSet, base_name='posts')
# router.register(r'authors', AuthorViewSet, base_name='authors')
router.register(r'category', CategoryViewSet, base_name='category')
router.register(r'tags', TagViewSet)

schema_view = get_swagger_view(title='API')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^photos/', include('photos.urls', namespace='photos')),
    url(r'^', include('blog.urls')),
    url(r'^api/', include(router.urls, namespace='api'), name='api'),
    url(r'^docs/', schema_view),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
