from django.db import migrations


def seed_ammunition_category(apps, schema_editor):
    EvidenceCategory = apps.get_model("apreensoes", "EvidenceCategory")
    CategoryField = apps.get_model("apreensoes", "CategoryField")

    category, _ = EvidenceCategory.objects.get_or_create(
        slug="municoes",
        defaults={
            "nome": "Municoes",
            "descricao": "Cartuchos, projeteis, estojos e outros itens relacionados a municoes.",
            "is_default": True,
            "active": True,
        },
    )

    fields = [
        (
            "Calibre aparente",
            "calibre_aparente",
            "text",
            False,
            "Preencher apenas quando o calibre estiver visualmente indicado ou muito evidente.",
            1,
        ),
        (
            "Quantidade de unidades",
            "quantidade_unidades",
            "integer",
            True,
            "Numero de unidades visiveis ou conferidas.",
            2,
        ),
        (
            "Tipo de municao",
            "tipo_municao",
            "text",
            False,
            "Cartucho, estojo, projetil ou outro tipo aparente.",
            3,
        ),
        (
            "Marca",
            "marca",
            "text",
            False,
            "Fabricante ou marcacao visivel.",
            4,
        ),
        (
            "Acondicionamento",
            "acondicionamento",
            "text",
            False,
            "Soltas, em caixa, em carregador, em cilindro ou outro arranjo aparente.",
            5,
        ),
    ]

    for label, key, field_type, required, help_text, sort_order in fields:
        CategoryField.objects.get_or_create(
            category=category,
            key=key,
            defaults={
                "label": label,
                "field_type": field_type,
                "required": required,
                "help_text": help_text,
                "sort_order": sort_order,
            },
        )


def remove_ammunition_category(apps, schema_editor):
    EvidenceCategory = apps.get_model("apreensoes", "EvidenceCategory")
    EvidenceCategory.objects.filter(slug="municoes").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("apreensoes", "0004_seed_armas_drogas_categories"),
    ]

    operations = [
        migrations.RunPython(seed_ammunition_category, remove_ammunition_category),
    ]
