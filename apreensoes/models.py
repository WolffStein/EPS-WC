from __future__ import annotations

from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def _build_unique_slug(model: type[models.Model], value: str, *, pk: int | None = None) -> str:
    base_slug = slugify(value)[:60] or "categoria"
    slug = base_slug
    counter = 2

    while model.objects.filter(slug=slug).exclude(pk=pk).exists():
        suffix = f"-{counter}"
        slug = f"{base_slug[: 60 - len(suffix)]}{suffix}"
        counter += 1

    return slug


def _build_unique_key(category_id: int, value: str, *, pk: int | None = None) -> str:
    base_key = slugify(value).replace("-", "_")[:50] or "campo"
    key = base_key
    counter = 2

    while CategoryField.objects.filter(category_id=category_id, key=key).exclude(pk=pk).exists():
        suffix = f"_{counter}"
        key = f"{base_key[: 50 - len(suffix)]}{suffix}"
        counter += 1

    return key


class Operation(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planejada", "Planejada"
        IN_PROGRESS = "em_andamento", "Em andamento"
        CLOSED = "encerrada", "Encerrada"

    codigo = models.CharField("codigo", max_length=30, unique=True)
    nome = models.CharField("nome da operacao", max_length=120)
    departamento = models.CharField(max_length=120)
    responsavel = models.CharField("chefe responsavel", max_length=120)
    data_operacao = models.DateField("data da operacao")
    horario_previsto = models.TimeField("horario previsto", blank=True, null=True)
    local_apreensao = models.CharField("local da apreensao", max_length=255)
    cidade_uf = models.CharField("cidade / UF", max_length=120, blank=True)
    suspeito_nome = models.CharField("suspeito / alvo", max_length=120)
    suspeito_documento = models.CharField("documento do suspeito", max_length=40, blank=True)
    suspeito_endereco = models.CharField("endereco do suspeito", max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    observacoes = models.TextField(blank=True)
    encerrada_em = models.DateTimeField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-data_operacao", "-criado_em")
        verbose_name = "operacao"
        verbose_name_plural = "operacoes"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"

    @property
    def total_itens(self) -> int:
        return self.items.count()

    @property
    def total_integrantes(self) -> int:
        return self.team_members.count()

    def start(self) -> None:
        if self.status == self.Status.PLANNED:
            self.status = self.Status.IN_PROGRESS
            self.save(update_fields=["status", "atualizado_em"])

    def close(self) -> None:
        self.status = self.Status.CLOSED
        if not self.encerrada_em:
            self.encerrada_em = timezone.now()
        self.save(update_fields=["status", "encerrada_em", "atualizado_em"])


class TeamMember(models.Model):
    operation = models.ForeignKey(
        Operation,
        on_delete=models.CASCADE,
        related_name="team_members",
    )
    nome = models.CharField(max_length=120)
    cargo = models.CharField(max_length=80)
    matricula = models.CharField(max_length=30, blank=True)
    contato = models.CharField(max_length=60, blank=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "integrante da equipe"
        verbose_name_plural = "integrantes da equipe"

    def __str__(self) -> str:
        return f"{self.nome} ({self.cargo})"


class EvidenceCategory(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    descricao = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = _build_unique_slug(EvidenceCategory, self.nome, pk=self.pk)
        super().save(*args, **kwargs)


class CategoryField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = "text", "Texto curto"
        TEXTAREA = "textarea", "Texto longo"
        INTEGER = "integer", "Numero inteiro"
        DECIMAL = "decimal", "Numero decimal"
        DATE = "date", "Data"
        BOOLEAN = "boolean", "Sim / Nao"

    category = models.ForeignKey(
        EvidenceCategory,
        on_delete=models.CASCADE,
        related_name="field_definitions",
    )
    label = models.CharField("rotulo", max_length=80)
    key = models.CharField(max_length=50, blank=True)
    field_type = models.CharField(
        "tipo do campo",
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT,
    )
    required = models.BooleanField("obrigatorio", default=False)
    help_text = models.CharField("ajuda", max_length=160, blank=True)
    placeholder = models.CharField(max_length=120, blank=True)
    sort_order = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        ordering = ("sort_order", "label")
        constraints = [
            models.UniqueConstraint(
                fields=["category", "key"],
                name="unique_category_key",
            ),
        ]
        verbose_name = "campo da categoria"
        verbose_name_plural = "campos da categoria"

    def __str__(self) -> str:
        return f"{self.category.nome}: {self.label}"

    def save(self, *args, **kwargs) -> None:
        if not self.key:
            self.key = _build_unique_key(self.category_id, self.label, pk=self.pk)
        super().save(*args, **kwargs)


class SeizedItem(models.Model):
    IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif"]
    SCENE_TYPE_LABELS = {
        "single_item": "Item unico",
        "repeated_items": "Multiplos itens semelhantes",
        "mixed_scene": "Cena mista",
        "uncertain": "Cena incerta",
    }

    operation = models.ForeignKey(
        Operation,
        on_delete=models.CASCADE,
        related_name="items",
    )
    category = models.ForeignKey(
        EvidenceCategory,
        on_delete=models.PROTECT,
        related_name="items",
    )
    titulo = models.CharField("item apreendido", max_length=120)
    quantidade = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    descricao = models.TextField(blank=True)
    evidence_image = models.FileField(
        "imagem do item",
        upload_to="apreensoes/imagens/",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
    )
    local_encontrado = models.CharField("local encontrado", max_length=255, blank=True)
    estado = models.CharField("estado / condicao", max_length=80, blank=True)
    extra_data = models.JSONField(default=dict, blank=True)
    ai_analysis = models.JSONField(default=dict, blank=True)
    ai_analysis_provider = models.CharField(max_length=40, blank=True)
    ai_analysis_model = models.CharField(max_length=80, blank=True)
    ai_last_analyzed_at = models.DateTimeField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "item apreendido"
        verbose_name_plural = "itens apreendidos"

    def __str__(self) -> str:
        return self.titulo

    @property
    def extra_field_items(self) -> list[dict[str, str]]:
        labels = {
            field_definition.key: field_definition.label
            for field_definition in self.category.field_definitions.all()
        }
        formatted: list[dict[str, str]] = []

        for key, value in self.extra_data.items():
            if value in ("", None, []):
                continue

            rendered_value = "Sim" if value is True else "Nao" if value is False else str(value)
            formatted.append(
                {
                    "label": labels.get(key, key.replace("_", " ").title()),
                    "value": rendered_value,
                }
            )

        return formatted

    @property
    def has_ai_analysis(self) -> bool:
        return bool(self.ai_analysis)

    @property
    def ai_suggested_title(self) -> str:
        return str(self.ai_analysis.get("suggested_title", "")).strip()

    @property
    def ai_suggested_category(self) -> str:
        return str(self.ai_analysis.get("suggested_category", "")).strip()

    @property
    def ai_summary(self) -> str:
        return str(self.ai_analysis.get("summary", "")).strip()

    @property
    def ai_confidence(self) -> str:
        return str(self.ai_analysis.get("confidence", "")).strip()

    @property
    def ai_visible_attributes(self) -> list[dict[str, str]]:
        return list(self.ai_analysis.get("visible_attributes", []))

    @property
    def ai_officer_review_notes(self) -> list[str]:
        return list(self.ai_analysis.get("officer_review_notes", []))

    @property
    def ai_missing_information(self) -> list[str]:
        return list(self.ai_analysis.get("missing_information", []))

    @property
    def ai_field_suggestions(self) -> list[dict[str, str]]:
        return list(self.ai_analysis.get("field_suggestions", []))

    @property
    def ai_quantity_hint(self) -> int | None:
        value = self.ai_analysis.get("suggested_quantity")
        return value if isinstance(value, int) and value > 0 else None

    @property
    def ai_category_slug(self) -> str:
        return str(self.ai_analysis.get("suggested_category_slug", "")).strip()

    @property
    def ai_should_create_multiple_records(self) -> bool:
        return bool(self.ai_analysis.get("should_create_multiple_records", False))

    @property
    def ai_scene_type(self) -> str:
        return str(self.ai_analysis.get("scene_type", "")).strip()

    @property
    def ai_scene_type_display(self) -> str:
        if not self.ai_scene_type:
            return ""
        return self.SCENE_TYPE_LABELS.get(
            self.ai_scene_type,
            self.ai_scene_type.replace("_", " ").strip().title(),
        )

    @property
    def ai_detected_items(self) -> list[dict[str, object]]:
        return list(self.ai_analysis.get("detected_items", []))
