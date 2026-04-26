from django.urls import path

from . import views

app_name = "apreensoes"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("operacoes/nova/", views.operation_create, name="operation_create"),
    path("operacoes/<int:pk>/", views.operation_detail, name="operation_detail"),
    path("operacoes/<int:pk>/editar/", views.operation_update, name="operation_update"),
    path("operacoes/<int:pk>/iniciar/", views.operation_start, name="operation_start"),
    path("operacoes/<int:pk>/encerrar/", views.operation_close, name="operation_close"),
    path("operacoes/<int:pk>/pdf/", views.operation_pdf, name="operation_pdf"),
    path(
        "operacoes/<int:operation_pk>/equipe/novo/",
        views.team_member_create,
        name="team_member_create",
    ),
    path("equipe/<int:pk>/remover/", views.team_member_delete, name="team_member_delete"),
    path("categorias/", views.category_list, name="category_list"),
    path("categorias/nova/", views.category_create, name="category_create"),
    path("categorias/<int:pk>/", views.category_detail, name="category_detail"),
    path(
        "categorias/<int:category_pk>/campos/novo/",
        views.category_field_create,
        name="category_field_create",
    ),
    path("operacoes/<int:operation_pk>/itens/novo/", views.item_create, name="item_create"),
    path("itens/<int:pk>/analisar-imagem/", views.item_analyze_image, name="item_analyze_image"),
    path("itens/<int:pk>/aplicar-ia/", views.item_apply_ai, name="item_apply_ai"),
    path("itens/<int:pk>/editar/", views.item_update, name="item_update"),
    path("itens/<int:pk>/remover/", views.item_delete, name="item_delete"),
]
