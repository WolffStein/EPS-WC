from django.db import migrations


def seed_weapon_and_drug_categories(apps, schema_editor):
    EvidenceCategory = apps.get_model("apreensoes", "EvidenceCategory")
    CategoryField = apps.get_model("apreensoes", "CategoryField")

    categories = [
        {
            "nome": "Armas",
            "slug": "armas",
            "descricao": "Armas de fogo, armas brancas, municoes e acessorios relacionados.",
            "fields": [
                ("Tipo de arma", "tipo_arma", "text", True, "Pistola, revolver, fuzil, faca, etc.", 1),
                ("Marca", "marca", "text", False, "Fabricante visivel ou conhecido.", 2),
                ("Modelo", "modelo", "text", False, "Modelo visivel na arma.", 3),
                ("Calibre", "calibre", "text", False, "Apenas se legivel ou claramente identificavel.", 4),
                ("Numero de serie", "numero_serie", "text", False, "Preencher somente se visivel.", 5),
                ("Acabamento / cor", "acabamento_cor", "text", False, "Preta, inox, madeira, etc.", 6),
                ("Municiada", "municiada", "boolean", False, "Somente se a condicao for observavel.", 7),
            ],
        },
        {
            "nome": "Drogas",
            "slug": "drogas",
            "descricao": "Substancias entorpecentes, porcoes, tabletes, frascos e embalagens.",
            "fields": [
                ("Tipo aparente", "tipo_aparente", "text", True, "Somente se a embalagem ou aparencia sugerir algo.", 1),
                ("Forma de apresentacao", "forma_apresentacao", "text", False, "Tablete, porcao, po, pedra, liquido.", 2),
                ("Cor aparente", "cor_aparente", "text", False, "Cor observada na substancia ou no conteudo.", 3),
                ("Quantidade de volumes", "quantidade_volumes", "integer", False, "Numero visivel de porcoes, sacos ou frascos.", 4),
                ("Unidade aparente", "unidade_aparente", "text", False, "Sacos, tabletes, pinos, frascos, etc.", 5),
                ("Embalagem", "embalagem", "text", False, "Saco zip, fita, papel filme, frasco, etc.", 6),
                ("Rotulo / marcacao", "rotulo_marcacao", "text", False, "Marcacoes visiveis na embalagem.", 7),
            ],
        },
    ]

    for category_data in categories:
        category, _ = EvidenceCategory.objects.get_or_create(
            nome=category_data["nome"],
            defaults={
                "slug": category_data["slug"],
                "descricao": category_data["descricao"],
                "is_default": True,
                "active": True,
            },
        )

        for label, key, field_type, required, help_text, sort_order in category_data["fields"]:
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


def remove_weapon_and_drug_categories(apps, schema_editor):
    EvidenceCategory = apps.get_model("apreensoes", "EvidenceCategory")
    EvidenceCategory.objects.filter(nome__in=["Armas", "Drogas"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("apreensoes", "0003_alter_operation_options_seizeditem_ai_analysis_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_weapon_and_drug_categories, remove_weapon_and_drug_categories),
    ]
