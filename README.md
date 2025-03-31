# Sistema de Conciliação Financeira Diária

Sistema para conciliação financeira diária de uma empresa de estacionamentos, que consolida e valida recebimentos provenientes de diferentes métodos de pagamento.

## Funcionalidades

- Importação de arquivos de gateways de pagamento (Mastercard e Visa)
- Importação de arquivos CNAB para pagamentos via boleto
- Importação de informações de pagamentos via PIX
- Reconciliação automática entre valores recebidos e vendas registradas
- Identificação e reporte de divergências

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```
3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

Para iniciar o servidor:
```bash
uvicorn app.main:app --reload
```

Acesse a interface web em: http://localhost:8000

## Estrutura do Projeto

```
financial-reconciliation/
├── app/
│   ├── main.py              # Aplicação FastAPI
│   ├── models/              # Modelos de dados
│   ├── services/            # Lógica de negócios
│   └── utils/               # Utilitários
├── tests/                   # Testes unitários
├── requirements.txt         # Dependências
└── README.md               # Documentação
``` 