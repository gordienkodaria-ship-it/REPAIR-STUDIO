
from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    dashboard_redirect,
    admin_dashboard,
    register,
    repair_detail,
    change_repair_status,
    add_repair_comment,
    create_repair_request,
    edit_repair_request,
    delete_repair_request,
    home,
    edit_profile,
    edit_service,
    delete_service,
    edit_part,
    delete_part,
    add_part_usage,
    statistics,
)


urlpatterns = [
    # Главная страница
    path('', home, name='home'),

    # Личный кабинет
    path('dashboard/', dashboard_redirect, name='dashboard'),

    # Авторизация
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='workshop/login.html'
        ),
        name='login'
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),
    path('register/', register, name='register'),

    # Профиль
    path('profile/', edit_profile, name='edit_profile'),

    # Заявки
    path(
        'repairs/<int:repair_id>/',
        repair_detail,
        name='repair_detail'
    ),
    path(
        'repairs/<int:repair_id>/change-status/',
        change_repair_status,
        name='change_repair_status'
    ),
    path(
        'repairs/<int:repair_id>/add-comment/',
        add_repair_comment,
        name='add_repair_comment'
    ),
    path(
        'repairs/create/',
        create_repair_request,
        name='create_repair_request'
    ),
    path(
        'repairs/<int:repair_id>/edit/',
        edit_repair_request,
        name='edit_repair_request'
    ),
    path(
        'repairs/<int:repair_id>/delete/',
        delete_repair_request,
        name='delete_repair_request'
    ),

    # Административная панель
    path(
        'admin-dashboard/',
        admin_dashboard,
        name='admin_dashboard'
    ),

    # Управление услугами
    path(
        'admin-dashboard/services/<int:service_id>/edit/',
        edit_service,
        name='edit_service'
    ),
    path(
        'admin-dashboard/services/<int:service_id>/delete/',
        delete_service,
        name='delete_service'
    ),

    # Управление запчастями
    path(
        'admin-dashboard/parts/<int:part_id>/edit/',
        edit_part,
        name='edit_part'
    ),
    path(
        'admin-dashboard/parts/<int:part_id>/delete/',
        delete_part,
        name='delete_part'
    ),

    path(
        'repairs/<int:repair_id>/add-part/',
        add_part_usage,
        name='add_part_usage'
    ),

    path(
        'statistics/',
        statistics,
        name='statistics'
    ),
]
