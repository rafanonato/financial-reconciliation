// Armazenamento local para os dados históricos
let historicalData = {};
let currentPage = 1;
let itemsPerPage = 10;
let filteredData = [];

// Configuração inicial quando o documento estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    initializeDateFilters();
    initializeCharts();
    initializeEventListeners();
    loadHistoricalData();
});

// Inicializar os filtros de data com valores padrão
function initializeDateFilters() {
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);
    
    document.getElementById('startDate').valueAsDate = oneMonthAgo;
    document.getElementById('endDate').valueAsDate = today;
    
    // Inicializar datas para comparação
    const twoMonthsAgo = new Date();
    twoMonthsAgo.setMonth(today.getMonth() - 2);
    
    document.getElementById('period1Start').valueAsDate = oneMonthAgo;
    document.getElementById('period1End').valueAsDate = today;
    document.getElementById('period2Start').valueAsDate = twoMonthsAgo;
    document.getElementById('period2End').valueAsDate = oneMonthAgo;
}

// Inicializar os gráficos vazios
function initializeCharts() {
    // Gráfico de evolução de receitas
    const revenueCtx = document.getElementById('revenueChart').getContext('2d');
    window.revenueChart = new Chart(revenueCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Valor Recebido',
                data: [],
                borderColor: 'rgba(75, 192, 192, 1)',
                tension: 0.1,
                fill: false
            }, {
                label: 'Valor Esperado',
                data: [],
                borderColor: 'rgba(153, 102, 255, 1)',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR');
                        }
                    }
                }
            }
        }
    });
    
    // Gráfico de distribuição de pagamentos
    const distributionCtx = document.getElementById('paymentDistributionChart').getContext('2d');
    window.distributionChart = new Chart(distributionCtx, {
        type: 'doughnut',
        data: {
            labels: ['Mastercard', 'Visa', 'PIX', 'Boleto'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
    
    // Gráfico por método de pagamento
    const methodCtx = document.getElementById('paymentMethodChart').getContext('2d');
    window.methodChart = new Chart(methodCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Mastercard',
                    data: [],
                    backgroundColor: 'rgba(255, 99, 132, 0.8)'
                },
                {
                    label: 'Visa',
                    data: [],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)'
                },
                {
                    label: 'PIX',
                    data: [],
                    backgroundColor: 'rgba(255, 206, 86, 0.8)'
                },
                {
                    label: 'Boleto',
                    data: [],
                    backgroundColor: 'rgba(75, 192, 192, 0.8)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR');
                        }
                    }
                }
            }
        }
    });
    
    // Gráfico por status
    const statusCtx = document.getElementById('statusChart').getContext('2d');
    window.statusChart = new Chart(statusCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Conciliado',
                    data: [],
                    borderColor: 'rgba(40, 167, 69, 1)',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true
                },
                {
                    label: 'Pendente',
                    data: [],
                    borderColor: 'rgba(255, 193, 7, 1)',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    fill: true
                },
                {
                    label: 'Erro',
                    data: [],
                    borderColor: 'rgba(220, 53, 69, 1)',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
    
    // Gráfico de comparação
    const comparisonCtx = document.getElementById('comparisonChart').getContext('2d');
    window.comparisonChart = new Chart(comparisonCtx, {
        type: 'bar',
        data: {
            labels: ['Valor Esperado', 'Valor Recebido', 'Diferença'],
            datasets: [
                {
                    label: 'Período 1',
                    data: [0, 0, 0],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)'
                },
                {
                    label: 'Período 2',
                    data: [0, 0, 0],
                    backgroundColor: 'rgba(255, 99, 132, 0.8)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR');
                        }
                    }
                }
            }
        }
    });
}

