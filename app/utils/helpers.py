from datetime import datetime
from typing import List, Dict
import pandas as pd

def validate_date_format(date_str: str) -> bool:
    """
    Valida se a string de data está no formato correto (YYYY-MM-DD)
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def calculate_total_amount(payments: List[Dict]) -> float:
    """
    Calcula o valor total de uma lista de pagamentos
    """
    return sum(payment.get('amount', 0) for payment in payments)

def format_currency(value: float) -> str:
    """
    Formata um valor numérico como moeda brasileira
    """
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Valida se a extensão do arquivo está na lista de extensões permitidas
    """
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)

def read_excel_file(file_path: str) -> pd.DataFrame:
    """
    Lê um arquivo Excel e retorna um DataFrame
    """
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        raise Exception(f"Erro ao ler arquivo Excel: {str(e)}")

def read_csv_file(file_path: str, separator: str = '\t') -> pd.DataFrame:
    """
    Lê um arquivo CSV e retorna um DataFrame
    """
    try:
        return pd.read_csv(file_path, sep=separator)
    except Exception as e:
        raise Exception(f"Erro ao ler arquivo: {str(e)}")

def validate_required_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Valida se todas as colunas necessárias estão presentes no DataFrame
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}")
    return True 