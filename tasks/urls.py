from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CustomLoginView
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Authentication
    path('login/', CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),

    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # Dashboard & Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reminders/', views.reminders, name='reminders'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Task Management
    path('tasks/', views.task_list, name='task_list'),
    path('task/new/', views.task_create, name='task_create'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/<int:pk>/edit/', views.task_update, name='task_update'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete'),

    # Workspace
    path('workspace/<int:workspace_id>/dashboard/', views.workspace_dashboard, name='workspace_dashboard'),
    path('invite/<int:workspace_id>/', views.invite_user, name='invite_user'),
    path('accept-invite/<str:token>/', views.accept_invite, name='accept_invite'),
    path('workspace/create/', views.create_workspace, name='create_workspace'),
    path('post-login/', views.post_login_redirect, name='post_login_redirect'),
    path('workspace/<int:workspace_id>/task/create/', views.create_workspace_task, name='create_workspace_task'),
    path('update-task-status/', views.update_task_status, name='update_task_status'),



]
