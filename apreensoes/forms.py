from __future__ import annotations

from datetime import date
from decimal import Decimal

from django import forms

from .models import CategoryField, EvidenceCategory, Operation, SeizedItem, TeamMember


class DateInput(forms.DateInput):
    input_type = "date"


class TimeInput(forms.TimeInput):
    input_type = "time"


class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = [
            "codigo",
            "nome",
            "departamento",
            "responsavel",
            "data_operacao",
            "horario_previsto",
            "local_apreensao",
            "cidade_uf",
            "suspeito_nome",
            "suspeito_documento",
            "suspeito_endereco",
            "observacoes",
        ]
        widgets = {
            "data_operacao": DateInput(),
            "horario_previsto": TimeInput(),
            "observacoes": forms.Textarea(attrs={"rows": 4}),
        }


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ["nome", "cargo", "matricula", "contato", "observacoes"]
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class EvidenceCategoryForm(forms.ModelForm):
    class Meta:
        model = EvidenceCategory
        fields = ["nome", "descricao", "active"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4}),
        }


class CategoryFieldForm(forms.ModelForm):
    class Meta:
        model = CategoryField
        fields = [
            "label",
            "field_type",
            "required",
            "help_text",
            "placeholder",
            "sort_order",
        ]


class SeizedItemForm(forms.ModelForm):
    DYNAMIC_PREFIX = "campo_"

    class Meta:
        model = SeizedItem
        fields = [
            "category",
            "titulo",
            "quantidade",
            "descricao",
            "local_encontrado",
            "estado",
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, operation: Operation | None = None, **kwargs):
        self.operation = operation
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = EvidenceCategory.objects.filter(active=True).order_by("nome")
        self.dynamic_field_map: dict[str, CategoryField] = {}

        selected_category = self._resolve_category()
        self.selected_category = selected_category

        if selected_category:
            for field_definition in selected_category.field_definitions.all():
                field_name = f"{self.DYNAMIC_PREFIX}{field_definition.key}"
                self.dynamic_field_map[field_name] = field_definition
                self.fields[field_name] = self._build_dynamic_form_field(field_definition)
                self.fields[field_name].initial = self._initial_extra_value(field_definition)

    def _resolve_category(self) -> EvidenceCategory | None:
        category_id = (
            self.data.get("category")
            or self.initial.get("category")
            or getattr(self.instance, "category_id", None)
        )

        if not category_id:
            return None

        try:
            return EvidenceCategory.objects.prefetch_related("field_definitions").get(pk=category_id)
        except EvidenceCategory.DoesNotExist:
            return None

    def _build_dynamic_form_field(self, field_definition: CategoryField) -> forms.Field:
        common_kwargs = {
            "label": field_definition.label,
            "required": field_definition.required,
            "help_text": field_definition.help_text,
        }

        if field_definition.field_type == CategoryField.FieldType.TEXTAREA:
            return forms.CharField(
                widget=forms.Textarea(
                    attrs={"rows": 3, "placeholder": field_definition.placeholder}
                ),
                **common_kwargs,
            )
        if field_definition.field_type == CategoryField.FieldType.INTEGER:
            return forms.IntegerField(
                widget=forms.NumberInput(attrs={"placeholder": field_definition.placeholder}),
                **common_kwargs,
            )
        if field_definition.field_type == CategoryField.FieldType.DECIMAL:
            return forms.DecimalField(
                decimal_places=2,
                widget=forms.NumberInput(
                    attrs={"step": "0.01", "placeholder": field_definition.placeholder}
                ),
                **common_kwargs,
            )
        if field_definition.field_type == CategoryField.FieldType.DATE:
            return forms.DateField(widget=DateInput(), **common_kwargs)
        if field_definition.field_type == CategoryField.FieldType.BOOLEAN:
            return forms.TypedChoiceField(
                choices=[
                    ("", "Selecione"),
                    ("true", "Sim"),
                    ("false", "Não"),
                ],
                coerce=lambda value: value == "true" if value else None,
                empty_value=None,
                **common_kwargs,
            )

        return forms.CharField(
            widget=forms.TextInput(attrs={"placeholder": field_definition.placeholder}),
            **common_kwargs,
        )

    def _initial_extra_value(self, field_definition: CategoryField):
        if not self.instance.pk:
            return None

        value = self.instance.extra_data.get(field_definition.key)
        if value in ("", None):
            return None
        if field_definition.field_type == CategoryField.FieldType.DATE and isinstance(value, str):
            return date.fromisoformat(value)
        if field_definition.field_type == CategoryField.FieldType.DECIMAL:
            return Decimal(str(value))

        return value

    def save(self, commit: bool = True) -> SeizedItem:
        instance = super().save(commit=False)

        if self.operation is not None:
            instance.operation = self.operation

        payload: dict[str, object] = {}
        for field_name, field_definition in self.dynamic_field_map.items():
            value = self.cleaned_data.get(field_name)
            if value in ("", None):
                continue
            if isinstance(value, date):
                payload[field_definition.key] = value.isoformat()
            elif isinstance(value, Decimal):
                payload[field_definition.key] = str(value)
            else:
                payload[field_definition.key] = value

        instance.extra_data = payload

        if commit:
            instance.save()

        return instance
