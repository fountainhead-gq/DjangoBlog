from django.contrib import admin
from photos.models import Photo


class PhotoAdmin(admin.ModelAdmin):
    # prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'width', 'uploader', 'date_upload')
    search_fields = ('title', )

admin.site.register(Photo, PhotoAdmin)
