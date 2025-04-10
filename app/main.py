from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from datetime import datetime
import os
from app.services.reconciliation_service import ReconciliationService
from app.models.payment import ReconciliationResult
from typing import List, Dict
import pandas as pd
import io

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

# Gerar dados de exemplo em vez de carregar o arquivo
def generate_sample_data():
    try:
        # Criar alguns pagamentos de exemplo para o dia atual
        from datetime import date
        from app.models.payment import Payment
        
        today = date.today()
        date_key = today.isoformat()
        
        # Limpar dados existentes
        if date_key in reconciliation_service.payments:
            reconciliation_service.payments[date_key] = []
        
        # Gerar 10 transações de exemplo
        sample_payments = []
        payment_methods = ['mastercard', 'visa']
        
        for i in range(1, 11):
            # Alternar entre mastercard e visa
            payment_method = payment_methods[i % 2]
            
            # Gerar um valor de pagamento
            amount = 100.0 + (i * 50)
            
            # ID da transação
            transaction_id = f"TRANS{i:06d}"
            
            # Criar o pagamento
            payment = Payment(
                ticket_number=f"TK{i:04d}",
                amount=amount,
                payment_type='credit_card',
                payment_method=payment_method,
                installments=1,
                transaction_id=transaction_id,
                date=today,
                status='pending'
            )
            
            sample_payments.append(payment)
            
            # Adicionar ao dicionário de pagamentos
            if date_key not in reconciliation_service.payments:
                reconciliation_service.payments[date_key] = []
            
            reconciliation_service.payments[date_key].append(payment)
        
        print(f"Gerados {len(sample_payments)} pagamentos de exemplo para a data {date_key}")
        return sample_payments
    
    except Exception as e:
        print(f"Erro ao gerar dados de exemplo: {str(e)}")
        return []

# Gerar dados de exemplo na inicialização
generate_sample_data()

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
async def get_transactions(
    date: str = None, 
    status: str = None, 
    search: str = None,
    page: int = 1,
    page_size: int = 50
):
    """
    Obtém a lista de transações com filtros opcionais e paginação
    """
    try:
        items, total = reconciliation_service.get_transactions(
            date=date, 
            status=status, 
            search=search,
            page=page,
            page_size=page_size
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
        }
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
            
            # Calcular total por bandeira corretamente
            total_by_brand = {
                "mastercard": sum(p.amount for p in payments if p.payment_method == 'mastercard'),
                "visa": sum(p.amount for p in payments if p.payment_method == 'visa')
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

@app.get("/api/export/errors/{date}")
async def export_errors(date: str):
    """
    Exporta os pagamentos com erro de conciliação para uma data específica
    """
    try:
        # Converter string para data
        export_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Realizar conciliação para obter erros
        reconciliation_result = reconciliation_service.reconcile_payments(export_date)
        
        if not reconciliation_result['errors']:
            raise HTTPException(
                status_code=404,
                detail="Nenhum erro de conciliação encontrado para esta data"
            )
        
        # Criar DataFrame com os erros
        errors_data = []
        for error in reconciliation_result['errors']:
            errors_data.append({
                'Ticket': error['ticket'],
                'Valor Esperado': error['expected'],
                'Valor Recebido': error['received'],
                'Diferença': error['difference'],
                'Status': 'Erro - Valor maior que o esperado'
            })
        
        df = pd.DataFrame(errors_data)
        
        # Criar arquivo CSV em memória
        output = io.StringIO()
        df.to_csv(output, index=False, sep=';', decimal=',')
        output.seek(0)
        
        # Retornar arquivo para download
        return Response(
            content=output.getvalue(),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=erros_conciliacao_{date}.csv'
            }
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido. Use YYYY-MM-DD"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao exportar erros de conciliação: {str(e)}"
        ) 