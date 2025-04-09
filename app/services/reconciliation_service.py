from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
from app.models.payment import Payment, ReconciliationResult, Discrepancy
import logging
import os

logger = logging.getLogger(__name__)

class ReconciliationService:
    def __init__(self):
        self.payments: Dict[str, List[Payment]] = {}
        self.expected_payments: Dict[str, float] = {}

    def process_credit_card_file(self, file_path: str) -> List[Payment]:
        """
        Processa arquivo de vendas de cartão de crédito
        Format:
        order_id,payment_sequential,payment_type,payment_installments,payment_value
        """
        try:
            logger.info(f"Processando arquivo de cartão de crédito: {file_path}")
            
            # Tentar ler o arquivo como CSV com diferentes separadores
            try:
                df = pd.read_csv(file_path, sep=',')
            except:
                try:
                    df = pd.read_csv(file_path, sep='\t')
                except Exception as e:
                    raise ValueError(f"Erro ao ler arquivo CSV: {str(e)}")
            
            # Validar colunas obrigatórias
            required_columns = ['order_id', 'payment_sequential', 'payment_type', 'payment_installments', 'payment_value']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}")
            
            payments = []
            expected_payments_dict = {}  # Dicionário para armazenar valores esperados
            
            # Determinar bandeira do cartão baseado no primeiro dígito do order_id
            def get_card_brand(order_id: str) -> str:
                # Melhorar a determinação da bandeira para uma distribuição mais realista
                try:
                    first_digit = int(str(order_id)[0])
                    # Mastercard para dígitos 1, 3, 5, 7, 9 e Visa para 0, 2, 4, 6, 8
                    return 'mastercard' if first_digit % 2 == 1 else 'visa'
                except (ValueError, IndexError):
                    # Em caso de erro, alternativa padrão
                    return 'mastercard'
            
            for idx, row in df.iterrows():
                try:
                    # Validar tipo de pagamento
                    if str(row['payment_type']).lower() != 'credit_card':
                        logger.warning(f"Tipo de pagamento inválido na linha {idx + 2}: {row['payment_type']}")
                        continue
                    
                    # Validar valor do pagamento
                    try:
                        payment_value = float(row['payment_value'])
                        if payment_value <= 0:
                            logger.warning(f"Valor de pagamento inválido na linha {idx + 2}: {payment_value}")
                            continue
                    except ValueError:
                        logger.warning(f"Valor de pagamento inválido na linha {idx + 2}: {row['payment_value']}")
                        continue
                    
                    # Validar número de parcelas
                    try:
                        installments = int(row['payment_installments'])
                        if installments <= 0:
                            logger.warning(f"Número de parcelas inválido na linha {idx + 2}: {installments}")
                            continue
                    except ValueError:
                        logger.warning(f"Número de parcelas inválido na linha {idx + 2}: {row['payment_installments']}")
                        continue
                    
                    # Extrair data do arquivo ou usar data atual
                    payment_date = datetime.now().date()
                    date_key = payment_date.isoformat()
                    
                    # Determinar a bandeira do cartão
                    card_brand = get_card_brand(row['order_id'])
                    
                    # Criar objeto Payment
                    ticket_number = str(row['order_id'])[:8]  # Usando primeiros 8 caracteres como ticket
                    payment = Payment(
                        ticket_number=ticket_number,
                        amount=payment_value,
                        payment_type='credit_card',
                        payment_method=card_brand,  # Usando a bandeira determinada
                        installments=installments,
                        transaction_id=str(row['order_id']),
                        date=payment_date,
                        status='pending'  # Status inicial é 'pending'
                    )
                    payments.append(payment)
                    
                    # Adicionar ao dicionário de pagamentos por data
                    if date_key not in self.payments:
                        self.payments[date_key] = []
                    self.payments[date_key].append(payment)
                    
                    # Adicionar ao dicionário de valores esperados
                    if date_key not in expected_payments_dict:
                        expected_payments_dict[date_key] = {}
                    if ticket_number not in expected_payments_dict[date_key]:
                        expected_payments_dict[date_key][ticket_number] = payment_value
                    
                    logger.info(f"Pagamento processado com sucesso: {payment.transaction_id} ({card_brand})")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar linha {idx + 2}: {str(e)}")
                    continue
            
            if not payments:
                raise ValueError("Nenhum pagamento válido encontrado no arquivo")
            
            # Atualizar valores esperados no serviço
            for date_key, expected_values in expected_payments_dict.items():
                if date_key not in self.expected_payments:
                    self.expected_payments[date_key] = {}
                self.expected_payments[date_key].update(expected_values)
            
            logger.info(f"Total de pagamentos processados: {len(payments)}")
            logger.info(f"Valores esperados definidos para as datas: {list(expected_payments_dict.keys())}")
            
            return payments
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de cartão de crédito: {str(e)}")
            raise

    def process_cnab_file(self, file_path: str) -> List[Payment]:
        """
        Processa arquivo CNAB para pagamentos via boleto
        """
        try:
            # Implementar processamento do arquivo CNAB
            # Por enquanto retorna lista vazia
            return []
        except Exception as e:
            logger.error(f"Erro ao processar arquivo CNAB: {e}")
            raise

    def process_pix_file(self, file_path: str) -> List[Payment]:
        """
        Processa arquivo de extratos PIX
        """
        try:
            # Implementar processamento do arquivo PIX
            # Por enquanto retorna lista vazia
            return []
        except Exception as e:
            logger.error(f"Erro ao processar arquivo PIX: {e}")
            raise

    def set_expected_payments(self, expected_payments: Dict[str, float]):
        """
        Define os valores esperados para cada ticket
        """
        try:
            # Validar valores
            for ticket, amount in expected_payments.items():
                if amount < 0:
                    raise ValueError(f"Valor negativo não permitido para ticket {ticket}")
            
            self.expected_payments = expected_payments
        except Exception as e:
            logger.error(f"Erro ao definir valores esperados: {e}")
            raise

    def get_dashboard_data(self, date: datetime) -> Dict:
        """
        Retorna os dados do dashboard para uma data específica
        """
        try:
            # Converter para string ISO se for datetime, ou usar direto se for date
            date_key = date.isoformat() if hasattr(date, 'date') else date.isoformat()
            
            # Obter pagamentos da data
            payments = self.payments.get(date_key, [])
            
            # Calcular totais por método de pagamento
            payment_methods = {
                'mastercard': sum(p.amount for p in payments if p.payment_method == 'mastercard'),
                'visa': sum(p.amount for p in payments if p.payment_method == 'visa'),
                'pix': sum(p.amount for p in payments if p.payment_method == 'pix'),
                'boleto': sum(p.amount for p in payments if p.payment_method == 'boleto')
            }
            
            # Calcular totais esperados e recebidos
            expected_amount = sum(self.expected_payments.get(date_key, {}).values())
            received_amount = sum(p.amount for p in payments)
            difference = received_amount - expected_amount
            
            # Calcular status de conciliação
            total_payments = len(payments)
            if total_payments == 0:
                status_counts = {'reconciled': 0, 'pending': 0, 'error': 0}
                status_percentages = {'reconciled': 0, 'pending': 0, 'error': 0}
            else:
                reconciled = len([p for p in payments if p.status == 'reconciled'])
                pending = len([p for p in payments if p.status == 'pending'])
                error = len([p for p in payments if p.status == 'error'])
                
                status_counts = {
                    'reconciled': reconciled,
                    'pending': pending,
                    'error': error
                }
                
                status_percentages = {
                    'reconciled': round((reconciled / total_payments) * 100),
                    'pending': round((pending / total_payments) * 100),
                    'error': round((error / total_payments) * 100)
                }
            
            # Calcular totais por método de pagamento em percentual
            total_amount = sum(payment_methods.values())
            payment_methods_percentages = {
                method: round((amount / total_amount * 100) if total_amount > 0 else 0, 1)
                for method, amount in payment_methods.items()
            }
            
            return {
                'expected_amount': expected_amount,
                'received_amount': received_amount,
                'difference': difference,
                'status': 'reconciled' if difference == 0 else 'pending',
                'payment_methods': payment_methods,
                'payment_methods_percentages': payment_methods_percentages,
                'status_counts': status_counts,
                'status_percentages': status_percentages
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados do dashboard: {str(e)}")
            raise

    def get_transactions(self, date: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None, page: int = 1, page_size: int = 50) -> Tuple[List[Dict], int]:
        """
        Obtém a lista de transações com filtros opcionais e paginação
        """
        try:
            all_payments = []
            if date:
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    date_key = date_obj.date().isoformat()
                    all_payments = self.payments.get(date_key, [])
                except ValueError as e:
                    logger.error(f"Erro ao converter data: {e}")
                    raise ValueError(f"Formato de data inválido: {date}")
            else:
                for payments in self.payments.values():
                    all_payments.extend(payments)
            
            # Converter pagamentos para dicionários
            transactions = []
            for payment in all_payments:
                transaction = {
                    'id': payment.transaction_id,
                    'date': payment.date.isoformat(),
                    'location': 'Estacionamento Centro',
                    'method': payment.payment_method.title(),
                    'amount': float(payment.amount),
                    'status': payment.status.title()
                }
                
                # Aplicar filtros
                if status and status.lower() != 'todos':
                    if transaction['status'].lower() != status.lower():
                        continue
                
                if search:
                    search_lower = search.lower()
                    if not any(str(value).lower().find(search_lower) != -1 for value in transaction.values()):
                        continue
                
                transactions.append(transaction)
            
            # Calcular total antes da paginação
            total_items = len(transactions)
            
            # Aplicar paginação
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_transactions = transactions[start_idx:end_idx]
            
            logger.info(f"Retornando {len(paginated_transactions)} transações de um total de {total_items}")
            return paginated_transactions, total_items
            
        except Exception as e:
            logger.error(f"Erro ao obter transações: {e}")
            raise

    def export_transactions(self, date: datetime, format: str = "csv") -> str:
        """
        Exporta as transações de uma data específica
        """
        try:
            transactions = self.get_transactions(date.strftime("%Y-%m-%d"))
            
            if not transactions:
                raise ValueError("Nenhuma transação encontrada para exportar")
            
            # Criar DataFrame
            df = pd.DataFrame(transactions)
            
            # Criar diretório de exportação se não existir
            export_dir = "exports"
            os.makedirs(export_dir, exist_ok=True)
            
            # Gerar nome do arquivo
            file_name = f"transactions_{date.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}"
            
            if format == "csv":
                file_path = os.path.join(export_dir, f"{file_name}.csv")
                df.to_csv(file_path, index=False)
            elif format == "xlsx":
                file_path = os.path.join(export_dir, f"{file_name}.xlsx")
                df.to_excel(file_path, index=False)
            else:
                raise ValueError(f"Formato de exportação não suportado: {format}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Erro ao exportar transações: {e}")
            raise

    def reconcile_payments(self, date: datetime) -> dict:
        """
        Realiza a conciliação dos pagamentos para uma data específica
        """
        try:
            # Converter para string ISO se for datetime, ou usar direto se for date
            date_key = date.isoformat() if hasattr(date, 'date') else date.isoformat()
            
            # Obter pagamentos da data
            payments = self.payments.get(date_key, [])
            if not payments:
                raise ValueError("Nenhum pagamento encontrado para a data especificada")
            
            # Obter ou criar valores esperados
            if date_key not in self.expected_payments:
                # Se não houver valores esperados definidos, usar os valores dos pagamentos
                self.expected_payments[date_key] = {}
                for payment in payments:
                    if payment.ticket_number not in self.expected_payments[date_key]:
                        self.expected_payments[date_key][payment.ticket_number] = payment.amount
            
            expected = self.expected_payments[date_key]
            
            # Agrupar pagamentos por ticket
            payments_by_ticket = {}
            for payment in payments:
                if payment.ticket_number not in payments_by_ticket:
                    payments_by_ticket[payment.ticket_number] = []
                payments_by_ticket[payment.ticket_number].append(payment)
            
            # Realizar conciliação
            reconciled = []
            pending = []
            errors = []
            
            for ticket, ticket_payments in payments_by_ticket.items():
                expected_amount = expected.get(ticket, 0)
                received_amount = sum(p.amount for p in ticket_payments)
                
                if expected_amount == received_amount:
                    # Pagamento conciliado
                    for payment in ticket_payments:
                        payment.status = 'reconciled'
                    reconciled.append({
                        'ticket': ticket,
                        'amount': received_amount,
                        'status': 'reconciled'
                    })
                elif expected_amount > received_amount:
                    # Pagamento pendente
                    for payment in ticket_payments:
                        payment.status = 'pending'
                    pending.append({
                        'ticket': ticket,
                        'expected': expected_amount,
                        'received': received_amount,
                        'difference': expected_amount - received_amount,
                        'status': 'pending'
                    })
                else:
                    # Pagamento com erro (recebido maior que esperado)
                    for payment in ticket_payments:
                        payment.status = 'error'
                    errors.append({
                        'ticket': ticket,
                        'expected': expected_amount,
                        'received': received_amount,
                        'difference': received_amount - expected_amount,
                        'status': 'error'
                    })
            
            # Verificar tickets esperados que não foram recebidos
            for ticket, expected_amount in expected.items():
                if ticket not in payments_by_ticket:
                    pending.append({
                        'ticket': ticket,
                        'expected': expected_amount,
                        'received': 0,
                        'difference': expected_amount,
                        'status': 'pending'
                    })
            
            return {
                'date': date_key,
                'reconciled': reconciled,
                'pending': pending,
                'errors': errors,
                'summary': {
                    'total_tickets': len(set(list(payments_by_ticket.keys()) + list(expected.keys()))),
                    'reconciled_count': len(reconciled),
                    'pending_count': len(pending),
                    'error_count': len(errors)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao realizar conciliação: {str(e)}")
            raise

    def get_reconciliation_history(self, start_date: str = None, end_date: str = None, 
                                  payment_method: str = None, view_type: str = "daily") -> dict:
        """
        Obtém o histórico de conciliações para análise, com opções de filtro por período, método de pagamento e tipo de visualização
        """
        try:
            # Obter todas as datas no serviço de reconciliação
            all_dates = list(self.payments.keys())
            
            # Filtrar datas conforme start_date e end_date
            filtered_dates = all_dates
            if start_date:
                filtered_dates = [d for d in filtered_dates if d >= start_date]
            if end_date:
                filtered_dates = [d for d in filtered_dates if d <= end_date]
            
            # Construir resposta com dados filtrados
            history_items = []
            
            for date_key in filtered_dates:
                payments = self.payments.get(date_key, [])
                
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
                total_expected = sum(self.expected_payments.get(date_key, {}).values())
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
            
            return {
                'items': history_items,
                'total': len(history_items)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico de conciliações: {str(e)}")
            raise
    
    def compare_periods(self, period1_start: str, period1_end: str, 
                        period2_start: str, period2_end: str, payment_method: str = None) -> dict:
        """
        Compara dados de reconciliação entre dois períodos distintos
        """
        try:
            # Obter todas as datas no serviço de reconciliação
            all_dates = list(self.payments.keys())
            
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
                payments = self.payments.get(date_key, [])
                
                # Filtrar por método de pagamento se especificado
                if payment_method and payment_method != 'all':
                    payments = [p for p in payments if p.payment_method == payment_method]
                
                # Calcular valores
                period1_data['expected_amount'] += sum(self.expected_payments.get(date_key, {}).values())
                period1_data['received_amount'] += sum(p.amount for p in payments)
                period1_data['transaction_count'] += len(payments)
                
                # Calcular por método de pagamento
                period1_data['payment_methods']['mastercard'] += sum(p.amount for p in payments if p.payment_method == 'mastercard')
                period1_data['payment_methods']['visa'] += sum(p.amount for p in payments if p.payment_method == 'visa')
                period1_data['payment_methods']['pix'] += sum(p.amount for p in payments if p.payment_method == 'pix')
                period1_data['payment_methods']['boleto'] += sum(p.amount for p in payments if p.payment_method == 'boleto')
            
            # Processar dados do período 2
            for date_key in period2_dates:
                payments = self.payments.get(date_key, [])
                
                # Filtrar por método de pagamento se especificado
                if payment_method and payment_method != 'all':
                    payments = [p for p in payments if p.payment_method == payment_method]
                
                # Calcular valores
                period2_data['expected_amount'] += sum(self.expected_payments.get(date_key, {}).values())
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
            
            return {
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
            
        except Exception as e:
            logger.error(f"Erro ao comparar períodos: {str(e)}")
            raise
    
    def get_day_detail(self, date: datetime) -> dict:
        """
        Obtém detalhes completos de um dia específico, incluindo transações e métodos de pagamento
        """
        try:
            # Converter para string ISO
            date_key = date.isoformat()
            
            # Obter pagamentos da data
            payments = self.payments.get(date_key, [])
            
            if not payments:
                raise ValueError(f"Nenhum pagamento encontrado para a data {date}")
            
            # Calcular valores
            expected_amount = sum(self.expected_payments.get(date_key, {}).values())
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
            
            return {
                'date': date_key,
                'expected_amount': expected_amount,
                'received_amount': received_amount,
                'difference': difference,
                'status': status,
                'payment_methods': payment_methods,
                'transactions': transactions
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do dia: {str(e)}")
            raise 