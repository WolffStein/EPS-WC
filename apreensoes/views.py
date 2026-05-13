import os

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .ai import (
    ImageAnalysisError,
    analyze_item_image,
    apply_ai_suggestions,
    get_ai_provider_name,
    get_ai_vision_model,
)
from .forms import (
    CategoryFieldForm,
    EvidenceCategoryForm,
    OperationForm,
    OperationWitnessFormSet,
    SeizedItemForm,
    SignInForm,
    TeamMemberForm,
)
from .models import EvidenceCategory, Operation, SeizedItem, TeamMember
from .pdf import build_operation_pdf


app_login_required = login_required(login_url="apreensoes:login")


def _ai_is_ready() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def _resolve_post_login_redirect(request: HttpRequest) -> str:
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("apreensoes:dashboard")


def _persist_ai_analysis(item: SeizedItem, analysis_payload: dict[str, object]) -> None:
    item.ai_analysis = analysis_payload
    item.ai_analysis_provider = get_ai_provider_name()
    item.ai_analysis_model = get_ai_vision_model()
    item.ai_last_analyzed_at = timezone.now()
    item.save(
        update_fields=[
            "ai_analysis",
            "ai_analysis_provider",
            "ai_analysis_model",
            "ai_last_analyzed_at",
            "atualizado_em",
        ]
    )


def _auto_fill_item_from_image(item: SeizedItem) -> tuple[bool, str]:
    analysis_payload = analyze_item_image(item)
    _persist_ai_analysis(item, analysis_payload)
    applied_fields = apply_ai_suggestions(item)

    if item.ai_should_create_multiple_records:
        if applied_fields:
            return (
                True,
                "Imagem analisada e sugestoes aplicadas em parte. Revise os grupos detectados, porque a foto parece conter mais de um registro.",
            )
        return (
            True,
            "Imagem analisada. A foto parece conter mais de um registro, entao o sistema manteve o preenchimento principal mais conservador.",
        )

    if applied_fields:
        return (
            True,
            "Imagem analisada e preenchimento assistido aplicado em: " + ", ".join(applied_fields) + ".",
        )

    return (
        True,
        "Imagem analisada, mas nao houve campos novos para preencher automaticamente.",
    )


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("apreensoes:dashboard")

    if request.method == "POST":
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Login realizado com sucesso.")
            return redirect(_resolve_post_login_redirect(request))
    else:
        form = SignInForm(request)

    return render(
        request,
        "registration/login.html",
        {
            "form": form,
            "next_url": request.POST.get("next") or request.GET.get("next", ""),
        },
    )


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Sessao encerrada com sucesso.")
    return redirect("apreensoes:login")


@app_login_required
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


@app_login_required
def operation_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = OperationForm(request.POST)
        witness_formset = OperationWitnessFormSet(request.POST)
        if form.is_valid() and witness_formset.is_valid():
            operation = form.save()
            witness_formset.instance = operation
            witness_formset.save()
            messages.success(request, "Operacao criada com sucesso.")
            return redirect("apreensoes:operation_detail", pk=operation.pk)
    else:
        form = OperationForm(initial={"data_operacao": timezone.localdate()})
        witness_formset = OperationWitnessFormSet()

    return render(
        request,
        "apreensoes/operation_form.html",
        {"form": form, "witness_formset": witness_formset, "page_title": "Nova operacao"},
    )


@app_login_required
def operation_update(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=pk)

    if operation.status == Operation.Status.CLOSED:
        messages.error(request, "Operacoes encerradas nao podem mais ser alteradas.")
        return redirect("apreensoes:operation_detail", pk=operation.pk)

    if request.method == "POST":
        form = OperationForm(request.POST, instance=operation)
        witness_formset = OperationWitnessFormSet(request.POST, instance=operation)
        if form.is_valid() and witness_formset.is_valid():
            form.save()
            witness_formset.save()
            messages.success(request, "Operacao atualizada.")
            return redirect("apreensoes:operation_detail", pk=operation.pk)
    else:
        form = OperationForm(instance=operation)
        witness_formset = OperationWitnessFormSet(instance=operation)

    return render(
        request,
        "apreensoes/operation_form.html",
        {"form": form, "witness_formset": witness_formset, "operation": operation, "page_title": "Editar operacao"},
    )


