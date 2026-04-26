from __future__ import annotations

import mimetypes
import os
from pathlib import Path

import httpx
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError

from .models import EvidenceCategory, SeizedItem


GEMINI_INLINE_IMAGE_LIMIT_BYTES = 18 * 1024 * 1024


class ImageAnalysisError(Exception):
    """Raised when AI image analysis cannot be completed."""


class VisibleAttribute(BaseModel):
    label: str = Field(description="Visible field name detected in the image.")
    value: str = Field(description="Observed value for the field.")


class FieldSuggestion(BaseModel):
    key: str = Field(description="Existing field key from the category configuration.")
    label: str = Field(description="Human-readable field name.")
    value: str = Field(description="Suggested value only when visually supported.")


class DetectedSceneItem(BaseModel):
    position_reference: str = Field(
        description="Short location cue such as esquerda, centro, direita, frente or fundo."
    )
    suggested_title: str = Field(description="Short title for the detected object group.")
    suggested_category: str = Field(
        description="Best-fit category name for this detected item or item group."
    )
    suggested_category_slug: str = Field(
        description="Slug or normalized category identifier for this detected item."
    )
    summary: str = Field(description="Short description of what is visible for this detected item.")
    suggested_quantity: int | None = Field(
        default=None,
        description="Visible quantity for the detected item or group when clear.",
    )
    should_be_separate_record: bool = Field(
        default=True,
        description="True when this should probably become its own inventory record.",
    )
    confidence: str = Field(description="Low, medium or high confidence.")


class ItemImageSuggestion(BaseModel):
    suggested_title: str = Field(description="Short suggested title for the seized item.")
    suggested_category: str = Field(
        description="Best-fit category suggestion based on visible evidence."
    )
    suggested_category_slug: str = Field(
        description="Slug or normalized category identifier that matches a category in the system."
    )
    summary: str = Field(description="Brief summary of what is visible in the image.")
    confidence: str = Field(description="Low, medium or high confidence.")
    suggested_quantity: int | None = Field(
        default=None,
        description="Suggested count of visible items when this is reasonably clear.",
    )
    visible_attributes: list[VisibleAttribute] = Field(default_factory=list)
    field_suggestions: list[FieldSuggestion] = Field(default_factory=list)
    officer_review_notes: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    scene_type: str = Field(
        description="single_item, repeated_items, mixed_scene or uncertain."
    )
    should_create_multiple_records: bool = Field(
        description="True when the photo likely contains more than one evidence record."
    )
    detected_items: list[DetectedSceneItem] = Field(default_factory=list)


def get_ai_provider_name() -> str:
    return "gemini"


def get_ai_vision_model() -> str:
    return os.getenv("GEMINI_VISION_MODEL", "gemini-2.5-flash")


def _build_field_guide(item: SeizedItem) -> str:
    pairs = []
    for field_definition in item.category.field_definitions.all():
        pairs.append(
            f"{field_definition.key}={field_definition.label} ({field_definition.get_field_type_display()})"
        )
    return "; ".join(pairs) or "Sem campos adicionais"


def _build_available_categories_guide() -> str:
    pairs = EvidenceCategory.objects.filter(active=True).values_list("nome", "slug")
    return "; ".join(f"{nome}={slug}" for nome, slug in pairs)


