from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
import os
from app.services.reconciliation_service import ReconciliationService
from app.models.payment import ReconciliationResult
from typing import List, Dict

app = FastAPI(
    title="FinanceSync Estacionamento",
    description="Sistema para conciliação financeira diária de estacionamentos",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretório para upload de arquivos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Montar diretório de arquivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Instância do serviço de conciliação
reconciliation_service = ReconciliationService()

@app.get("/")
async def root():
    return FileResponse("app/static/index.html")

@app.get("/api/dashboard/{date}")
async def get_dashboard_data(date: str):
    """
    Retorna os dados do dashboard para uma data específica
    """
    try:
        # Converter string para data
        dashboard_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Obter dados do serviço de reconciliação
        dashboard_data = reconciliation_service.get_dashboard_data(dashboard_date)
        
        return JSONResponse(
            status_code=200,
            content=dashboard_data
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Data inválida: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter dados do dashboard: {str(e)}"
        )

@app.get("/api/transactions")
async def get_transactions(date: str = None, status: str = None, search: str = None):
    """
    Obtém a lista de transações com filtros opcionais
    """
    try:
        transactions = reconciliation_service.get_transactions(date, status, search)
        return transactions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter transações: {str(e)}"
        )

@app.post("/api/reconcile")
async def reconcile_payments(request: Request):
    """
    Realiza a conciliação dos pagamentos para uma data específica
    """
    try:
        data = await request.json()
        date = data.get('date')
        
        if not date:
            raise HTTPException(
                status_code=400,
                detail="Data não fornecida"
            )
            
        # Converter string para data
        reconciliation_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Realizar conciliação
        result = reconciliation_service.reconcile_payments(reconciliation_date)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Conciliação realizada com sucesso",
                "result": result
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Data inválida: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao realizar conciliação: {str(e)}"
        )

@app.post("/upload/credit-card")
async def upload_credit_card(file: UploadFile = File(...)):
    """
    Upload de arquivo de vendas de cartão de crédito
    Formato esperado: CSV (Comma-Separated Values) ou TSV (Tab-Separated Values) com as colunas:
    - order_id
    - payment_sequential
    - payment_type
    - payment_installments
    - payment_value
    """
    try:
        # Validar extensão do arquivo
        if not file.filename.lower().endswith(('.csv', '.txt', '.tsv')):
            raise HTTPException(
                status_code=400,
                detail="Arquivo deve ter extensão .csv, .txt ou .tsv"
            )

        # Criar diretório de upload se não existir
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Salvar arquivo com timestamp para evitar conflitos
        extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"credit_card_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}")
        
        try:
            # Ler e salvar o arquivo
            content = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Processar arquivo
            payments = reconciliation_service.process_credit_card_file(file_path)
            
            # Calcular total por bandeira (placeholder - você pode adicionar a lógica específica)
            total_by_brand = {
                "mastercard": sum(p.amount for p in payments),  # Temporário
                "visa": 0.0  # Temporário
            }
            
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Arquivo processado com sucesso",
                    "filename": file.filename,
                    "saved_as": file_path,
                    "processed_payments": len(payments),
                    "total_value": sum(payment.amount for payment in payments),
                    "total_by_brand": total_by_brand
                }
            )
            
        except ValueError as ve:
            # Remover arquivo em caso de erro de validação
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=422,
                detail=str(ve)
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )

@app.post("/upload/cnab")
async def upload_cnab(file: UploadFile = File(...)):
    """
    Upload de arquivo CNAB para pagamentos via boleto
    """
    try:
        # Validar extensão do arquivo
        if not file.filename.endswith('.txt'):
            raise HTTPException(
                status_code=400,
                detail="Arquivo deve ter extensão .txt"
            )

        # Salvar arquivo
        file_path = os.path.join(UPLOAD_DIR, f"cnab_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Processar arquivo
        payments = reconciliation_service.process_cnab_file(file_path)
        
        return {
            "message": "Arquivo CNAB processado com sucesso",
            "filename": file.filename,
            "processed_payments": len(payments)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )

@app.post("/upload/pix")
async def upload_pix(file: UploadFile = File(...)):
    """
    Upload de arquivo de extratos PIX
    """
    try:
        # Validar extensão do arquivo
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail="Arquivo deve ter extensão .xlsx"
            )

        # Salvar arquivo
        file_path = os.path.join(UPLOAD_DIR, f"pix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Processar arquivo
        payments = reconciliation_service.process_pix_file(file_path)
        
        return {
            "message": "Arquivo PIX processado com sucesso",
            "filename": file.filename,
            "processed_payments": len(payments)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )

@app.get("/api/export/{date}")
async def export_transactions(date: str, format: str = "csv"):
    """
    Exporta as transações de uma data específica
    """
    try:
        export_date = datetime.strptime(date, "%Y-%m-%d")
        file_path = reconciliation_service.export_transactions(export_date, format)
        return FileResponse(
            file_path,
            filename=f"transactions_{date}.{format}",
            media_type="application/octet-stream"
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido. Use YYYY-MM-DD"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao exportar transações: {str(e)}"
        ) 