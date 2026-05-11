from __future__ import annotations

from datetime import date
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import CategoryField, EvidenceCategory, Operation, SeizedItem, TeamMember


class DateInput(forms.DateInput):
    input_type = "date"


class TimeInput(forms.TimeInput):
    input_type = "time"


class SignInForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "placeholder": "Digite seu usuario",
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Digite sua senha",
            }
        ),
    )


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
    use_required_attribute = False
    DEFAULT_TITLES = {
        "armas": "Arma apreendida",
        "drogas": "Droga apreendida",
        "municoes": "Municoes apreendidas",
        "veiculos": "Veiculo apreendido",
        "eletronicos": "Eletronico apreendido",
    }

    class Meta:
        model = SeizedItem
        fields = [
            "category",
            "titulo",
            "quantidade",
            "descricao",
            "evidence_image",
            "local_encontrado",
            "estado",
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4}),
            "evidence_image": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                    "capture": "environment",
                }
            ),
        }

    def __init__(self, *args, operation: Operation | None = None, **kwargs):
        self.operation = operation
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = EvidenceCategory.objects.filter(active=True).order_by("nome")
        self.fields["titulo"].required = False
        self.fields["quantidade"].required = False
        self.fields["titulo"].widget.attrs.update(
            {
                "placeholder": "Deixe em branco para a IA sugerir um titulo apos salvar.",
            }
        )
        self.fields["quantidade"].widget.attrs.update(
            {
                "placeholder": "1",
                "inputmode": "numeric",
            }
        )
        self.fields["descricao"].widget.attrs.update(
            {
                "placeholder": "Opcional na captura rapida. A IA tenta resumir a foto apos salvar.",
            }
        )
        self.fields["local_encontrado"].widget.attrs.update(
            {
                "placeholder": "Ex.: sala, porta-malas, quarto, gaveta",
            }
        )
        self.fields["estado"].widget.attrs.update(
            {
                "placeholder": "Ex.: integro, desmontado, embalado",
            }
        )
        self.dynamic_field_map: dict[str, CategoryField] = {}
        self.required_dynamic_field_names: set[str] = set()

        selected_category = self._resolve_category()
        self.selected_category = selected_category

        if selected_category:
            for field_definition in selected_category.field_definitions.all():
                field_name = f"{self.DYNAMIC_PREFIX}{field_definition.key}"
                self.dynamic_field_map[field_name] = field_definition
                self.fields[field_name] = self._build_dynamic_form_field(field_definition)
                self.fields[field_name].initial = self._initial_extra_value(field_definition)
                if field_definition.required:
                    self.required_dynamic_field_names.add(field_name)

            for field_name in self.dynamic_field_map:
                self.fields[field_name].required = False

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
                    ("false", "Nao"),
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

    def _allows_ai_assisted_completion(self) -> bool:
        uploaded_image = bool(self.files.get("evidence_image"))
        existing_image = bool(getattr(self.instance, "evidence_image", None))
        return uploaded_image or existing_image

    def _default_title_for_category(self) -> str:
        if self.selected_category:
            return self.DEFAULT_TITLES.get(
                self.selected_category.slug,
                f"{self.selected_category.nome.rstrip('s')} apreendido"
                if self.selected_category.nome
                else "Item apreendido",
            )
        return "Item apreendido"

    def clean(self):
        cleaned_data = super().clean()

        if self._allows_ai_assisted_completion():
            return cleaned_data

        for field_name in self.required_dynamic_field_names:
            value = cleaned_data.get(field_name)
            if value not in ("", None):
                continue

            label = self.fields[field_name].label
            self.add_error(
                field_name,
                f"{label} e obrigatorio quando o registro for salvo sem imagem para analise.",
            )

        return cleaned_data

    def save(self, commit: bool = True) -> SeizedItem:
        instance = super().save(commit=False)

        if self.operation is not None:
            instance.operation = self.operation

        if not str(instance.titulo).strip():
            instance.titulo = self._default_title_for_category()
        if not instance.quantidade:
            instance.quantidade = 1

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
