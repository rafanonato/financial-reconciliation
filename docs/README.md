# FinanceSync Estacionamento - Documentação do Sistema

## Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [Modelos de Dados](#modelos-de-dados)
5. [Serviços](#serviços)
6. [API Endpoints](#api-endpoints)
7. [Interface do Usuário](#interface-do-usuário)
8. [Fluxo de Trabalho](#fluxo-de-trabalho)
9. [Configuração e Instalação](#configuração-e-instalação)
10. [Manutenção e Suporte](#manutenção-e-suporte)

## Visão Geral

O FinanceSync Estacionamento é um sistema de conciliação financeira desenvolvido para gerenciar e reconciliar pagamentos de estacionamentos. O sistema suporta múltiplos métodos de pagamento, incluindo cartões de crédito (Mastercard e Visa), PIX e boletos.

### Principais Funcionalidades
- Upload e processamento de arquivos de diferentes métodos de pagamento
- Dashboard com visão geral das transações
- Conciliação automática de pagamentos
- Exportação de relatórios
- Interface responsiva e intuitiva

## Arquitetura

O sistema é construído utilizando:
- **Backend**: FastAPI (Python 3.8+)
- **Frontend**: HTML5, CSS3, JavaScript
- **Processamento de Dados**: Pandas
- **Validação de Dados**: Pydantic
- **Armazenamento**: Em memória (com potencial para persistência)

### Componentes Principais
1. **API REST**: Endpoints para interação com o sistema
2. **Serviço de Reconciliação**: Lógica de negócio para processamento e conciliação
3. **Interface Web**: Dashboard e formulários de interação
4. **Processadores de Arquivo**: Módulos específicos para cada tipo de arquivo

## Estrutura do Projeto

```
financial-reconciliation/
├── app/
│   ├── main.py              # Aplicação FastAPI
│   │   ├── __init__.py
│   │   └── payment.py       # Modelos de dados
│   ├── services/
│   │   ├── __init__.py
│   │   └── reconciliation_service.py  # Serviço de reconciliação
│   └── static/
│       └── index.html       # Interface do usuário
├── docs/                    # Documentação
├── exports/                 # Arquivos exportados
└── requirements.txt         # Dependências
```

## Modelos de Dados

### Payment
```python
class Payment:
    ticket_number: str
    amount: float
    payment_type: str
    payment_method: str
    installments: int
    transaction_id: str
    date: date
    status: str
```

### ReconciliationResult
```python
class ReconciliationResult:
    date: str
    reconciled: List[Dict]
    pending: List[Dict]
    errors: List[Dict]
    summary: Dict
```

## Serviços

### ReconciliationService

#### Principais Métodos
1. **process_credit_card_file**
   - Processa arquivos CSV de cartão de crédito
   - Valida formato e dados
   - Determina bandeira do cartão
   - Cria objetos Payment

2. **get_dashboard_data**
   - Retorna dados consolidados para o dashboard
   - Calcula totais por método de pagamento
   - Gera estatísticas de conciliação

3. **get_transactions**
   - Lista transações com paginação
   - Suporta filtros por data, status e busca
   - Retorna dados formatados para exibição

4. **reconcile_payments**
   - Realiza conciliação de pagamentos
   - Compara valores esperados vs. recebidos
   - Atualiza status das transações

5. **export_transactions**
   - Exporta transações em CSV ou XLSX
   - Gera arquivos na pasta exports

## API Endpoints

### Transações
- `GET /api/transactions`
  - Lista transações com paginação
  - Parâmetros: date, status, search, page, page_size

### Dashboard
- `GET /api/dashboard/{date}`
  - Retorna dados do dashboard
  - Inclui totais e estatísticas

### Upload
- `POST /api/upload/credit-card`
  - Upload de arquivo de cartão de crédito
- `POST /api/upload/cnab`
  - Upload de arquivo CNAB (boleto)
- `POST /api/upload/pix`
  - Upload de arquivo PIX

### Conciliação
- `POST /api/reconcile`
  - Inicia processo de conciliação
  - Parâmetros: date

### Exportação
- `GET /api/export/{date}`
  - Exporta transações
  - Parâmetros: format (csv/xlsx)

## Interface do Usuário

### Componentes
1. **Dashboard**
   - Resumo diário
   - Gráfico de métodos de pagamento
   - Status de conciliação
   - Indicadores de performance

2. **Upload de Arquivos**
   - Seleção de tipo de arquivo
   - Upload com validação
   - Feedback de processamento

3. **Tabela de Transações**
   - Listagem paginada
   - Filtros e busca
   - Exportação de dados

### Funcionalidades JavaScript
- Atualização em tempo real
- Validação de formulários
- Formatação de valores
- Paginação dinâmica
- Filtros interativos

## Fluxo de Trabalho

1. **Upload de Arquivos**
   - Usuário seleciona tipo de arquivo
   - Sistema valida formato e conteúdo
   - Dados são processados e armazenados

2. **Conciliação**
   - Sistema compara valores esperados vs. recebidos
   - Status é atualizado automaticamente
   - Discrepâncias são identificadas

3. **Visualização**
   - Dashboard mostra resumo
   - Tabela lista transações
   - Filtros permitem análise detalhada

4. **Exportação**
   - Dados podem ser exportados
   - Formatos suportados: CSV, XLSX
   - Arquivos são salvos em /exports

## Configuração e Instalação

### Requisitos
- Python 3.8+
- Dependências listadas em requirements.txt

### Instalação
1. Clone o repositório
2. Crie ambiente virtual: `python -m venv venv`
3. Ative o ambiente: `source venv/bin/activate`
4. Instale dependências: `pip install -r requirements.txt`
5. Execute o servidor: `uvicorn app.main:app --reload`

### Configuração
- Porta padrão: 8000
- Host: 127.0.0.1
- Modo de desenvolvimento: --reload

## Manutenção e Suporte

### Logs
- Logs são gerados para operações importantes
- Níveis: INFO, WARNING, ERROR
- Incluem detalhes de erros e operações

### Tratamento de Erros
- Validação de entrada de dados
- Mensagens de erro amigáveis
- Logs detalhados para debugging

### Backup e Recuperação
- Dados são mantidos em memória
- Exportações podem ser usadas como backup
- Sistema pode ser reiniciado sem perda de dados

### Melhorias Futuras
1. Persistência de dados
2. Autenticação de usuários
3. Mais formatos de arquivo
4. Relatórios avançados
5. Integração com sistemas externos

---

© 2024 FinanceSync Estacionamento. Todos os direitos reservados. 