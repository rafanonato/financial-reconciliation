from datetime import datetime
from typing import List, Dict, Optional
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
                    
                    # Criar objeto Payment
                    payment = Payment(
                        ticket_number=str(row['order_id'])[:8],  # Usando primeiros 8 caracteres como ticket
                        amount=payment_value,
                        payment_type='credit_card',
                        payment_method='credit_card',
                        installments=installments,
                        transaction_id=str(row['order_id']),
                        date=datetime.now().date()  # Data atual como padrão
                    )
                    payments.append(payment)
                    
                    # Adicionar ao dicionário de pagamentos por data
                    date_key = payment.date.isoformat()
                    if date_key not in self.payments:
                        self.payments[date_key] = []
                    self.payments[date_key].append(payment)
                    
                    logger.info(f"Pagamento processado com sucesso: {payment.transaction_id}")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar linha {idx + 2}: {str(e)}")
                    continue
            
            if not payments:
                raise ValueError("Nenhum pagamento válido encontrado no arquivo")
            
            logger.info(f"Total de pagamentos processados: {len(payments)}")
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
        Obtém os dados do dashboard para uma data específica
        """
        try:
            date_key = date.date().isoformat()
            received_payments = self.payments.get(date_key, [])
            
            # Calcular totais por método de pagamento
            payment_methods = {
                'mastercard': 0,
                'visa': 0,
                'pix': 0,
                'boleto': 0
            }
            
            for payment in received_payments:
                if payment.payment_method == 'credit_card':
                    # Aqui você pode adicionar lógica para diferenciar Mastercard e Visa
                    payment_methods['mastercard'] += payment.amount
                elif payment.payment_method == 'pix':
                    payment_methods['pix'] += payment.amount
                elif payment.payment_method == 'boleto':
                    payment_methods['boleto'] += payment.amount
            
            # Calcular status das transações
            status_counts = {
                'conciliado': 0,
                'pendente': 0,
                'erro': 0
            }
            
            total_transactions = len(received_payments)
            if total_transactions > 0:
                # Aqui você pode adicionar lógica para determinar o status de cada transação
                status_counts['conciliado'] = sum(1 for p in received_payments if p.amount > 0)  # Exemplo
                status_counts['pendente'] = sum(1 for p in received_payments if p.amount == 0)  # Exemplo
                status_counts['erro'] = total_transactions - status_counts['conciliado'] - status_counts['pendente']
            
            return {
                'summary': {
                    'expected': sum(self.expected_payments.values()),
                    'received': sum(p.amount for p in received_payments),
                    'difference': sum(self.expected_payments.values()) - sum(p.amount for p in received_payments),
                    'status': 'PENDENTE'  # Você pode adicionar lógica para determinar o status
                },
                'payment_methods': payment_methods,
                'status_counts': status_counts
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados do dashboard: {e}")
            raise

    def get_transactions(self, date: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None) -> List[Dict]:
        """
        Obtém a lista de transações com filtros opcionais
        """
        try:
            all_payments = []
            if date:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                date_key = date_obj.date().isoformat()
                all_payments = self.payments.get(date_key, [])
            else:
                for payments in self.payments.values():
                    all_payments.extend(payments)
            
            # Converter pagamentos para dicionários
            transactions = []
            for payment in all_payments:
                transaction = {
                    'id': payment.transaction_id,
                    'date': payment.date.strftime("%d/%m/%Y"),
                    'location': 'Estacionamento Centro',  # Você pode adicionar lógica para determinar o local
                    'method': payment.payment_method,
                    'amount': payment.amount,
                    'status': 'pendente'  # Você pode adicionar lógica para determinar o status
                }
                
                # Aplicar filtros
                if status and transaction['status'] != status:
                    continue
                
                if search:
                    search_lower = search.lower()
                    if not any(str(value).lower().find(search_lower) != -1 for value in transaction.values()):
                        continue
                
                transactions.append(transaction)
            
            return transactions
            
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

    def reconcile_payments(self, date: datetime) -> ReconciliationResult:
        """
        Realiza a conciliação dos pagamentos para uma data específica
        """
        try:
            date_key = date.date().isoformat()
            received_payments = self.payments.get(date_key, [])
            
            # Calcular totais
            total_expected = sum(self.expected_payments.values())
            total_received = sum(payment.amount for payment in received_payments)
            
            # Identificar discrepâncias
            discrepancies = []
            
            # Verificar pagamentos recebidos vs esperados
            for payment in received_payments:
                expected_amount = self.expected_payments.get(payment.ticket_number)
                if expected_amount is None:
                    discrepancies.append(Discrepancy(
                        description=f"Ticket {payment.ticket_number} recebido mas não estava na lista de esperados",
                        difference=payment.amount
                    ))
                elif abs(expected_amount - payment.amount) > 0.01:  # Tolerância de 1 centavo
                    discrepancies.append(Discrepancy(
                        description=f"Valor divergente para ticket {payment.ticket_number}",
                        difference=payment.amount - expected_amount
                    ))
            
            # Verificar pagamentos esperados não recebidos
            for ticket, expected_amount in self.expected_payments.items():
                if not any(p.ticket_number == ticket for p in received_payments):
                    discrepancies.append(Discrepancy(
                        description=f"Ticket {ticket} esperado mas não recebido",
                        difference=-expected_amount
                    ))
            
            # Determinar status
            if len(discrepancies) == 0:
                status = "CONCILIADO"
            else:
                status = "DIVERGENTE"
            
            return ReconciliationResult(
                status=status,
                total_expected=total_expected,
                total_received=total_received,
                discrepancies=discrepancies
            )
            
        except Exception as e:
            logger.error(f"Erro ao realizar conciliação: {e}")
            raise 