// Inicializar os listeners de eventos
function initializeEventListeners() {
    // Botão para aplicar filtros
    document.getElementById('applyFiltersBtn').addEventListener('click', function() {
        applyFilters();
    });
    
    // Botão para exportar relatório
    document.getElementById('exportReportBtn').addEventListener('click', function() {
        openExportModal();
    });
    
    // Botão para confirmar exportação
    document.getElementById('confirmExportBtn').addEventListener('click', function() {
        exportReport();
    });
    
    // Botão para comparar períodos
    document.getElementById('compareBtn').addEventListener('click', function() {
        comparePeriodsData();
    });
    
    // Botão para página anterior na tabela de histórico
    document.getElementById('prevPageBtn').addEventListener('click', function() {
        if (currentPage > 1) {
            currentPage--;
            renderHistoricalTable();
        }
    });
    
    // Botão para próxima página na tabela de histórico
    document.getElementById('nextPageBtn').addEventListener('click', function() {
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderHistoricalTable();
        }
    });
    
    // Seletor de tipo de visualização histórica
    document.getElementById('historicalViewSelect').addEventListener('change', function() {
        applyFilters();
    });
    
    // Exportar detalhes do dia
    document.getElementById('exportDayDetailsBtn').addEventListener('click', function() {
        exportDayDetails();
    });
}

// Formatar valor como moeda brasileira
function formatCurrency(value) {
    return 'R$ ' + value.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Formatar data no formato brasileiro
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR');
}

// Obter a classe de badge para o status
function getStatusBadgeClass(status) {
    const statusMap = {
        'reconciled': 'bg-success',
        'pending': 'bg-warning',
        'error': 'bg-danger',
        'conciliado': 'bg-success',
        'pendente': 'bg-warning',
        'erro': 'bg-danger'
    };
    return statusMap[status.toLowerCase()] || 'bg-secondary';
}

// Traduzir status para português
function translateStatus(status) {
    const translations = {
        'reconciled': 'Conciliado',
        'pending': 'Pendente',
        'error': 'Erro'
    };
    return translations[status.toLowerCase()] || status;
}

// Carregar dados históricos da API
async function loadHistoricalData() {
    try {
        // Neste exemplo, vamos gerar dados fictícios para simular dados históricos
        // Em um cenário real, você faria uma requisição para a API
        generateMockHistoricalData();
        
        // Aplicar filtros iniciais para exibir os dados
        applyFilters();
    } catch (error) {
        console.error('Erro ao carregar dados históricos:', error);
        alert('Erro ao carregar dados históricos. Por favor, tente novamente.');
    }
}

