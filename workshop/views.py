
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import (
    RepairRequest,
    StatusHistory,
    RepairComment,
    Service,
    User,
    Part,
    PartUsage,
)

from .forms import (
    ClientRegistrationForm,
    RepairStatusForm,
    RepairCommentForm,
    RepairRequestForm,
    ProfileUpdateForm,
    AssignMasterForm,
    MasterCreationForm,
    ServiceForm,
    PartForm,
    PartUsageForm
)


# ==========================================
# ПРОВЕРКА ПРАВ ДОСТУПА
# ==========================================

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden(
                'Необходимо войти в систему.'
            )

        if request.user.role != User.Role.ADMIN:
            return HttpResponseForbidden(
                'У вас нет прав доступа.'
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def master_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden(
                'Необходимо войти в систему.'
            )

        if request.user.role != User.Role.MASTER:
            return HttpResponseForbidden(
                'У вас нет прав доступа.'
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def client_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden(
                'Необходимо войти в систему.'
            )

        if request.user.role != User.Role.CLIENT:
            return HttpResponseForbidden(
                'У вас нет прав доступа.'
            )

        return view_func(request, *args, **kwargs)

    return wrapper


# ==========================================
# ДОСТУП К ЗАЯВКАМ
# ==========================================

def get_repair_for_user(request, repair_id):
    if not request.user.is_authenticated:
        raise PermissionDenied

    if request.user.role == User.Role.ADMIN:
        requests = RepairRequest.objects.all()

    elif request.user.role == User.Role.MASTER:
        requests = RepairRequest.objects.filter(
            master=request.user
        )

    elif request.user.role == User.Role.CLIENT:
        requests = RepairRequest.objects.filter(
            customer=request.user
        )

    else:
        raise PermissionDenied

    return get_object_or_404(requests, pk=repair_id)


def repair_detail(request, repair_id):
    repair = get_repair_for_user(request, repair_id)

    status_history = StatusHistory.objects.filter(
        repair=repair
    ).order_by('-created_at')

    comments = RepairComment.objects.filter(
        repair=repair
    ).order_by('created_at')

    part_usages = PartUsage.objects.filter(
        repair=repair
    ).select_related('part')

    comment_form = RepairCommentForm()
    part_usage_form = PartUsageForm()

    return render(
        request,
        'workshop/repair_detail.html',
        {
            'repair': repair,
            'status_history': status_history,
            'comments': comments,
            'comment_form': comment_form,
            'part_usages': part_usages,
            'part_usage_form': part_usage_form,
        }
    )


# ==========================================
# ЛИЧНЫЙ КАБИНЕТ
# ==========================================

def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.role == User.Role.CLIENT:
        repair_requests = RepairRequest.objects.filter(
            customer=request.user
        ).order_by('-created_at')

    elif request.user.role == User.Role.MASTER:
        repair_requests = RepairRequest.objects.filter(
            master=request.user
        ).order_by('-created_at')

    elif request.user.role == User.Role.ADMIN:
        repair_requests = RepairRequest.objects.all().order_by(
            '-created_at'
        )

    else:
        return HttpResponseForbidden(
            'Неизвестная роль пользователя.'
        )

    return render(
        request,
        'workshop/dashboard.html',
        {'repair_requests': repair_requests}
    )


# ==========================================
# ПАНЕЛЬ АДМИНИСТРАТОРА
# ==========================================

@admin_required
def admin_dashboard(request):

    assign_form = AssignMasterForm()
    master_form = MasterCreationForm()
    service_form = ServiceForm()
    part_form = PartForm()

    if request.method == 'POST':

        action = request.POST.get('action')

        # Назначение мастера
        if action == 'assign_master':
            repair = get_object_or_404(
                RepairRequest,
                pk=request.POST.get('repair_id')
            )

            assign_form = AssignMasterForm(
                request.POST,
                instance=repair
            )

            if assign_form.is_valid():
                assign_form.save()
                return redirect('admin_dashboard')

        # Создание мастера
        elif action == 'create_master':
            master_form = MasterCreationForm(request.POST)

            if master_form.is_valid():
                master_form.save()
                return redirect('admin_dashboard')

        # Создание услуги
        elif action == 'create_service':
            service_form = ServiceForm(request.POST)

            if service_form.is_valid():
                service_form.save()
                return redirect('admin_dashboard')

        # Добавление запчасти
        elif action == 'create_part':
            part_form = PartForm(request.POST)

            if part_form.is_valid():
                part_form.save()
                return redirect('admin_dashboard')

    repairs = RepairRequest.objects.select_related(
        'customer',
        'master',
        'service'
    ).all().order_by('-created_at')

    masters = User.objects.filter(
        role=User.Role.MASTER
    ).order_by('username')

    clients = User.objects.filter(
        role=User.Role.CLIENT
    ).order_by('username')

    services = Service.objects.all().order_by('name')

    parts = Part.objects.all().order_by('name')

    low_stock_parts = Part.objects.filter(
        quantity__lte=Count('usages')
    ) if False else [
        part for part in parts
        if part.quantity <= part.min_quantity
    ]

    context = {
        # Статистика
        'repairs_count': RepairRequest.objects.count(),
        'new_repairs_count': RepairRequest.objects.filter(
            status=RepairRequest.Status.NEW
        ).count(),
        'clients_count': clients.count(),
        'masters_count': masters.count(),
        'services_count': services.count(),
        'parts_count': parts.count(),

        'income': RepairRequest.objects.filter(
            status__in=[
                RepairRequest.Status.COMPLETED,
                RepairRequest.Status.ISSUED,
            ]
        ).aggregate(total=Sum('work_cost'))['total'] or 0,

        # Данные
        'repairs': repairs,
        'masters': masters,
        'clients': clients,
        'services': services,
        'parts': parts,
        'low_stock_parts': low_stock_parts,

        # Формы
        'assign_form': assign_form,
        'master_form': master_form,
        'service_form': service_form,
        'part_form': part_form,
    }

    return render(
        request,
        'workshop/admin_dashboard.html',
        context
    )


# ==========================================
# СТАТИСТИКА
# ==========================================

@admin_required
def statistics(request):
    total_repairs = RepairRequest.objects.count()

    status_statistics = []

    for status_value, status_label in RepairRequest.Status.choices:
        count = RepairRequest.objects.filter(
            status=status_value
        ).count()

        percentage = (
            round(count / total_repairs * 100)
            if total_repairs else 0
        )

        status_statistics.append({
            'label': status_label,
            'count': count,
            'percentage': percentage,
        })

    completed_count = RepairRequest.objects.filter(
        status__in=[
            RepairRequest.Status.COMPLETED,
            RepairRequest.Status.ISSUED,
        ]
    ).count()

    cancelled_count = RepairRequest.objects.filter(
        status=RepairRequest.Status.CANCELLED
    ).count()

    active_count = total_repairs - completed_count - cancelled_count

    income = RepairRequest.objects.filter(
        status__in=[
            RepairRequest.Status.COMPLETED,
            RepairRequest.Status.ISSUED,
        ]
    ).aggregate(total=Sum('work_cost'))['total'] or 0

    context = {
        'total_repairs': total_repairs,
        'completed_count': completed_count,
        'active_count': active_count,
        'cancelled_count': cancelled_count,
        'income': income,
        'status_statistics': status_statistics,
    }

    return render(
        request,
        'workshop/statistics.html',
        context
    )



# ==========================================
# УПРАВЛЕНИЕ УСЛУГАМИ
# ==========================================

@admin_required
def edit_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)

    if request.method == 'POST':
        form = ServiceForm(
            request.POST,
            instance=service
        )

        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')

    else:
        form = ServiceForm(instance=service)

    return render(
        request,
        'workshop/service_form.html',
        {
            'form': form,
            'service': service,
        }
    )


@admin_required
def delete_service(request, service_id):
    if request.method != 'POST':
        return redirect('admin_dashboard')

    service = get_object_or_404(Service, pk=service_id)
    service.delete()

    return redirect('admin_dashboard')


# ==========================================
# УПРАВЛЕНИЕ ЗАПЧАСТЯМИ
# ==========================================

@admin_required
def edit_part(request, part_id):
    part = get_object_or_404(Part, pk=part_id)

    if request.method == 'POST':
        form = PartForm(
            request.POST,
            instance=part
        )

        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')

    else:
        form = PartForm(instance=part)

    return render(
        request,
        'workshop/part_form.html',
        {
            'form': form,
            'part': part,
        }
    )


@admin_required
def delete_part(request, part_id):
    if request.method != 'POST':
        return redirect('admin_dashboard')

    part = get_object_or_404(Part, pk=part_id)

    if part.usages.exists():
        return HttpResponseForbidden(
            'Нельзя удалить запчасть, которая уже использовалась.'
        )

    part.delete()

    return redirect('admin_dashboard')


# ==========================================
# РЕГИСТРАЦИЯ
# ==========================================

def register(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')

    else:
        form = ClientRegistrationForm()

    return render(
        request,
        'workshop/register.html',
        {'form': form}
    )


# ==========================================
# ИЗМЕНЕНИЕ СТАТУСА ЗАЯВКИ
# ==========================================


@master_required
def change_repair_status(request, repair_id):
    repair = get_repair_for_user(request, repair_id)

    if request.method == 'POST':
        old_status = repair.status

        form = RepairStatusForm(
            request.POST,
            instance=repair
        )

        if form.is_valid():
            updated_repair = form.save()

            if old_status != updated_repair.status:
                StatusHistory.objects.create(
                    repair=updated_repair,
                    old_status=old_status,
                    new_status=updated_repair.status,
                    changed_by=request.user,
                    comment='Статус заявки изменён'
                )

            return redirect(
                'repair_detail',
                repair_id=updated_repair.id
            )

    else:
        form = RepairStatusForm(instance=repair)

    return render(
        request,
        'workshop/change_repair_status.html',
        {
            'form': form,
            'repair': repair
        }
    )



# ==========================================
# КОММЕНТАРИИ
# ==========================================

def add_repair_comment(request, repair_id):
    repair = get_repair_for_user(request, repair_id)

    if request.method == 'POST':
        form = RepairCommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.repair = repair
            comment.author = request.user
            comment.save()

    return redirect(
        'repair_detail',
        repair_id=repair.id
    )


# ==========================================
# СОЗДАНИЕ ЗАЯВКИ
# ==========================================

@client_required
def create_repair_request(request):
    if request.method == 'POST':
        form = RepairRequestForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            repair = form.save(commit=False)
            repair.customer = request.user
            repair.status = RepairRequest.Status.NEW

            if repair.service:
                repair.work_cost = repair.service.price

            repair.save()

            return redirect(
                'repair_detail',
                repair_id=repair.id
            )

    else:
        form = RepairRequestForm()

    return render(
        request,
        'workshop/create_repair_request.html',
        {'form': form}
    )


# ==========================================
# РЕДАКТИРОВАНИЕ ЗАЯВКИ
# ==========================================

@client_required
def edit_repair_request(request, repair_id):
    repair = get_repair_for_user(request, repair_id)

    if repair.status != RepairRequest.Status.NEW:
        return HttpResponseForbidden(
            'Эту заявку уже нельзя редактировать.'
        )

    if request.method == 'POST':
        form = RepairRequestForm(
            request.POST,
            request.FILES,
            instance=repair
        )

        if form.is_valid():
            updated_repair = form.save(commit=False)

            if updated_repair.service:
                updated_repair.work_cost = updated_repair.service.price

            updated_repair.save()

            return redirect(
                'repair_detail',
                repair_id=updated_repair.id
            )

    else:
        form = RepairRequestForm(instance=repair)

    return render(
        request,
        'workshop/edit_repair_request.html',
        {
            'form': form,
            'repair': repair
        }
    )


# ==========================================
# УДАЛЕНИЕ ЗАЯВКИ
# ==========================================

@client_required
def delete_repair_request(request, repair_id):
    repair = get_repair_for_user(request, repair_id)

    if repair.status != RepairRequest.Status.NEW:
        return HttpResponseForbidden(
            'Эту заявку уже нельзя удалить.'
        )

    if request.method == 'POST':
        repair.delete()
        return redirect('dashboard')

    return redirect(
        'repair_detail',
        repair_id=repair.id
    )


# ==========================================
# ГЛАВНАЯ СТРАНИЦА
# ==========================================

def home(request):
    services = Service.objects.filter(is_active=True)

    return render(
        request,
        'workshop/home.html',
        {'services': services}
    )


# ==========================================
# ПРОФИЛЬ
# ==========================================

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            return redirect('edit_profile')

    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(
        request,
        'workshop/edit_profile.html',
        {'form': form}
    )



@master_required
def add_part_usage(request, repair_id):
    repair = get_repair_for_user(request, repair_id)

    if request.method == 'POST':
        form = PartUsageForm(request.POST)

        if form.is_valid():
            usage = form.save(commit=False)
            usage.repair = repair
            usage.used_by = request.user
            usage.unit_price = usage.part.unit_price

            try:
                usage.save()
                messages.success(request, 'Запчасть добавлена к заявке.')
            except ValidationError as error:
                messages.error(request, str(error))
        else:
            messages.error(request, 'Проверьте данные запчасти.')

    return redirect('repair_detail', repair_id=repair.id)