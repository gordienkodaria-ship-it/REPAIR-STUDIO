from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    Service,
    RepairRequest,
    StatusHistory,
    RepairComment,
    Part,
    PartUsage,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'role',
        'phone',
        'is_active',
    )

    list_filter = (
        'role',
        'is_active',
        'is_staff',
    )

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
        'phone',
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone'),
        }),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'price',
        'is_active',
        'created_at',
    )

    list_filter = ('is_active',)

    search_fields = (
        'name',
        'description',
    )

    ordering = ('name',)


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'master',
        'device_type',
        'service',
        'status',
        'created_at',
    )

    list_filter = ('status', 'created_at')

    search_fields = (
        'customer__username',
        'customer__first_name',
        'customer__last_name',
        'device_type',
        'description',
    )

    ordering = ('-created_at',)


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'repair',
        'old_status',
        'new_status',
        'changed_by',
        'created_at',
    )

    list_filter = ('new_status', 'created_at')

    search_fields = (
        'repair__device_type',
        'comment',
        'changed_by__username',
    )

    ordering = ('-created_at',)


@admin.register(RepairComment)
class RepairCommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'repair',
        'author',
        'text',
        'created_at',
    )

    search_fields = (
        'text',
        'author__username',
        'repair__device_type',
    )

    ordering = ('-created_at',)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'quantity',
        'min_quantity',
        'unit_price',
    )

    search_fields = (
        'name',
        'description',
    )

    ordering = ('name',)


@admin.register(PartUsage)
class PartUsageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'repair',
        'part',
        'quantity',
        'unit_price',
        'used_by',
        'created_at',
    )

    search_fields = (
        'part__name',
        'repair__device_type',
        'used_by__username',
    )

    ordering = ('-created_at',)