def _build_specialized_rules(item: SeizedItem) -> str:
    slug = item.category.slug

    if slug == "armas":
        return (
            "Se a imagem parecer uma arma, foque em sugerir apenas atributos visuais como tipo "
            "aparente da arma, marca, modelo, cor/acabamento, numero de serie visivel, calibre "
            "aparente e presencia de acessorios visiveis. Nunca invente calibre ou serial. "
            "Se houver mais de uma arma, municoes separadas ou outros itens como drogas na mesma "
            "foto, marque should_create_multiple_records como true, use scene_type='mixed_scene' "
            "ou 'repeated_items' e detalhe os grupos em detected_items. Para objetos longos ou "
            "equipamentos taticos sem confirmacao clara, nao afirme que sao arma de fogo; use "
            "descricoes conservadoras e destaque a incerteza."
        )

    if slug == "drogas":
        return (
            "Se a imagem parecer droga ou substancia entorpecente, foque em sugerir apenas "
            "apresentacao visivel, cor, tipo de embalagem, quantidade aparente de volumes, "
            "rotulagem visivel e unidade aparente quando estiver clara. Nao identifique substancia "
            "com certeza se a imagem nao permitir; use termos como 'aparenta ser' na descricao. "
            "Se houver armas, municoes ou mais de um conjunto distinto de evidencias, marque "
            "should_create_multiple_records como true e descreva cada grupo em detected_items."
        )

    if slug == "municoes":
        return (
            "Se a imagem parecer municao, cartucho ou estojo, foque em quantidade visivel, "
            "calibre aparente somente quando houver indicio visual suficiente, tipo de municao, "
            "marca visivel e acondicionamento. Se a foto tambem tiver armas ou drogas, marque "
            "should_create_multiple_records como true e detalhe os demais grupos em detected_items."
        )

    return (
        "Para outras categorias, sugira somente o que estiver visualmente sustentado na foto "
        "e que ajude o agente a preencher o formulario. Se a foto trouxer varios objetos que "
        "normalmente seriam cadastrados separadamente, use detected_items para orientar o desdobramento."
    )


def _build_prompt(item: SeizedItem) -> str:
    return (
        "Voce esta ajudando no preenchimento de um inventario de apreensao policial. "
        "Analise a imagem de forma conservadora. Nao invente numeros de serie, IMEI, placa, "
        "chassi, calibre, substancia ou qualquer informacao nao visivel. Sugira dados apenas "
        "quando houver evidencia visual clara. Se algo importante nao estiver visivel, liste em "
        "missing_information. Ignore logos institucionais, fundos de coletiva, balancas, mesas "
        "ou caixas ao fundo quando eles nao forem o objeto apreendido principal. "
        "Se a foto mostrar varios itens distintos que normalmente virariam registros separados "
        "no inventario, marque should_create_multiple_records=true, classifique a cena em "
        "scene_type e preencha detected_items com os grupos visiveis. "
        "Nos campos de topo, descreva apenas o item principal correspondente ao registro atual; "
        "se isso nao estiver claro, mantenha o topo conservador e use officer_review_notes para "
        "pedir desmembramento manual. "
        "Valores aceitos para scene_type: single_item, repeated_items, mixed_scene, uncertain. "
        f"Categoria atual selecionada no sistema: {item.category.nome}. "
        f"Campos configurados para esta categoria: {_build_field_guide(item)}. "
        f"Categorias disponiveis no sistema com seus slugs: {_build_available_categories_guide()}. "
        f"{_build_specialized_rules(item)} "
        "Use field_suggestions somente com chaves que existam na categoria atual. "
        "Responda em portugues com sugestoes curtas, objetivas e prontas para revisao humana."
    )