// Gerar dados históricos de exemplo (simulando API)
function generateMockHistoricalData() {
    const today = new Date();
    let currentDate = new Date();
    currentDate.setMonth(today.getMonth() - 12); // Dados dos últimos 12 meses
    
    // Métodos de pagamento disponíveis
    const paymentMethods = ['mastercard', 'visa', 'pix', 'boleto'];
    
    // Para cada dia no intervalo
    while (currentDate <= today) {
        const dateKey = currentDate.toISOString().split('T')[0];
        
        // Valores aleatórios para exemplo
        const expectedAmount = Math.random() * 50000 + 10000;
        const variance = (Math.random() - 0.5) * 2000; // Variação de até R$ 2.000 para mais ou para menos
        const receivedAmount = expectedAmount + variance;
        
        // Distribuição por método de pagamento
        const mastercardAmount = receivedAmount * (Math.random() * 0.3 + 0.2); // 20% a 50%
        const visaAmount = receivedAmount * (Math.random() * 0.3 + 0.1); // 10% a 40%
        const pixAmount = receivedAmount * (Math.random() * 0.2 + 0.1); // 10% a 30%
        const boletoAmount = receivedAmount - mastercardAmount - visaAmount - pixAmount;
        
        // Status baseado na diferença
        let status;
        if (Math.abs(expectedAmount - receivedAmount) < 0.01) {
            status = 'reconciled';
        } else if (receivedAmount < expectedAmount) {
            status = 'pending';
        } else {
            status = 'error';
        }
        
        // Criando transações simuladas
        const transactionCount = Math.floor(Math.random() * 20) + 5; // 5 a 25 transações
        const transactions = [];
        
        for (let i = 0; i < transactionCount; i++) {
            const method = paymentMethods[Math.floor(Math.random() * paymentMethods.length)];
            let amount;
            
            // Distribuir valores de acordo com o método
            switch (method) {
                case 'mastercard':
                    amount = mastercardAmount / (transactionCount / 2) * (Math.random() + 0.5);
                    break;
                case 'visa':
                    amount = visaAmount / (transactionCount / 3) * (Math.random() + 0.5);
                    break;
                case 'pix':
                    amount = pixAmount / (transactionCount / 4) * (Math.random() + 0.5);
                    break;
                case 'boleto':
                    amount = boletoAmount / (transactionCount / 4) * (Math.random() + 0.5);
                    break;
            }
            
            // Criar transação
            transactions.push({
                id: 'TRANS' + Math.floor(Math.random() * 1000000),
                method: method,
                amount: amount,
                status: status
            });
        }
        
        // Armazenar dados do dia
        historicalData[dateKey] = {
            date: dateKey,
            expected_amount: expectedAmount,
            received_amount: receivedAmount,
            difference: receivedAmount - expectedAmount,
            status: status,
            payment_methods: {
                mastercard: mastercardAmount,
                visa: visaAmount,
                pix: pixAmount,
                boleto: boletoAmount
            },
            transactions: transactions
        };
        
        // Avançar para o próximo dia
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    console.log(`Gerados dados históricos para ${Object.keys(historicalData).length} dias`);
}

// Aplicar filtros e atualizar visualizações
function applyFilters() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const paymentMethod = document.getElementById('paymentMethodSelect').value;
    const viewType = document.getElementById('viewTypeSelect').value;
    
    if (!startDate || !endDate) {
        alert('Por favor, selecione datas válidas para filtrar os dados.');
        return;
    }
    
    // Filtrar dados pelo intervalo de datas e método de pagamento
    filteredData = Object.values(historicalData).filter(data => {
        const dataDate = data.date;
        return dataDate >= startDate && dataDate <= endDate;
    });
    
    // Se um método de pagamento específico for selecionado
    if (paymentMethod !== 'all') {
        filteredData = filteredData.filter(data => {
            return data.payment_methods[paymentMethod] > 0;
        });
    }
    
    // Agrupar dados conforme o tipo de visualização
    const groupedData = groupDataByViewType(filteredData, viewType);
    
    // Atualizar visualizações
    updateDashboard(groupedData);
    updateCharts(groupedData, viewType);
    
    // Resetar paginação e renderizar tabela
    currentPage = 1;
    renderHistoricalTable();
}

// Agrupar dados pelo tipo de visualização (diário, mensal, anual)
function groupDataByViewType(data, viewType) {
    if (viewType === 'daily') {
        // Para visualização diária, não precisamos agrupar
        return data;
    } else {
        // Para visualização mensal ou anual, agrupamos os dados
        const grouped = {};
        
        data.forEach(item => {
            let key;
            
            if (viewType === 'monthly') {
                // Formato YYYY-MM para mensal
                key = item.date.substring(0, 7);
            } else { // 'yearly'
                // Formato YYYY para anual
                key = item.date.substring(0, 4);
            }
            
            if (!grouped[key]) {
                grouped[key] = {
                    date: key,
                    expected_amount: 0,
                    received_amount: 0,
                    difference: 0,
                    payment_methods: {
                        mastercard: 0,
                        visa: 0,
                        pix: 0,
                        boleto: 0
                    },
                    transactions: [],
                    days: 0
                };
            }
            
            // Somar os valores
            grouped[key].expected_amount += item.expected_amount;
            grouped[key].received_amount += item.received_amount;
            grouped[key].difference += item.difference;
            grouped[key].payment_methods.mastercard += item.payment_methods.mastercard;
            grouped[key].payment_methods.visa += item.payment_methods.visa;
            grouped[key].payment_methods.pix += item.payment_methods.pix;
            grouped[key].payment_methods.boleto += item.payment_methods.boleto;
            grouped[key].transactions = grouped[key].transactions.concat(item.transactions);
            grouped[key].days += 1;
        });
        
        // Determinar o status baseado na diferença agregada
        Object.values(grouped).forEach(item => {
            if (Math.abs(item.difference) < 0.01) {
                item.status = 'reconciled';
            } else if (item.received_amount < item.expected_amount) {
                item.status = 'pending';
            } else {
                item.status = 'error';
            }
        });
        
        return Object.values(grouped);
    }
}

