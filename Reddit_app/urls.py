#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 13:00:32 2021

@author: grace
"""

from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView


urlpatterns = [
    path('', views.intro_page, name='intro_page'),
    path('dashboard/', views.dashboard_view, name='dashboard_view'),  # change this
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


