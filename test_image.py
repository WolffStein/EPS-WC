import os
import sys
import django
from pathlib import Path

# Load .env manually for tests
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apreensoes.models import Operation, EvidenceCategory, SeizedItem
from apreensoes.ai import analyze_item_image, ImageAnalysisError
from django.core.files import File

def run_test():
    print("Iniciando teste do sistema...")
    
    # 1. Verificar categorias
    cat_eletronicos = EvidenceCategory.objects.filter(slug='eletronicos').first()
    if not cat_eletronicos:
        print("Categoria 'eletronicos' não encontrada. Verifique se o banco foi populado.")
        return
        
    print(f"Categoria encontrada: {cat_eletronicos.nome}")
    
    # Limpar operações de teste anteriores
    Operation.objects.filter(codigo__startswith="TEST-").delete()
    
    # 2. Criar operacao
    op = Operation.objects.create(
        codigo="TEST-02",
        nome="Operacao de Teste 2",
        departamento="TI",
        data_operacao="2026-05-02"
    )
    print(f"Operacao criada: {op.codigo}")
    
    # 3. Criar item apreendido
    item = SeizedItem(
        operation=op,
        category=cat_eletronicos,
        titulo="Celular Apreendido",
        quantidade=1,
    )
    
    # 4. Anexar imagem de teste
    test_image_dir = Path(r"C:\Users\Eduardo\Documents\faculdade\eps\imagens\test")
    test_image_path = None
    for file in test_image_dir.iterdir():
        if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            test_image_path = file
            break
            
    if not test_image_path:
        print("Nenhuma imagem de teste encontrada.")
        return
        
    print(f"Usando imagem de teste: {test_image_path}")
    
    with open(test_image_path, 'rb') as f:
        item.evidence_image.save(test_image_path.name, File(f), save=True)
        
    print(f"Item criado e imagem salva em: {item.evidence_image.path}")
    
    # 5. Testar Analise IA (Formulario preenchimento/OCR)
    try:
        print("Iniciando chamada para a IA...")
        analysis = analyze_item_image(item)
        print("SUCESSO! Resposta da IA:")
        print(analysis)
    except ImageAnalysisError as e:
        print(f"ERRO DE IA: {e}")
    except Exception as e:
        print(f"ERRO INESPERADO: {e}")

if __name__ == '__main__':
    run_test()
