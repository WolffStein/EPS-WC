from django.contrib import admin

from .models import CategoryField, EvidenceCategory, Operation, SeizedItem, TeamMember


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0


class SeizedItemInline(admin.TabularInline):
    model = SeizedItem
    extra = 0


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nome",
        "departamento",
        "data_operacao",
        "status",
        "responsavel",
    )
    list_filter = ("status", "departamento", "data_operacao")
    search_fields = ("codigo", "nome", "suspeito_nome", "responsavel")
    inlines = [TeamMemberInline, SeizedItemInline]


class CategoryFieldInline(admin.TabularInline):
    model = CategoryField
    extra = 0


@admin.register(EvidenceCategory)
class EvidenceCategoryAdmin(admin.ModelAdmin):
    list_display = ("nome", "is_default", "active")
    list_filter = ("is_default", "active")
    search_fields = ("nome",)
    inlines = [CategoryFieldInline]


@admin.register(SeizedItem)
class SeizedItemAdmin(admin.ModelAdmin):
    list_display = ("titulo", "category", "operation", "quantidade", "criado_em")
    list_filter = ("category",)
    search_fields = ("titulo", "operation__codigo", "operation__nome")
