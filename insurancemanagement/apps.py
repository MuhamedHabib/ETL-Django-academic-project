# core/apps.py

from django.contrib.admin.apps import AdminConfig


class CustomAdminConfig(AdminConfig):
    default_site = 'insurancemanagement.admin.CustomAdminSite'
