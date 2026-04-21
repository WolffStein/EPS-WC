from django.test import TestCase
from django.urls import reverse

from .forms import SeizedItemForm
from .models import EvidenceCategory, Operation, SeizedItem


class AppFlowTests(TestCase):
    def setUp(self):
        self.category = EvidenceCategory.objects.get(nome="Eletrônicos")
        self.operation = Operation.objects.create(
            codigo="EPS-001",
            nome="Operação EPS",
            departamento="Crimes Cibernéticos",
            responsavel="Delegado João",
            data_operacao="2026-04-20",
            local_apreensao="Rua Alfa, 123",
            cidade_uf="Brasília/DF",
            suspeito_nome="Fulano de Tal",
        )

    def test_dashboard_renders(self):
        response = self.client.get(reverse("apreensoes:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Operações")
        self.assertContains(response, "EPS-001")

    def test_dynamic_item_form_saves_extra_data(self):
        form = SeizedItemForm(
            data={
                "category": self.category.pk,
                "titulo": "Celular Samsung",
                "quantidade": 1,
                "descricao": "Aparelho encontrado na residência.",
                "local_encontrado": "Quarto principal",
                "estado": "Ligado",
                "campo_imei": "356789123456789",
            },
            operation=self.operation,
        )
        self.assertTrue(form.is_valid(), form.errors)

        item = form.save()
        self.assertEqual(item.extra_data["imei"], "356789123456789")

    def test_item_registration_view_creates_item(self):
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
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SeizedItem.objects.count(), 1)

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
