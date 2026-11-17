from django.db import models, transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from decimal import Decimal

class User(AbstractUser):
    """Пользователь системы ремонтной мастерской."""

    class Role(models.TextChoices):
        CLIENT = 'client', 'Клиент'
        MASTER = 'master', 'Мастер'
        ADMIN = 'admin', 'Администратор'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
        verbose_name='Роль пользователя'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Номер телефона'
    )

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'


class Service(models.Model):
    """Услуги ремонтной мастерской."""

    name = models.CharField(
        max_length=150,
        verbose_name='Название услуги'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Стоимость'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Услуга активна'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'



class RepairRequest(models.Model):
    """Заявка клиента на ремонт техники."""

    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        ACCEPTED = 'accepted', 'Принята'
        DIAGNOSTICS = 'diagnostics', 'Диагностика'
        WAITING_PARTS = 'waiting_parts', 'Ожидание запчастей'
        IN_PROGRESS = 'in_progress', 'В ремонте'
        COMPLETED = 'completed', 'Готова к выдаче'
        ISSUED = 'issued', 'Выдана'
        CANCELLED = 'cancelled', 'Отменена'

    customer = models.ForeignKey(
        'workshop.User',
        on_delete=models.CASCADE,
        related_name='repair_requests',
        verbose_name='Клиент'
    )

    master = models.ForeignKey(
        'workshop.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_repairs',
        verbose_name='Мастер'
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests',
        verbose_name='Услуга'
    )

    device_type = models.CharField(
        max_length=100,
        verbose_name='Тип устройства'
    )

    description = models.TextField(
        verbose_name='Описание неисправности'
    )

    photo = models.ImageField(
        upload_to='repair_photos/',
        blank=True,
        null=True,
        verbose_name='Фотография устройства'
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Статус заявки'
    )

    work_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Стоимость ремонта'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    def __str__(self):
        return f'Заявка №{self.pk} — {self.device_type}'

    class Meta:
        verbose_name = 'Заявка на ремонт'
        verbose_name_plural = 'Заявки на ремонт'
        ordering = ['-created_at']



class StatusHistory(models.Model):
    """История изменения статусов заявок."""

    repair = models.ForeignKey(
        RepairRequest,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Заявка'
    )

    changed_by = models.ForeignKey(
        'workshop.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Кто изменил'
    )

    old_status = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Предыдущий статус'
    )

    new_status = models.CharField(
        max_length=30,
        choices=RepairRequest.Status.choices,
        verbose_name='Новый статус'
    )

    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата изменения'
    )

    class Meta:
        verbose_name = 'История статуса'
        verbose_name_plural = 'История статусов'
        ordering = ['-created_at']



class RepairComment(models.Model):
    """Комментарии к заявкам."""

    repair = models.ForeignKey(
        RepairRequest,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Заявка'
    )

    author = models.ForeignKey(
        'workshop.User',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    text = models.TextField(
        verbose_name='Текст комментария'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата комментария'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']



class Part(models.Model):
    """Запчасти на складе."""

    name = models.CharField(
        max_length=150,
        verbose_name='Название запчасти'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )

    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество на складе'
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за единицу'
    )

    min_quantity = models.PositiveIntegerField(
        default=2,
        verbose_name='Минимальный остаток'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Запчасть'
        verbose_name_plural = 'Запчасти'
        ordering = ['name']


class PartUsage(models.Model):
    """Использование запчастей при ремонте."""

    repair = models.ForeignKey(
        RepairRequest,
        on_delete=models.CASCADE,
        related_name='used_parts',
        verbose_name='Заявка'
    )

    part = models.ForeignKey(
        Part,
        on_delete=models.PROTECT,
        related_name='usages',
        verbose_name='Запчасть'
    )

    quantity = models.PositiveIntegerField(
        verbose_name='Количество'
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена на момент использования'
    )

    used_by = models.ForeignKey(
        'workshop.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Кто использовал'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата использования'
    )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                old_usage = PartUsage.objects.select_for_update().get(pk=self.pk)

                if old_usage.part_id != self.part_id:
                    raise ValidationError(
                        'Нельзя менять запчасть в уже созданной записи.'
                    )

                difference = self.quantity - old_usage.quantity
            else:
                difference = self.quantity

            if difference > 0:
                updated = Part.objects.filter(
                    pk=self.part_id,
                    quantity__gte=difference
                ).update(quantity=F('quantity') - difference)

                if updated == 0:
                    raise ValidationError(
                        'Недостаточно запчастей на складе.'
                    )

            elif difference < 0:
                Part.objects.filter(pk=self.part_id).update(
                    quantity=F('quantity') - difference
                )

            if not self.unit_price and self.part_id:
                self.unit_price = self.part.unit_price

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            Part.objects.filter(pk=self.part_id).update(
                quantity=F('quantity') + self.quantity
            )
            super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Использование запчасти'
        verbose_name_plural = 'Использование запчастей'        