def _guess_mime_type(image_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(image_path.name)
    if mime_type and mime_type.startswith("image/"):
        return mime_type
    return "image/jpeg"


def _build_image_input(client: genai.Client, image_path: Path):
    if image_path.stat().st_size <= GEMINI_INLINE_IMAGE_LIMIT_BYTES:
        return types.Part.from_bytes(
            data=image_path.read_bytes(),
            mime_type=_guess_mime_type(image_path),
        )
    return client.files.upload(file=image_path)


def _map_gemini_error(exc: Exception) -> ImageAnalysisError:
    message = str(exc).lower()

    if "api key" in message or "unauthenticated" in message or "permission" in message:
        return ImageAnalysisError(
            "A chave da Gemini API parece invalida, nao autorizada ou indisponivel para este projeto."
        )

    if "quota" in message or "resource_exhausted" in message or "429" in message:
        return ImageAnalysisError(
            "A chave da Gemini API foi aceita, mas o projeto esta sem cota disponivel no momento."
        )

    if "mime" in message or "image" in message or "invalid" in message or "400" in message:
        return ImageAnalysisError(
            "A Gemini nao conseguiu processar essa imagem. Tente outra foto ou verifique o formato enviado."
        )

    return ImageAnalysisError(
        "Nao foi possivel concluir a analise na Gemini API agora. Tente novamente em instantes."
    )


def _has_meaningful_ai_value(value: object) -> bool:
    normalized = str(value).strip().lower()
    if not normalized:
        return False
    return normalized not in {
        "null",
        "none",
        "n/a",
        "na",
        "nao visivel",
        "não visível",
        "nao aplicavel",
        "não aplicável",
        "indeterminado",
        "desconhecido",
    }


def analyze_item_image(item: SeizedItem) -> dict[str, object]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ImageAnalysisError("Defina a variavel GEMINI_API_KEY para usar a analise de imagens.")

    if not item.evidence_image:
        raise ImageAnalysisError("O item precisa ter uma imagem enviada antes da analise.")

    image_path = Path(item.evidence_image.path)
    if not image_path.exists():
        raise ImageAnalysisError("A imagem do item nao foi encontrada no armazenamento local.")

    client = genai.Client(api_key=api_key)
    model = get_ai_vision_model()

    try:
        image_input = _build_image_input(client, image_path)
        response = client.models.generate_content(
            model=model,
            contents=[image_input, _build_prompt(item)],
            config={
                "response_mime_type": "application/json",
                "response_json_schema": ItemImageSuggestion.model_json_schema(),
            },
        )
    except errors.APIError as exc:
        raise _map_gemini_error(exc) from exc
    except httpx.HTTPError as exc:
        raise ImageAnalysisError(
            "Nao foi possivel conectar a Gemini API agora. Verifique sua rede e tente novamente."
        ) from exc
    except OSError as exc:
        raise ImageAnalysisError(
            "Nao foi possivel abrir a imagem do item para enviar a Gemini API."
        ) from exc

    if not response.text:
        raise ImageAnalysisError(
            "A Gemini API nao retornou um resultado estruturado para essa imagem. Tente outra foto."
        )

    try:
        return ItemImageSuggestion.model_validate_json(response.text).model_dump(mode="json")
    except ValidationError as exc:
        raise ImageAnalysisError(
            "A Gemini API respondeu, mas o conteudo nao veio no formato esperado pelo sistema."
        ) from exc


def apply_ai_suggestions(item: SeizedItem) -> list[str]:
    if not item.ai_analysis:
        raise ImageAnalysisError("Esse item ainda nao possui sugestoes de IA para aplicar.")

    applied: list[str] = []
    category_changed = False

    if item.category.slug == "outros" and item.ai_category_slug:
        suggested_category = EvidenceCategory.objects.filter(
            slug=item.ai_category_slug,
            active=True,
        ).first()
        if suggested_category:
            item.category = suggested_category
            applied.append("categoria")
            category_changed = True

    allow_primary_autofill = not item.ai_should_create_multiple_records

    if (
        allow_primary_autofill
        and item.ai_quantity_hint
        and item.quantidade == 1
        and item.ai_quantity_hint > 1
    ):
        item.quantidade = item.ai_quantity_hint
        applied.append("quantidade")

    suggested_title = item.ai_suggested_title
    if (
        allow_primary_autofill
        and suggested_title
        and item.titulo.strip().lower() in {"item", "objeto", "item apreendido"}
    ):
        item.titulo = suggested_title
        applied.append("titulo")

    if allow_primary_autofill and item.ai_summary and not item.descricao.strip():
        item.descricao = item.ai_summary
        applied.append("descricao")

    extra_data = dict(item.extra_data)
    for suggestion in item.ai_field_suggestions:
        key = str(suggestion.get("key", "")).strip()
        value = str(suggestion.get("value", "")).strip()
        if not key or not _has_meaningful_ai_value(value):
            continue
        if key not in extra_data or not str(extra_data.get(key, "")).strip():
            extra_data[key] = value
            applied.append(key)

    item.extra_data = extra_data
    update_fields = ["titulo", "quantidade", "descricao", "extra_data", "atualizado_em"]
    if category_changed:
        update_fields.append("category")
    item.save(update_fields=update_fields)

    return applied
