import os
from pathlib import Path
from unittest.mock import patch

import httpx
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .ai import ImageAnalysisError, ItemImageSuggestion, analyze_item_image
from .forms import SeizedItemForm
from .models import EvidenceCategory, Operation, SeizedItem


TEST_MEDIA_ROOT = Path(__file__).resolve().parent.parent / "media" / "test_uploads"


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AppFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="agente",
            password="senha-segura-123",
        )
        self.client.force_login(self.user)
        self.category = EvidenceCategory.objects.get(slug="eletronicos")
        self.operation = Operation.objects.create(
            codigo="EPS-001",
            nome="Operacao EPS",
            departamento="Crimes Ciberneticos",
            responsavel="Delegado Joao",
            data_operacao="2026-04-20",
            local_apreensao="Rua Alfa, 123",
            cidade_uf="Brasilia/DF",
            suspeito_nome="Fulano de Tal",
        )

    def test_dashboard_requires_authentication(self):
        self.client.logout()

        response = self.client.get(reverse("apreensoes:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("apreensoes:login"), response.url)

    def test_login_view_authenticates_user(self):
        self.client.logout()

        response = self.client.post(
            reverse("apreensoes:login"),
            data={
                "username": "agente",
                "password": "senha-segura-123",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("apreensoes:dashboard"))
        follow_response = self.client.get(reverse("apreensoes:dashboard"))
        self.assertEqual(follow_response.status_code, 200)

    def test_dashboard_renders(self):
        response = self.client.get(reverse("apreensoes:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planejadas")
        self.assertContains(response, "EPS-001")

    def test_dynamic_item_form_saves_extra_data(self):
        form = SeizedItemForm(
            data={
                "category": self.category.pk,
                "titulo": "Celular Samsung",
                "quantidade": 1,
                "descricao": "Aparelho encontrado na residencia.",
                "local_encontrado": "Quarto principal",
                "estado": "Ligado",
                "campo_imei": "356789123456789",
            },
            operation=self.operation,
        )
        self.assertTrue(form.is_valid(), form.errors)

        item = form.save()
        self.assertEqual(item.extra_data["imei"], "356789123456789")

    def test_item_registration_view_accepts_image_upload(self):
        response = self.client.post(
            reverse("apreensoes:item_create", args=[self.operation.pk]),
            data={
                "category": self.category.pk,
                "titulo": "Notebook Dell",
                "quantidade": 2,
                "descricao": "Equipamento apreendido na empresa.",
                "local_encontrado": "Sala financeira",
                "estado": "Desligado",
                "campo_imei": "112233445566778",
                "evidence_image": SimpleUploadedFile(
                    "notebook.jpg",
                    b"fake-image-bytes",
                    content_type="image/jpeg",
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SeizedItem.objects.count(), 1)
        self.assertTrue(SeizedItem.objects.first().evidence_image.name.endswith(".jpg"))

    @patch("apreensoes.ai.genai.Client")
    def test_analyze_item_image_embeds_small_image_inline(self, mocked_client_cls):
        item = SeizedItem.objects.create(
            operation=self.operation,
            category=self.category,
            titulo="Celular",
            quantidade=1,
            evidence_image=SimpleUploadedFile(
                "celular.jpg",
                b"realistic-image-bytes",
                content_type="image/jpeg",
            ),
        )

        mocked_client = mocked_client_cls.return_value
        mocked_client.models.generate_content.return_value.text = ItemImageSuggestion(
            suggested_title="Celular preto",
            suggested_category="Eletronicos",
            suggested_category_slug="eletronicos",
            summary="Telefone celular visivel.",
            confidence="medium",
            suggested_quantity=1,
            visible_attributes=[],
            field_suggestions=[],
            officer_review_notes=[],
            missing_information=[],
            scene_type="single_item",
            should_create_multiple_records=False,
            detected_items=[],
        ).model_dump_json()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            payload = analyze_item_image(item)

        self.assertEqual(payload["suggested_title"], "Celular preto")
        mocked_client.files.upload.assert_not_called()
        call_args = mocked_client.models.generate_content.call_args.kwargs
        self.assertEqual(call_args["model"], os.environ.get("GEMINI_VISION_MODEL", "gemini-2.5-flash"))
        self.assertEqual(len(call_args["contents"]), 2)

    @patch("apreensoes.ai.genai.Client")
    def test_analyze_item_image_uploads_large_image_file(self, mocked_client_cls):
        item = SeizedItem.objects.create(
            operation=self.operation,
            category=self.category,
            titulo="Celular",
            quantidade=1,
            evidence_image=SimpleUploadedFile(
                "celular.jpg",
                b"realistic-image-bytes",
                content_type="image/jpeg",
            ),
        )

        mocked_client = mocked_client_cls.return_value
        mocked_client.files.upload.return_value = "uploaded-file"
        mocked_client.models.generate_content.return_value.text = ItemImageSuggestion(
            suggested_title="Celular preto",
            suggested_category="Eletronicos",
            suggested_category_slug="eletronicos",
            summary="Telefone celular visivel.",
            confidence="medium",
            suggested_quantity=1,
            visible_attributes=[],
            field_suggestions=[],
            officer_review_notes=[],
            missing_information=[],
            scene_type="single_item",
            should_create_multiple_records=False,
            detected_items=[],
        ).model_dump_json()

        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}),
            patch("apreensoes.ai.GEMINI_INLINE_IMAGE_LIMIT_BYTES", 1),
        ):
            payload = analyze_item_image(item)

        uploaded = mocked_client.files.upload.call_args.kwargs["file"]
        self.assertIsInstance(uploaded, Path)
        self.assertTrue(uploaded.name.endswith(".jpg"))
        self.assertEqual(payload["suggested_title"], "Celular preto")

    @patch("apreensoes.ai.genai.Client")
    def test_analyze_item_image_returns_friendly_message_on_connection_error(
        self,
        mocked_client_cls,
    ):
        item = SeizedItem.objects.create(
            operation=self.operation,
            category=self.category,
            titulo="Celular",
            quantidade=1,
            evidence_image=SimpleUploadedFile(
                "celular.jpg",
                b"realistic-image-bytes",
                content_type="image/jpeg",
            ),
        )

        mocked_client = mocked_client_cls.return_value
        mocked_client.models.generate_content.side_effect = httpx.ConnectError("network down")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with self.assertRaisesMessage(
                ImageAnalysisError,
                "Nao foi possivel conectar a Gemini API agora. Verifique sua rede e tente novamente.",
            ):
                analyze_item_image(item)

    @patch(
        "apreensoes.views.analyze_item_image",
        return_value={
            "suggested_title": "Celular preto",
            "suggested_category": "Eletronicos",
            "suggested_category_slug": "eletronicos",
            "summary": "Telefone celular visivel sobre a mesa.",
            "confidence": "medium",
            "suggested_quantity": 1,
            "visible_attributes": [{"label": "Cor", "value": "Preta"}],
            "field_suggestions": [{"key": "marca", "label": "Marca", "value": "Samsung"}],
            "officer_review_notes": ["Confirmar o IMEI manualmente."],
            "missing_information": ["IMEI nao visivel na foto."],
            "scene_type": "single_item",
            "should_create_multiple_records": False,
            "detected_items": [],
        },
    )
    def test_item_ai_analysis_route_persists_payload(self, mocked_analysis):
        item = SeizedItem.objects.create(
            operation=self.operation,
            category=self.category,
            titulo="Celular",
            quantidade=1,
            evidence_image=SimpleUploadedFile(
                "celular.jpg",
                b"fake-image-bytes",
                content_type="image/jpeg",
            ),
        )

        response = self.client.post(reverse("apreensoes:item_analyze_image", args=[item.pk]))
        self.assertEqual(response.status_code, 302)

        item.refresh_from_db()
        self.assertEqual(item.ai_analysis["suggested_title"], "Celular preto")
        self.assertEqual(item.ai_analysis_provider, "gemini")
        self.assertTrue(item.ai_last_analyzed_at is not None)
        mocked_analysis.assert_called_once()

    def test_apply_ai_suggestions_fills_empty_fields(self):
        armas = EvidenceCategory.objects.get(nome="Armas")
        item = SeizedItem.objects.create(
            operation=self.operation,
            category=armas,
            titulo="Item",
            quantidade=1,
            evidence_image=SimpleUploadedFile(
                "arma.jpg",
                b"fake-image-bytes",
                content_type="image/jpeg",
            ),
            ai_analysis={
                "suggested_title": "Pistola preta",
                "suggested_category": "Armas",
                "suggested_category_slug": "armas",
                "summary": "Arma curta aparentemente do tipo pistola sobre uma superficie.",
                "confidence": "high",
                "suggested_quantity": 1,
                "field_suggestions": [
                    {"key": "tipo_arma", "label": "Tipo de arma", "value": "Pistola"},
                    {"key": "acabamento_cor", "label": "Acabamento / cor", "value": "Preta"},
                ],
                "officer_review_notes": ["Confirmar numero de serie no exame direto."],
                "missing_information": ["Numero de serie nao legivel na foto."],
                "scene_type": "single_item",
                "should_create_multiple_records": False,
                "detected_items": [],
            },
        )

        response = self.client.post(reverse("apreensoes:item_apply_ai", args=[item.pk]))
        self.assertEqual(response.status_code, 302)

        item.refresh_from_db()
        self.assertEqual(item.titulo, "Pistola preta")
        self.assertEqual(item.descricao, "Arma curta aparentemente do tipo pistola sobre uma superficie.")
        self.assertEqual(item.extra_data["tipo_arma"], "Pistola")
        self.assertEqual(item.extra_data["acabamento_cor"], "Preta")

    def test_apply_ai_suggestions_keeps_primary_fields_conservative_for_mixed_scene(self):
        outros = EvidenceCategory.objects.get(slug="outros")
        item = SeizedItem.objects.create(
            operation=self.operation,
            category=outros,
            titulo="Item",
            quantidade=1,
            evidence_image=SimpleUploadedFile(
                "cena-mista.jpg",
                b"fake-image-bytes",
                content_type="image/jpeg",
            ),
            ai_analysis={
                "suggested_title": "Pistola com municoes ao lado",
                "suggested_category": "Armas",
                "suggested_category_slug": "armas",
                "summary": "Cena com arma curta aparente e municoes visiveis.",
                "confidence": "medium",
                "suggested_quantity": 3,
                "field_suggestions": [
                    {"key": "tipo_arma", "label": "Tipo de arma", "value": "Pistola"},
                    {"key": "acabamento_cor", "label": "Acabamento / cor", "value": "Preta"},
                ],
                "officer_review_notes": [
                    "Criar registros separados para a arma e para as municoes."
                ],
                "missing_information": [
                    "Nao esta claro qual grupo corresponde ao registro atual."
                ],
                "scene_type": "mixed_scene",
                "should_create_multiple_records": True,
                "detected_items": [
                    {
                        "position_reference": "centro",
                        "suggested_title": "Pistola preta",
                        "suggested_category": "Armas",
                        "suggested_category_slug": "armas",
                        "summary": "Arma curta aparente em primeiro plano.",
                        "suggested_quantity": 1,
                        "should_be_separate_record": True,
                        "confidence": "medium",
                    },
                    {
                        "position_reference": "direita",
                        "suggested_title": "Municoes aparentes",
                        "suggested_category": "Municoes",
                        "suggested_category_slug": "municoes",
                        "summary": "Conjunto de cartuchos visiveis agrupados.",
                        "suggested_quantity": 12,
                        "should_be_separate_record": True,
                        "confidence": "medium",
                    },
                ],
            },
        )

        response = self.client.post(reverse("apreensoes:item_apply_ai", args=[item.pk]))
        self.assertEqual(response.status_code, 302)

        item.refresh_from_db()
        self.assertEqual(item.category.slug, "armas")
        self.assertEqual(item.titulo, "Item")
        self.assertEqual(item.quantidade, 1)
        self.assertEqual(item.descricao, "")
        self.assertEqual(item.extra_data["tipo_arma"], "Pistola")
        self.assertEqual(item.extra_data["acabamento_cor"], "Preta")

    def test_apply_ai_suggestions_ignores_placeholder_values(self):
        drogas = EvidenceCategory.objects.get(slug="drogas")
        item = SeizedItem.objects.create(
            operation=self.operation,
            category=drogas,
            titulo="Item",
            quantidade=1,
            ai_analysis={
                "suggested_title": "Drogas aparentes",
                "suggested_category": "Drogas",
                "suggested_category_slug": "drogas",
                "summary": "Volumes aparentes sobre a mesa.",
                "confidence": "medium",
                "suggested_quantity": 1,
                "field_suggestions": [
                    {"key": "tipo_aparente", "label": "Tipo aparente", "value": "Pedras"},
                    {
                        "key": "quantidade_volumes",
                        "label": "Quantidade de volumes",
                        "value": "null",
                    },
                    {
                        "key": "rotulo_marcacao",
                        "label": "Rotulo / marcacao",
                        "value": "Nao visivel",
                    },
                ],
                "officer_review_notes": [],
                "missing_information": [],
                "scene_type": "single_item",
                "should_create_multiple_records": False,
                "detected_items": [],
            },
        )

        response = self.client.post(reverse("apreensoes:item_apply_ai", args=[item.pk]))
        self.assertEqual(response.status_code, 302)

        item.refresh_from_db()
        self.assertEqual(item.extra_data["tipo_aparente"], "Pedras")
        self.assertNotIn("quantidade_volumes", item.extra_data)
        self.assertNotIn("rotulo_marcacao", item.extra_data)

    def test_item_update_view_shows_detected_items_for_mixed_scene(self):
        armas = EvidenceCategory.objects.get(nome="Armas")
        item = SeizedItem.objects.create(
            operation=self.operation,
            category=armas,
            titulo="Registro provisiorio",
            quantidade=1,
            evidence_image=SimpleUploadedFile(
                "foto-mista.jpg",
                b"fake-image-bytes",
                content_type="image/jpeg",
            ),
            ai_analysis={
                "suggested_title": "Cena com arma e porcoes",
                "suggested_category": "Armas",
                "suggested_category_slug": "armas",
                "summary": "Imagem com arma curta, municoes e porcoes aparentes.",
                "confidence": "medium",
                "suggested_quantity": 1,
                "visible_attributes": [{"label": "Acabamento", "value": "Preto"}],
                "field_suggestions": [],
                "officer_review_notes": ["Separar arma, municoes e drogas em registros distintos."],
                "missing_information": ["Calibre e substancia nao podem ser confirmados so pela foto."],
                "scene_type": "mixed_scene",
                "should_create_multiple_records": True,
                "detected_items": [
                    {
                        "position_reference": "esquerda",
                        "suggested_title": "Pistola preta",
                        "suggested_category": "Armas",
                        "suggested_category_slug": "armas",
                        "summary": "Arma curta aparente apoiada no lado esquerdo.",
                        "suggested_quantity": 1,
                        "should_be_separate_record": True,
                        "confidence": "medium",
                    },
                    {
                        "position_reference": "centro",
                        "suggested_title": "Porcoes aparentes",
                        "suggested_category": "Drogas",
                        "suggested_category_slug": "drogas",
                        "summary": "Conjunto de porcoes embaladas ao centro da cena.",
                        "suggested_quantity": 20,
                        "should_be_separate_record": True,
                        "confidence": "medium",
                    },
                    {
                        "position_reference": "direita",
                        "suggested_title": "Municoes aparentes",
                        "suggested_category": "Municoes",
                        "suggested_category_slug": "municoes",
                        "summary": "Cartuchos agrupados no lado direito.",
                        "suggested_quantity": 18,
                        "should_be_separate_record": True,
                        "confidence": "medium",
                    },
                ],
            },
        )

        response = self.client.get(reverse("apreensoes:item_update", args=[item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cena com mais de um registro potencial")
        self.assertContains(response, "Municoes aparentes")
        self.assertContains(response, "Cena: Cena mista")

    def test_close_operation_and_generate_pdf(self):
        SeizedItem.objects.create(
            operation=self.operation,
            category=self.category,
            titulo="HD externo",
            quantidade=1,
            extra_data={"imei": "nao-aplicavel"},
        )
        self.client.post(reverse("apreensoes:operation_close", args=[self.operation.pk]))
        self.operation.refresh_from_db()

        self.assertEqual(self.operation.status, Operation.Status.CLOSED)
        pdf_response = self.client.get(reverse("apreensoes:operation_pdf", args=[self.operation.pk]))

        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))
