
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import path

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Vocation, LeaveRecord, Sales,Course

#admin.site.register(InvoiceRecod)
admin.site.register(Sales)
@admin.register(Vocation, LeaveRecord)
class ViewAdmin(ImportExportModelAdmin):  #############admin.ModelAdmin:paramétre aprés import_export
    pass



# core/admin.py


class CourseAdmin(admin.ModelAdmin):
    fields = ['imdb_id', 'genres', 'original_title', 'overview', 'watched']
    list_display = ('original_title', 'genres', 'release_date', 'watched')
    search_fields = ['original_title', 'overview']


admin.site.register(Course, CourseAdmin)
