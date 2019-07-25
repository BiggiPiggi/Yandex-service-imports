from django.urls import path

from . import views

urlpatterns = [
    path('', views.imports, name='imports'),
    path('/<int:import_id>/citizens/<int:citizen_id>', views.imports_change, name='imports_change'),
    path('/<int:import_id>/citizens', views.imports_all, name='imports_all'),
    path('/<int:import_id>/citizens/birthdays', views.imports_birthdays, name='imports_birthdays'),
    path('/<int:import_id>/towns/stat/percentile/age', views.imports_percentile, name='imports_percentile'),
]