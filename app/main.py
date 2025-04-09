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

@app.get("/api/history")
async def get_reconciliation_history(
    start_date: str = None,
    end_date: str = None,
    payment_method: str = None,
    view_type: str = "daily"
):
    """
    Obtém o histórico de conciliações para análise, com opções de filtro por período, método de pagamento e tipo de visualização
    """
    try:
        # Validar datas se fornecidas
        if start_date:
            datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            datetime.strptime(end_date, '%Y-%m-%d')
        
        # Validar tipo de visualização
        if view_type not in ['daily', 'monthly', 'yearly']:
            raise ValueError(f"Tipo de visualização inválido: {view_type}")
        
        # Simulação de resposta para o protótipo
        # Em um cenário real, você chamaria o método correspondente no serviço
        
        # Obter todas as datas no serviço de reconciliação
        all_dates = list(reconciliation_service.payments.keys())
        
        # Filtrar datas conforme start_date e end_date
        filtered_dates = all_dates
        if start_date:
            filtered_dates = [d for d in filtered_dates if d >= start_date]
        if end_date:
            filtered_dates = [d for d in filtered_dates if d <= end_date]
        
        # Construir resposta com dados filtrados
        history_items = []
        
        for date_key in filtered_dates:
            payments = reconciliation_service.payments.get(date_key, [])
            
            # Pular se não houver pagamentos
            if not payments:
                continue
                
            # Filtrar por método de pagamento se especificado
            if payment_method and payment_method != 'all':
                payments = [p for p in payments if p.payment_method == payment_method]
                
                # Pular se não houver pagamentos após filtro
                if not payments:
                    continue
            
            # Calcular valores agregados
            total_expected = sum(reconciliation_service.expected_payments.get(date_key, {}).values())
            total_received = sum(p.amount for p in payments)
            
            # Calcular métodos de pagamento
            payment_methods = {
                'mastercard': sum(p.amount for p in payments if p.payment_method == 'mastercard'),
                'visa': sum(p.amount for p in payments if p.payment_method == 'visa'),
                'pix': sum(p.amount for p in payments if p.payment_method == 'pix'),
                'boleto': sum(p.amount for p in payments if p.payment_method == 'boleto')
            }
            
            # Determinar status baseado na diferença
            difference = total_received - total_expected
            status = 'reconciled' if abs(difference) < 0.01 else ('pending' if total_received < total_expected else 'error')
            
            # Adicionar item ao histórico
            history_items.append({
                'date': date_key,
                'expected_amount': total_expected,
                'received_amount': total_received,
                'difference': difference,
                'status': status,
                'payment_methods': payment_methods,
                'transaction_count': len(payments)
            })
        
        # Agrupar conforme o tipo de visualização
        if view_type != 'daily':
            grouped_items = {}
            
            for item in history_items:
                group_key = item['date'][:7] if view_type == 'monthly' else item['date'][:4]
                
                if group_key not in grouped_items:
                    grouped_items[group_key] = {
                        'date': group_key,
                        'expected_amount': 0,
                        'received_amount': 0,
                        'difference': 0,
                        'payment_methods': {
                            'mastercard': 0,
                            'visa': 0,
                            'pix': 0,
                            'boleto': 0
                        },
                        'transaction_count': 0
                    }
                
                # Somar valores
                grouped_items[group_key]['expected_amount'] += item['expected_amount']
                grouped_items[group_key]['received_amount'] += item['received_amount']
                grouped_items[group_key]['difference'] += item['difference']
                
                for method in item['payment_methods']:
                    grouped_items[group_key]['payment_methods'][method] += item['payment_methods'][method]
                
                grouped_items[group_key]['transaction_count'] += item['transaction_count']
            
            # Determinar status baseado na diferença agregada
            for key in grouped_items:
                difference = grouped_items[key]['difference']
                grouped_items[key]['status'] = 'reconciled' if abs(difference) < 0.01 else ('pending' if difference < 0 else 'error')
            
            history_items = list(grouped_items.values())
        
        return JSONResponse(
            status_code=200,
            content={
                'items': history_items,
                'total': len(history_items)
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Parâmetros inválidos: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter histórico de conciliações: {str(e)}"
        )

@app.get("/api/history/compare")
async def compare_periods(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    payment_method: str = None
):
    """
    Compara dados de reconciliação entre dois períodos distintos
    """
    try:
        # Validar datas
        for date_str in [period1_start, period1_end, period2_start, period2_end]:
            datetime.strptime(date_str, '%Y-%m-%d')
        
        # Simulação de resposta para o protótipo
        # Em um cenário real, você chamaria o método correspondente no serviço
        
        # Obter todas as datas no serviço de reconciliação
        all_dates = list(reconciliation_service.payments.keys())
        
        # Filtrar datas para o período 1
        period1_dates = [d for d in all_dates if d >= period1_start and d <= period1_end]
        
        # Filtrar datas para o período 2
        period2_dates = [d for d in all_dates if d >= period2_start and d <= period2_end]
        
        # Calcular dados agregados para o período 1
        period1_data = {
            'expected_amount': 0,
            'received_amount': 0,
            'difference': 0,
            'payment_methods': {
                'mastercard': 0,
                'visa': 0,
                'pix': 0,
                'boleto': 0
            },
            'transaction_count': 0
        }
        
        # Calcular dados agregados para o período 2
        period2_data = {
            'expected_amount': 0,
            'received_amount': 0,
            'difference': 0,
            'payment_methods': {
                'mastercard': 0,
                'visa': 0,
                'pix': 0,
                'boleto': 0
            },
            'transaction_count': 0
        }
        
        # Processar dados do período 1
        for date_key in period1_dates:
            payments = reconciliation_service.payments.get(date_key, [])
            
            # Filtrar por método de pagamento se especificado
            if payment_method and payment_method != 'all':
                payments = [p for p in payments if p.payment_method == payment_method]
            
            # Calcular valores
            period1_data['expected_amount'] += sum(reconciliation_service.expected_payments.get(date_key, {}).values())
            period1_data['received_amount'] += sum(p.amount for p in payments)
            period1_data['transaction_count'] += len(payments)
            
            # Calcular por método de pagamento
            period1_data['payment_methods']['mastercard'] += sum(p.amount for p in payments if p.payment_method == 'mastercard')
            period1_data['payment_methods']['visa'] += sum(p.amount for p in payments if p.payment_method == 'visa')
            period1_data['payment_methods']['pix'] += sum(p.amount for p in payments if p.payment_method == 'pix')
            period1_data['payment_methods']['boleto'] += sum(p.amount for p in payments if p.payment_method == 'boleto')
        
        # Processar dados do período 2
        for date_key in period2_dates:
            payments = reconciliation_service.payments.get(date_key, [])
            
            # Filtrar por método de pagamento se especificado
            if payment_method and payment_method != 'all':
                payments = [p for p in payments if p.payment_method == payment_method]
            
            # Calcular valores
            period2_data['expected_amount'] += sum(reconciliation_service.expected_payments.get(date_key, {}).values())
            period2_data['received_amount'] += sum(p.amount for p in payments)
            period2_data['transaction_count'] += len(payments)
            
            # Calcular por método de pagamento
            period2_data['payment_methods']['mastercard'] += sum(p.amount for p in payments if p.payment_method == 'mastercard')
            period2_data['payment_methods']['visa'] += sum(p.amount for p in payments if p.payment_method == 'visa')
            period2_data['payment_methods']['pix'] += sum(p.amount for p in payments if p.payment_method == 'pix')
            period2_data['payment_methods']['boleto'] += sum(p.amount for p in payments if p.payment_method == 'boleto')
        
        # Calcular diferenças
        period1_data['difference'] = period1_data['received_amount'] - period1_data['expected_amount']
        period2_data['difference'] = period2_data['received_amount'] - period2_data['expected_amount']
        
        return JSONResponse(
            status_code=200,
            content={
                'period1': {
                    'start_date': period1_start,
                    'end_date': period1_end,
                    'data': period1_data
                },
                'period2': {
                    'start_date': period2_start,
                    'end_date': period2_end,
                    'data': period2_data
                },
                'comparison': {
                    'expected_diff': period2_data['expected_amount'] - period1_data['expected_amount'],
                    'received_diff': period2_data['received_amount'] - period1_data['received_amount'],
                    'transaction_count_diff': period2_data['transaction_count'] - period1_data['transaction_count'],
                    'percentage_change': ((period2_data['received_amount'] / period1_data['received_amount']) - 1) * 100 if period1_data['received_amount'] > 0 else 0
                }
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Parâmetros inválidos: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao comparar períodos: {str(e)}"
        )

@app.get("/api/history/detail/{date}")
async def get_day_detail(date: str):
    """
    Obtém detalhes completos de um dia específico, incluindo transações e métodos de pagamento
    """
    try:
        # Validar data
        detail_date = datetime.strptime(date, '%Y-%m-%d').date()
        date_key = detail_date.isoformat()
        
        # Obter pagamentos da data
        payments = reconciliation_service.payments.get(date_key, [])
        
        if not payments:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum pagamento encontrado para a data {date}"
            )
        
        # Calcular valores
        expected_amount = sum(reconciliation_service.expected_payments.get(date_key, {}).values())
        received_amount = sum(p.amount for p in payments)
        difference = received_amount - expected_amount
        
        # Determinar status
        status = 'reconciled' if abs(difference) < 0.01 else ('pending' if received_amount < expected_amount else 'error')
        
        # Calcular métodos de pagamento
        payment_methods = {
            'mastercard': sum(p.amount for p in payments if p.payment_method == 'mastercard'),
            'visa': sum(p.amount for p in payments if p.payment_method == 'visa'),
            'pix': sum(p.amount for p in payments if p.payment_method == 'pix'),
            'boleto': sum(p.amount for p in payments if p.payment_method == 'boleto')
        }
        
        # Transformar pagamentos em formato de transações
        transactions = []
        for payment in payments:
            transactions.append({
                'id': payment.transaction_id,
                'method': payment.payment_method,
                'amount': payment.amount,
                'status': payment.status
            })
        
        return JSONResponse(
            status_code=200,
            content={
                'date': date_key,
                'expected_amount': expected_amount,
                'received_amount': received_amount,
                'difference': difference,
                'status': status,
                'payment_methods': payment_methods,
                'transactions': transactions
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Data inválida: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter detalhes do dia: {str(e)}"
        )

@app.get("/static/historico.html")
async def historia_page():
    """
    Retorna a página de histórico e análises
    """
    return FileResponse("app/static/historico.html") 