@app_login_required
def operation_detail(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(
        Operation.objects.prefetch_related(
            "team_members",
            "witnesses",
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
            "ai_ready": _ai_is_ready(),
        },
    )


@app_login_required
@require_POST
def operation_start(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=pk)
    operation.start()
    messages.success(request, "Operacao marcada como em andamento.")
    return redirect("apreensoes:operation_detail", pk=operation.pk)


@app_login_required
@require_POST
def operation_close(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=pk)
    operation.close()
    messages.success(request, "Operacao encerrada e pronta para gerar PDF.")
    return redirect("apreensoes:operation_detail", pk=operation.pk)


@app_login_required
def team_member_create(request: HttpRequest, operation_pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=operation_pk)

    if operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operacao ja foi encerrada.")
        return redirect("apreensoes:operation_detail", pk=operation.pk)

    if request.method == "POST":
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.operation = operation
            member.save()
            messages.success(request, "Integrante adicionado a equipe.")
            return redirect("apreensoes:operation_detail", pk=operation.pk)
    else:
        form = TeamMemberForm()

    return render(
        request,
        "apreensoes/team_member_form.html",
        {"form": form, "operation": operation},
    )


@app_login_required
@require_POST
def team_member_delete(request: HttpRequest, pk: int) -> HttpResponse:
    member = get_object_or_404(TeamMember.objects.select_related("operation"), pk=pk)
    operation_pk = member.operation.pk

    if member.operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operacao ja foi encerrada.")
    else:
        member.delete()
        messages.success(request, "Integrante removido.")

    return redirect("apreensoes:operation_detail", pk=operation_pk)


@app_login_required
def category_list(request: HttpRequest) -> HttpResponse:
    categories = EvidenceCategory.objects.prefetch_related("field_definitions").all()
    return render(
        request,
        "apreensoes/category_list.html",
        {"categories": categories},
    )


@app_login_required
def category_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = EvidenceCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(
                request,
                "Categoria criada. Agora voce pode adicionar os campos especificos dela.",
            )
            return redirect("apreensoes:category_detail", pk=category.pk)
    else:
        form = EvidenceCategoryForm()

    return render(
        request,
        "apreensoes/category_form.html",
        {"form": form},
    )


@app_login_required
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


@app_login_required
def category_field_create(request: HttpRequest, category_pk: int) -> HttpResponse:
    category = get_object_or_404(EvidenceCategory, pk=category_pk)

    if request.method == "POST":
        form = CategoryFieldForm(request.POST)
        if form.is_valid():
            category_field = form.save(commit=False)
            category_field.category = category
            category_field.save()
            messages.success(request, "Campo adicionado a categoria.")
            return redirect("apreensoes:category_detail", pk=category.pk)
    else:
        form = CategoryFieldForm()

    return render(
        request,
        "apreensoes/category_field_form.html",
        {"form": form, "category": category},
    )


@app_login_required
def item_create(request: HttpRequest, operation_pk: int) -> HttpResponse:
    operation = get_object_or_404(Operation, pk=operation_pk)

    if operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operacao ja foi encerrada.")
        return redirect("apreensoes:operation_detail", pk=operation.pk)

    initial = {}
    if request.method == "GET" and request.GET.get("category"):
        initial["category"] = request.GET.get("category")

    if request.method == "POST":
        form = SeizedItemForm(request.POST, request.FILES, operation=operation)
        if form.is_valid():
            item = form.save()
            if operation.status == Operation.Status.PLANNED:
                operation.start()
            if item.evidence_image:
                try:
                    _, auto_message = _auto_fill_item_from_image(item)
                except ImageAnalysisError as exc:
                    messages.warning(
                        request,
                        "Item registrado e imagem salva, mas a analise automatica nao conseguiu concluir agora: "
                        + str(exc),
                    )
                except Exception:
                    messages.warning(
                        request,
                        "Item registrado e imagem salva, mas a analise automatica falhou nesta tentativa.",
                    )
                else:
                    messages.success(request, auto_message)

                return redirect("apreensoes:item_update", pk=item.pk)

            messages.success(request, "Item apreendido registrado.")
            return redirect("apreensoes:operation_detail", pk=item.operation.pk)
    else:
        form = SeizedItemForm(operation=operation, initial=initial)

    return render(
        request,
        "apreensoes/item_form.html",
        {
            "form": form,
            "operation": operation,
            "mode": "create",
            "ai_ready": _ai_is_ready(),
        },
    )


@app_login_required
def item_update(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(
        SeizedItem.objects.select_related("operation", "category"),
        pk=pk,
    )
    operation = item.operation

    if operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operacao ja foi encerrada.")
        return redirect("apreensoes:operation_detail", pk=operation.pk)

    if request.method == "POST":
        form = SeizedItemForm(request.POST, request.FILES, instance=item, operation=operation)
        if form.is_valid():
            form.save()
            uploaded_new_image = bool(request.FILES.get("evidence_image"))
            if uploaded_new_image and item.evidence_image:
                try:
                    _, auto_message = _auto_fill_item_from_image(item)
                except ImageAnalysisError as exc:
                    messages.warning(
                        request,
                        "Item atualizado e imagem salva, mas a analise automatica nao conseguiu concluir agora: "
                        + str(exc),
                    )
                except Exception:
                    messages.warning(
                        request,
                        "Item atualizado e imagem salva, mas a analise automatica falhou nesta tentativa.",
                    )
                else:
                    messages.success(request, auto_message)

                return redirect("apreensoes:item_update", pk=item.pk)

            messages.success(request, "Item atualizado.")
            return redirect("apreensoes:operation_detail", pk=operation.pk)
    else:
        form = SeizedItemForm(instance=item, operation=operation)

    return render(
        request,
        "apreensoes/item_form.html",
        {
            "form": form,
            "operation": operation,
            "mode": "update",
            "item": item,
            "ai_ready": _ai_is_ready(),
        },
    )


@app_login_required
@require_POST
def item_analyze_image(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(
        SeizedItem.objects.select_related("operation", "category"),
        pk=pk,
    )

    if item.operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operacao ja foi encerrada.")
        return redirect("apreensoes:operation_detail", pk=item.operation.pk)

    try:
        analysis_payload = analyze_item_image(item)
    except ImageAnalysisError as exc:
        messages.error(request, str(exc))
    except Exception:
        messages.error(
            request,
            "Nao foi possivel concluir a analise da imagem agora. Verifique a configuracao da Gemini API e tente novamente.",
        )
    else:
        _persist_ai_analysis(item, analysis_payload)
        if item.ai_should_create_multiple_records:
            messages.success(
                request,
                "Analise concluida. A IA detectou uma cena com multiplos itens e recomenda criar registros separados.",
            )
        else:
            messages.success(request, "Analise de imagem concluida. Revise as sugestoes da IA.")

    return redirect("apreensoes:item_update", pk=item.pk)


@app_login_required
@require_POST
def item_apply_ai(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(
        SeizedItem.objects.select_related("operation", "category"),
        pk=pk,
    )

    if item.operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operacao ja foi encerrada.")
        return redirect("apreensoes:operation_detail", pk=item.operation.pk)

    try:
        applied_fields = apply_ai_suggestions(item)
    except ImageAnalysisError as exc:
        messages.error(request, str(exc))
    else:
        if applied_fields:
            message = "Sugestoes aplicadas automaticamente em: " + ", ".join(applied_fields) + "."
            if item.ai_should_create_multiple_records:
                message += " Revise os grupos detectados antes de encerrar, pois a foto sugere mais de um registro."
            messages.success(request, message)
        else:
            if item.ai_should_create_multiple_records:
                messages.info(
                    request,
                    "A IA sinalizou que a imagem parece conter mais de um item. Revise os grupos detectados e crie registros separados se necessario.",
                )
            else:
                messages.info(
                    request,
                    "A IA nao encontrou campos vazios novos para preencher automaticamente.",
                )

    return redirect("apreensoes:item_update", pk=item.pk)


@app_login_required
@require_POST
def item_delete(request: HttpRequest, pk: int) -> HttpResponse:
    item = get_object_or_404(SeizedItem.objects.select_related("operation"), pk=pk)
    operation_pk = item.operation.pk

    if item.operation.status == Operation.Status.CLOSED:
        messages.error(request, "A operacao ja foi encerrada.")
    else:
        item.delete()
        messages.success(request, "Item removido.")

    return redirect("apreensoes:operation_detail", pk=operation_pk)


@app_login_required
def operation_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    operation = get_object_or_404(
        Operation.objects.prefetch_related(
            "team_members",
            "witnesses",
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


@app_login_required
def help_view(request: HttpRequest) -> HttpResponse:
    return render(request, "apreensoes/help.html")