// Atualizar o dashboard com os dados filtrados
function updateDashboard(data) {
    // Calcular totais
    const totalExpected = data.reduce((sum, item) => sum + item.expected_amount, 0);
    const totalReceived = data.reduce((sum, item) => sum + item.received_amount, 0);
    const totalTransactions = data.reduce((sum, item) => sum + item.transactions.length, 0);
    const totalDays = data.reduce((sum, item) => sum + (item.days || 1), 0);
    const dailyAverage = totalReceived / totalDays;
    
    // Calcular discrepâncias (transações com erro)
    const totalDiscrepancies = data.filter(item => item.status === 'error').length;
    
    // Atualizar elementos da interface
    document.getElementById('totalReconciled').textContent = formatCurrency(totalReceived);
    document.getElementById('totalTransactions').textContent = totalTransactions.toLocaleString('pt-BR');
    document.getElementById('dailyAverage').textContent = formatCurrency(dailyAverage);
    document.getElementById('totalDiscrepancies').textContent = totalDiscrepancies.toLocaleString('pt-BR');
}

// Atualizar os gráficos com os dados filtrados
function updateCharts(data, viewType) {
    // Ordenar dados por data
    data.sort((a, b) => a.date.localeCompare(b.date));
    
    // Formatar labels baseado no tipo de visualização
    const labels = data.map(item => {
        if (viewType === 'daily') {
            return formatDate(item.date);
        } else if (viewType === 'monthly') {
            const [year, month] = item.date.split('-');
            return `${month}/${year}`;
        } else { // 'yearly'
            return item.date;
        }
    });
    
    // Atualizar gráfico de evolução de receitas
    window.revenueChart.data.labels = labels;
    window.revenueChart.data.datasets[0].data = data.map(item => item.received_amount);
    window.revenueChart.data.datasets[1].data = data.map(item => item.expected_amount);
    window.revenueChart.update();
    
    // Calcular totais por método de pagamento
    const mastercard = data.reduce((sum, item) => sum + item.payment_methods.mastercard, 0);
    const visa = data.reduce((sum, item) => sum + item.payment_methods.visa, 0);
    const pix = data.reduce((sum, item) => sum + item.payment_methods.pix, 0);
    const boleto = data.reduce((sum, item) => sum + item.payment_methods.boleto, 0);
    
    // Atualizar gráfico de distribuição de pagamentos
    window.distributionChart.data.datasets[0].data = [mastercard, visa, pix, boleto];
    window.distributionChart.update();
    
    // Atualizar gráfico por método de pagamento
    window.methodChart.data.labels = labels;
    window.methodChart.data.datasets[0].data = data.map(item => item.payment_methods.mastercard);
    window.methodChart.data.datasets[1].data = data.map(item => item.payment_methods.visa);
    window.methodChart.data.datasets[2].data = data.map(item => item.payment_methods.pix);
    window.methodChart.data.datasets[3].data = data.map(item => item.payment_methods.boleto);
    window.methodChart.update();
    
    // Calcular percentuais por status para cada período
    const reconciledPercentages = data.map(item => {
        const reconciledCount = item.transactions.filter(t => t.status === 'reconciled').length;
        return reconciledCount / item.transactions.length * 100 || 0;
    });
    
    const pendingPercentages = data.map(item => {
        const pendingCount = item.transactions.filter(t => t.status === 'pending').length;
        return pendingCount / item.transactions.length * 100 || 0;
    });
    
    const errorPercentages = data.map(item => {
        const errorCount = item.transactions.filter(t => t.status === 'error').length;
        return errorCount / item.transactions.length * 100 || 0;
    });
    
    // Atualizar gráfico por status
    window.statusChart.data.labels = labels;
    window.statusChart.data.datasets[0].data = reconciledPercentages;
    window.statusChart.data.datasets[1].data = pendingPercentages;
    window.statusChart.data.datasets[2].data = errorPercentages;
    window.statusChart.update();
}

