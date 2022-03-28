
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import path

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Policy, PolicyRecord, Invoice, InvoiceRecod, Purchase

admin.site.register(InvoiceRecod)
admin.site.register(Purchase)
@admin.register(Policy,PolicyRecord,Invoice)
class ViewAdmin(ImportExportModelAdmin):  #############admin.ModelAdmin:paramétre aprés import_export
    pass



# core/admin.py


