from django.db import migrations


def seed_default_categories(apps, schema_editor):
    EvidenceCategory = apps.get_model("apreensoes", "EvidenceCategory")
    CategoryField = apps.get_model("apreensoes", "CategoryField")

    default_categories = [
        {
            "nome": "Eletrônicos",
            "slug": "eletronicos",
            "descricao": "Celulares, notebooks, computadores, tablets e equipamentos correlatos.",
            "fields": [
                ("Marca", "marca", "text", False, "Fabricante ou marca comercial.", 1),
                ("Modelo", "modelo", "text", False, "Modelo do equipamento.", 2),
                ("Número de série", "numero_serie", "text", False, "Serial ou patrimônio.", 3),
                ("IMEI", "imei", "text", False, "Preencher manualmente se necessário.", 4),
                ("Cor", "cor", "text", False, "Cor predominante.", 5),
            ],
        },
        {
            "nome": "Veículos",
            "slug": "veiculos",
            "descricao": "Carros, motos, caminhões e outros veículos automotores.",
            "fields": [
                ("Marca", "marca", "text", False, "", 1),
                ("Modelo", "modelo", "text", False, "", 2),
                ("Placa", "placa", "text", False, "", 3),
                ("Chassi", "chassi", "text", False, "", 4),
                ("Renavam", "renavam", "text", False, "", 5),
                ("Cor", "cor", "text", False, "", 6),
            ],
        },
        {
            "nome": "Documentos",
            "slug": "documentos",
            "descricao": "Papéis, contratos, identidades, cartões e documentos diversos.",
            "fields": [
                ("Tipo de documento", "tipo_documento", "text", True, "", 1),
                ("Número do documento", "numero_documento", "text", False, "", 2),
                ("Titular", "titular", "text", False, "", 3),
                ("Data de emissão", "data_emissao", "date", False, "", 4),
            ],
        },
        {
            "nome": "Mídias de armazenamento",
            "slug": "midias-armazenamento",
            "descricao": "Pendrives, HDs, SSDs, cartões de memória e dispositivos similares.",
            "fields": [
                ("Tipo de mídia", "tipo_midia", "text", True, "", 1),
                ("Capacidade (GB)", "capacidade_gb", "integer", False, "", 2),
                ("Número de série", "numero_serie", "text", False, "", 3),
                ("Interface", "interface", "text", False, "USB, SATA, NVMe, etc.", 4),
            ],
        },
        {
            "nome": "Outros",
            "slug": "outros",
            "descricao": "Categoria coringa para itens que não se encaixam nas demais.",
            "fields": [],
        },
    ]

    for category_data in default_categories:
        category, created = EvidenceCategory.objects.get_or_create(
            nome=category_data["nome"],
            defaults={
                "slug": category_data["slug"],
                "descricao": category_data["descricao"],
                "is_default": True,
                "active": True,
            },
        )

        if not created:
            continue

        for label, key, field_type, required, help_text, sort_order in category_data["fields"]:
            CategoryField.objects.create(
                category=category,
                label=label,
                key=key,
                field_type=field_type,
                required=required,
                help_text=help_text,
                sort_order=sort_order,
            )


def remove_default_categories(apps, schema_editor):
    EvidenceCategory = apps.get_model("apreensoes", "EvidenceCategory")
    EvidenceCategory.objects.filter(is_default=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("apreensoes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_categories, remove_default_categories),
    ]
