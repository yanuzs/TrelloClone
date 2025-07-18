from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create-project/', views.create_project_view, name='create_project'),
    path('project/<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('project/<int:project_id>/edit/', views.edit_project_view, name='edit_project'),
    path('project/<int:project_id>/comment/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),
    path('project/<int:project_id>/comment/<int:comment_id>/edit/', views.edit_comment_view, name='edit_comment'),
    path('project/<int:project_id>/column/<int:column_id>/add-task/', views.add_task_view, name='add_task'),
    path('project/<int:project_id>/task/<int:task_id>/edit/', views.edit_task_view, name='edit_task'),
    path('project/<int:project_id>/task/<int:task_id>/delete/', views.delete_task_view, name='delete_task'),
    path('project/<int:project_id>/move-task/', views.move_task_view, name='move_task'),
    path('', views.login_view, name='home'), 
]