// Renderizar a tabela de histórico com os dados filtrados
function renderHistoricalTable() {
    const tbody = document.getElementById('historicalTableBody');
    tbody.innerHTML = '';
    
    const viewType = document.getElementById('historicalViewSelect').value;
    
    // Calcular índices para paginação
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredData.length);
    
    // Renderizar cada linha com os dados
    for (let i = startIndex; i < endIndex; i++) {
        const item = filteredData[i];
        const row = document.createElement('tr');
        
        // Formatar a data conforme o tipo de visualização
        let displayDate;
        if (viewType === 'daily') {
            displayDate = formatDate(item.date);
        } else if (viewType === 'monthly') {
            const [year, month] = item.date.split('-');
            displayDate = `${month}/${year}`;
        } else { // 'yearly'
            displayDate = item.date;
        }
        
        // Criar as células da linha
        row.innerHTML = `
            <td>${displayDate}</td>
            <td>${formatCurrency(item.expected_amount)}</td>
            <td>${formatCurrency(item.received_amount)}</td>
            <td class="${item.difference < 0 ? 'text-danger' : 'text-success'}">${formatCurrency(item.difference)}</td>
            <td>
                <span class="badge ${getStatusBadgeClass(item.status)}">
                    ${translateStatus(item.status)}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="showDayDetail('${item.date}')">
                    <i class="bi bi-eye"></i> Detalhes
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    }
    
    // Atualizar informações de paginação
    const paginationInfo = document.getElementById('paginationInfo');
    if (filteredData.length === 0) {
        paginationInfo.textContent = 'Nenhum registro encontrado';
    } else {
        paginationInfo.textContent = `Mostrando ${startIndex + 1}-${endIndex} de ${filteredData.length} registros`;
    }
    
    // Atualizar estado dos botões de paginação
    document.getElementById('prevPageBtn').classList.toggle('disabled', currentPage === 1);
    document.getElementById('nextPageBtn').classList.toggle('disabled', endIndex >= filteredData.length);
}

// Mostrar detalhes de um dia específico
function showDayDetail(date) {
    const data = historicalData[date];
    if (!data) {
        alert('Dados não encontrados para esta data.');
        return;
    }
    
    // Preencher informações no modal
    document.getElementById('detailDate').textContent = formatDate(date);
    document.getElementById('detailExpected').textContent = formatCurrency(data.expected_amount);
    document.getElementById('detailReceived').textContent = formatCurrency(data.received_amount);
    document.getElementById('detailDifference').textContent = formatCurrency(data.difference);
    document.getElementById('detailStatus').textContent = translateStatus(data.status);
    
    // Preencher tabela de transações
    const tbody = document.getElementById('detailTransactions');
    tbody.innerHTML = '';
    
    data.transactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${transaction.id}</td>
            <td>${transaction.method.charAt(0).toUpperCase() + transaction.method.slice(1)}</td>
            <td>${formatCurrency(transaction.amount)}</td>
            <td>
                <span class="badge ${getStatusBadgeClass(transaction.status)}">
                    ${translateStatus(transaction.status)}
                </span>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // Renderizar gráfico de distribuição por método
    renderDetailMethodChart(data);
    
    // Mostrar o modal
    const detailModal = new bootstrap.Modal(document.getElementById('dayDetailModal'));
    detailModal.show();
}

// Renderizar gráfico de distribuição por método para um dia específico
function renderDetailMethodChart(data) {
    // Destruir o gráfico anterior se existir
    if (window.detailMethodChart) {
        window.detailMethodChart.destroy();
    }
    
    // Criar novo gráfico
    const ctx = document.getElementById('detailMethodChart').getContext('2d');
    window.detailMethodChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Mastercard', 'Visa', 'PIX', 'Boleto'],
            datasets: [{
                data: [
                    data.payment_methods.mastercard,
                    data.payment_methods.visa,
                    data.payment_methods.pix,
                    data.payment_methods.boleto
                ],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Comparar dados entre dois períodos
function comparePeriodsData() {
    const period1Start = document.getElementById('period1Start').value;
    const period1End = document.getElementById('period1End').value;
    const period2Start = document.getElementById('period2Start').value;
    const period2End = document.getElementById('period2End').value;
    
    if (!period1Start || !period1End || !period2Start || !period2End) {
        alert('Por favor, selecione datas válidas para ambos os períodos.');
        return;
    }
    
    // Filtar dados para o período 1
    const period1Data = Object.values(historicalData).filter(data => {
        return data.date >= period1Start && data.date <= period1End;
    });
    
    // Filtrar dados para o período 2
    const period2Data = Object.values(historicalData).filter(data => {
        return data.date >= period2Start && data.date <= period2End;
    });
    
    // Calcular totais para o período 1
    const period1Expected = period1Data.reduce((sum, item) => sum + item.expected_amount, 0);
    const period1Received = period1Data.reduce((sum, item) => sum + item.received_amount, 0);
    const period1Difference = period1Received - period1Expected;
    
    // Calcular totais para o período 2
    const period2Expected = period2Data.reduce((sum, item) => sum + item.expected_amount, 0);
    const period2Received = period2Data.reduce((sum, item) => sum + item.received_amount, 0);
    const period2Difference = period2Received - period2Expected;
    
    // Gerar labels para os períodos
    const period1Label = `${formatDate(period1Start)} a ${formatDate(period1End)}`;
    const period2Label = `${formatDate(period2Start)} a ${formatDate(period2End)}`;
    
    // Atualizar o gráfico de comparação
    window.comparisonChart.data.datasets[0].label = period1Label;
    window.comparisonChart.data.datasets[1].label = period2Label;
    
    window.comparisonChart.data.datasets[0].data = [period1Expected, period1Received, period1Difference];
    window.comparisonChart.data.datasets[1].data = [period2Expected, period2Received, period2Difference];
    
    window.comparisonChart.update();
}

// Abrir modal de exportação de relatório
function openExportModal() {
    const exportModal = new bootstrap.Modal(document.getElementById('exportModal'));
    exportModal.show();
}

// Exportar relatório com base nas configurações selecionadas
function exportReport() {
    const reportType = document.getElementById('reportTypeSelect').value;
    const reportFormat = document.getElementById('reportFormatSelect').value;
    const includeCharts = document.getElementById('includeChartsCheck').checked;
    
    // Aqui você faria a chamada para a API para gerar o relatório
    // Para este exemplo, vamos simular o download
    
    let message;
    switch(reportType) {
        case 'summary':
            message = `Exportando relatório de resumo do período em formato ${reportFormat.toUpperCase()}`;
            break;
        case 'detailed':
            message = `Exportando relatório detalhado por dia em formato ${reportFormat.toUpperCase()}`;
            break;
        case 'comparative':
            message = `Exportando relatório comparativo em formato ${reportFormat.toUpperCase()}`;
            break;
    }
    
    alert(`${message}\n${includeCharts ? 'Incluindo gráficos' : 'Sem gráficos'}`);
    
    // Fechar o modal
    bootstrap.Modal.getInstance(document.getElementById('exportModal')).hide();
}

// Exportar detalhes de um dia específico
function exportDayDetails() {
    const date = document.getElementById('detailDate').textContent;
    alert(`Exportando detalhes do dia ${date}`);
}

// Chamada inicial para carregar a tabela quando a página carregar
renderHistoricalTable(); 