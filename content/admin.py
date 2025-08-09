from django.contrib import admin
from .models import Content, ContentReport
# Register your models here.

admin.site.register(Content)

@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ('content', 'reporter', 'reason', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'reason')
    search_fields = ('content__name', 'reporter__username')
