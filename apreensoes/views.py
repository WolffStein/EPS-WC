from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CategoryFieldForm,
    EvidenceCategoryForm,
    OperationForm,
    SeizedItemForm,
    TeamMemberForm,
)
from .models import EvidenceCategory, Operation, SeizedItem, TeamMember
from .pdf import build_operation_pdf


def dashboard(request: HttpRequest) -> HttpResponse:
    operations = Operation.objects.prefetch_related("team_members", "items").all()
    context = {
        "operations": operations,
        "stats": {
            "planejadas": operations.filter(status=Operation.Status.PLANNED).count(),
            "em_andamento": operations.filter(status=Operation.Status.IN_PROGRESS).count(),
            "encerradas": operations.filter(status=Operation.Status.CLOSED).count(),
        },
    }
    return render(request, "apreensoes/dashboard.html", context)


def operation_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = OperationForm(request.POST)
        if form.is_valid():
            operation = form.save()
            messages.success(request, "Operação criada com sucesso.")
            return redirect("apreensoes:operation_detail", pk=operation.pk)
    else:
        form = OperationForm(initial={"data_operacao": timezone.localdate()})

    return render(
        request,
        "apreensoes/operation_form.html",
        {"form": form, "page_title": "Nova operação"},
    )


def operation_update(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=pk)

    if operation.status == Operation.Status.CLOSED:
        messages.error(request, "Operações encerradas não podem mais ser alteradas.")
        return redirect("apreensoes:operation_detail", pk=operation.pk)

    if request.method == "POST":
        form = OperationForm(request.POST, instance=operation)
        if form.is_valid():
            form.save()
            messages.success(request, "Operação atualizada.")
            return redirect("apreensoes:operation_detail", pk=operation.pk)
    else:
        form = OperationForm(instance=operation)

    return render(
        request,
        "apreensoes/operation_form.html",
        {"form": form, "operation": operation, "page_title": "Editar operação"},
    )


def operation_detail(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(
        Operation.objects.prefetch_related(
            "team_members",
            "items__category__field_definitions",
        ),
        pk=pk,
    )
    categories = EvidenceCategory.objects.filter(active=True).prefetch_related("field_definitions")

    return render(
        request,
        "apreensoes/operation_detail.html",
        {
            "operation": operation,
            "categories": categories,
        },
    )


@require_POST
def operation_start(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=pk)
    operation.start()
    messages.success(request, "Operação marcada como em andamento.")
    return redirect("apreensoes:operation_detail", pk=operation.pk)


@require_POST
def operation_close(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=pk)
    operation.close()
    messages.success(request, "Operação encerrada e pronta para gerar PDF.")
    return redirect("apreensoes:operation_detail", pk=operation.pk)


def team_member_create(request: HttpRequest, operation_pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=operation_pk)

    if operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operação já foi encerrada.")
        return redirect("apreensoes:operation_detail", pk=operation.pk)

    if request.method == "POST":
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.operation = operation
            member.save()
            messages.success(request, "Integrante adicionado à equipe.")
            return redirect("apreensoes:operation_detail", pk=operation.pk)
    else:
        form = TeamMemberForm()

    return render(
        request,
        "apreensoes/team_member_form.html",
        {"form": form, "operation": operation},
    )


@require_POST
def team_member_delete(request: HttpRequest, pk: int) -> HttpResponse:
    member = get_object_or_404(TeamMember.objects.select_related("operation"), pk=pk)
    operation_pk = member.operation.pk

    if member.operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operação já foi encerrada.")
    else:
        member.delete()
        messages.success(request, "Integrante removido.")

    return redirect("apreensoes:operation_detail", pk=operation_pk)


def category_list(request: HttpRequest) -> HttpResponse:
    categories = EvidenceCategory.objects.prefetch_related("field_definitions").all()
    return render(
        request,
        "apreensoes/category_list.html",
        {"categories": categories},
    )


def category_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = EvidenceCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(
                request,
                "Categoria criada. Agora você pode adicionar os campos específicos dela.",
            )
            return redirect("apreensoes:category_detail", pk=category.pk)
    else:
        form = EvidenceCategoryForm()

    return render(
        request,
        "apreensoes/category_form.html",
        {"form": form},
    )


def category_detail(request: HttpRequest, pk: int) -> HttpResponse:
    category = get_object_or_404(
        EvidenceCategory.objects.prefetch_related("field_definitions"),
        pk=pk,
    )
    return render(
        request,
        "apreensoes/category_detail.html",
        {"category": category},
    )


def category_field_create(request: HttpRequest, category_pk: int) -> HttpResponse:
    category = get_object_or_404(EvidenceCategory, pk=category_pk)

    if request.method == "POST":
        form = CategoryFieldForm(request.POST)
        if form.is_valid():
            category_field = form.save(commit=False)
            category_field.category = category
            category_field.save()
            messages.success(request, "Campo adicionado à categoria.")
            return redirect("apreensoes:category_detail", pk=category.pk)
    else:
        form = CategoryFieldForm()

    return render(
        request,
        "apreensoes/category_field_form.html",
        {"form": form, "category": category},
    )


def item_create(request: HttpRequest, operation_pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=operation_pk)

    if operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operação já foi encerrada.")
        return redirect("apreensoes:operation_detail", pk=operation.pk)

    initial = {}
    if request.method == "GET" and request.GET.get("category"):
        initial["category"] = request.GET.get("category")

    if request.method == "POST":
        form = SeizedItemForm(request.POST, operation=operation)
        if form.is_valid():
            item = form.save()
            if operation.status == Operation.Status.PLANNED:
                operation.start()
            messages.success(request, "Item apreendido registrado.")
            return redirect("apreensoes:operation_detail", pk=item.operation.pk)
    else:
        form = SeizedItemForm(operation=operation, initial=initial)

    return render(
        request,
        "apreensoes/item_form.html",
        {"form": form, "operation": operation, "mode": "create"},
    )


def item_update(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(
        SeizedItem.objects.select_related("operation", "category"),
        pk=pk,
    )
    operation = item.operation

    if operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operação já foi encerrada.")
        return redirect("apreensoes:operation_detail", pk=operation.pk)

    if request.method == "POST":
        form = SeizedItemForm(request.POST, instance=item, operation=operation)
        if form.is_valid():
            form.save()
            messages.success(request, "Item atualizado.")
            return redirect("apreensoes:operation_detail", pk=operation.pk)
    else:
        form = SeizedItemForm(instance=item, operation=operation)

    return render(
        request,
        "apreensoes/item_form.html",
        {"form": form, "operation": operation, "mode": "update", "item": item},
    )


@require_POST
def item_delete(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(SeizedItem.objects.select_related("operation"), pk=pk)
    operation_pk = item.operation.pk

    if item.operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operação já foi encerrada.")
    else:
        item.delete()
        messages.success(request, "Item removido.")

    return redirect("apreensoes:operation_detail", pk=operation_pk)


def operation_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(
        Operation.objects.prefetch_related(
            "team_members",
            "items__category__field_definitions",
        ),
        pk=pk,
    )
    pdf_content = build_operation_pdf(operation)

    response = HttpResponse(pdf_content, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="auto-apreensao-{operation.codigo.lower()}.pdf"'
    )
    return response
