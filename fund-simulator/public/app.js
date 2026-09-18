// 基金模拟交易系统前端

// 全局变量
let currentPortfolioId = 1;
let holdings = [];
let transactions = [];

// API基础URL
const API_BASE = '';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadDashboard();
    loadHoldings();
    loadTransactions();
    setupEventListeners();
    initializeCharts();
});

// 初始化应用
function initializeApp() {
    // 设置默认日期
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('buyDate').value = today;
    document.getElementById('sellDate').value = today;
    
    // 初始化投资组合
    initializePortfolio();
}

// 初始化投资组合
async function initializePortfolio() {
    try {
        const portfolios = await fetchAPI('/api/portfolios');
        if (portfolios.length === 0) {
            // 创建默认投资组合
            await fetchAPI('/api/portfolios', 'POST', {
                portfolio_name: '我的投资组合',
                initial_capital: 100000
            });
        }
        currentPortfolioId = portfolios[0]?.id || 1;
    } catch (error) {
        console.error('初始化投资组合失败:', error);
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 买入表单提交
    document.getElementById('buyForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleBuy();
    });
    
    // 卖出表单提交
    document.getElementById('sellForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleSell();
    });
    
    // 添加基金表单提交
    document.getElementById('addFundForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleAddFund();
    });
    
    // 导航链接点击
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('href');
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // 滚动到目标区域
            const element = document.querySelector(target);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// 加载仪表盘数据
async function loadDashboard() {
    try {
        const holdings = await fetchAPI(`/api/portfolios/${currentPortfolioId}/holdings`);
        
        // 计算总资产
        let totalAssets = 100000; // 初始资金
        let totalReturn = 0;
        
        holdings.forEach(holding => {
            totalAssets += holding.market_value - (holding.cost_price * holding.shares);
            totalReturn += holding.profit_loss;
        });
        
        // 更新仪表盘显示
        document.getElementById('totalAssets').textContent = formatCurrency(totalAssets);
        document.getElementById('totalReturn').textContent = formatCurrency(totalReturn);
        document.getElementById('holdingCount').textContent = holdings.length;
        
        // 模拟今日收益（实际应从API获取）
        const dailyReturn = totalReturn * 0.05; // 假设今日收益是总收益的5%
        document.getElementById('dailyReturn').textContent = formatCurrency(dailyReturn);
        
        // 更新资产配置图表
        updateAllocationChart(holdings);
        
    } catch (error) {
        console.error('加载仪表盘失败:', error);
    }
}

// 加载持仓数据
async function loadHoldings() {
    try {
        holdings = await fetchAPI(`/api/portfolios/${currentPortfolioId}/holdings`);
        renderHoldingsTable();
        updateSellFundDropdown();
    } catch (error) {
        console.error('加载持仓失败:', error);
    }
}

// 渲染持仓表格
function renderHoldingsTable() {
    const tbody = document.getElementById('holdingsTable');
    tbody.innerHTML = '';
    
    if (holdings.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-muted py-4">
                    暂无持仓，请先买入基金
                </td>
            </tr>
        `;
        return;
    }
    
    holdings.forEach(holding => {
        const row = document.createElement('tr');
        const profitClass = holding.profit_loss >= 0 ? 'profit' : 'loss';
        const profitSign = holding.profit_loss >= 0 ? '+' : '';
        
        row.innerHTML = `
            <td>${holding.fund_code}</td>
            <td>${holding.fund_name || '未知基金'}</td>
            <td>${formatNumber(holding.shares)}</td>
            <td>${formatCurrency(holding.cost_price)}</td>
            <td>${formatCurrency(holding.current_price)}</td>
            <td>${formatCurrency(holding.market_value)}</td>
            <td class="${profitClass}">${profitSign}${formatCurrency(holding.profit_loss)}</td>
            <td class="${profitClass}">${profitSign}${(holding.profit_loss_rate * 100).toFixed(2)}%</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewFundDetail('${holding.fund_code}')">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="sellFund('${holding.fund_code}')">
                    <i class="bi bi-cart-dash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// 更新卖出基金下拉列表
function updateSellFundDropdown() {
    const select = document.getElementById('sellFundCode');
    select.innerHTML = '<option value="">请选择持仓基金</option>';
    
    holdings.forEach(holding => {
        const option = document.createElement('option');
        option.value = holding.fund_code;
        option.textContent = `${holding.fund_code} - ${holding.fund_name || '未知基金'}`;
        select.appendChild(option);
    });
}

// 加载交易记录
async function loadTransactions() {
    try {
        transactions = await fetchAPI(`/api/portfolios/${currentPortfolioId}/transactions`);
        renderTransactionHistory();
    } catch (error) {
        console.error('加载交易记录失败:', error);
    }
}

// 渲染交易历史
function renderTransactionHistory() {
    const tbody = document.getElementById('transactionHistory');
    tbody.innerHTML = '';
    
    if (transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    暂无交易记录
                </td>
            </tr>
        `;
        return;
    }
    
    transactions.forEach(tx => {
        const row = document.createElement('tr');
        const typeClass = tx.transaction_type === 'BUY' ? 'text-success' : 'text-danger';
        const typeText = tx.transaction_type === 'BUY' ? '买入' : '卖出';
        
        row.innerHTML = `
            <td>${formatDate(tx.transaction_date)}</td>
            <td>${tx.fund_code} - ${tx.fund_name || '未知基金'}</td>
            <td class="${typeClass}">${typeText}</td>
            <td>${formatCurrency(tx.amount)}</td>
            <td>${formatNumber(tx.shares)}</td>
            <td>${formatCurrency(tx.fees)}</td>
        `;
        tbody.appendChild(row);
    });
}

// 处理买入操作
async function handleBuy() {
    const fundCode = document.getElementById('fundCode').value;
    const amount = parseFloat(document.getElementById('buyAmount').value);
    
    if (!fundCode || isNaN(amount) || amount <= 0) {
        showToast('请输入有效的基金代码和金额');
        return;
    }
    
    try {
        const result = await fetchAPI(`/api/portfolios/${currentPortfolioId}/buy`, 'POST', {
            fund_code: fundCode,
            amount: amount
        });
        
        showToast(`买入成功！份额: ${formatNumber(result.shares)}, 手续费: ${formatCurrency(result.fees)}`);
        
        // 刷新数据
        loadDashboard();
        loadHoldings();
        loadTransactions();
        
        // 清空表单
        document.getElementById('fundCode').value = '';
        document.getElementById('buyAmount').value = '';
        
    } catch (error) {
        showToast('买入失败: ' + error.message);
    }
}

// 处理卖出操作
async function handleSell() {
    const fundCode = document.getElementById('sellFundCode').value;
    const shares = parseFloat(document.getElementById('sellShares').value);
    
    if (!fundCode || isNaN(shares) || shares <= 0) {
        showToast('请选择基金并输入有效的份额');
        return;
    }
    
    // 检查持仓份额
    const holding = holdings.find(h => h.fund_code === fundCode);
    if (!holding || holding.shares < shares) {
        showToast('持仓份额不足');
        return;
    }
    
    try {
        // 这里需要后端实现卖出API
        showToast('卖出功能开发中...');
        
        // 刷新数据
        loadDashboard();
        loadHoldings();
        loadTransactions();
        
    } catch (error) {
        showToast('卖出失败: ' + error.message);
    }
}

// 处理添加基金
async function handleAddFund() {
    const fundCode = document.getElementById('newFundCode').value;
    const fundName = document.getElementById('newFundName').value;
    
    if (!fundCode || !fundName) {
        showToast('请输入基金代码和名称');
        return;
    }
    
    try {
        // 这里需要后端实现添加基金API
        showToast('添加基金功能开发中...');
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('addFundModal'));
        modal.hide();
        
    } catch (error) {
        showToast('添加基金失败: ' + error.message);
    }
}

// 查看基金详情
function viewFundDetail(fundCode) {
    showToast(`查看基金 ${fundCode} 详情功能开发中`);
}

// 卖出基金
function sellFund(fundCode) {
    document.getElementById('sellFundCode').value = fundCode;
    document.getElementById('sellShares').focus();
}

// 初始化图表
function initializeCharts() {
    // 资产走势图
    const assetCtx = document.getElementById('assetChart').getContext('2d');
    window.assetChart = new Chart(assetCtx, {
        type: 'line',
        data: {
            labels: generateDateLabels(30),
            datasets: [{
                label: '资产总值',
                data: generateRandomData(100000, 120000, 30),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '¥' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
    
    // 资产配置图
    const allocationCtx = document.getElementById('allocationChart').getContext('2d');
    window.allocationChart = new Chart(allocationCtx, {
        type: 'doughnut',
        data: {
            labels: ['股票型', '混合型', '债券型', '货币型', '其他'],
            datasets: [{
                data: [35, 25, 20, 15, 5],
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#f093fb',
                    '#f5576c',
                    '#4facfe'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    // 收益分析图
    const performanceCtx = document.getElementById('performanceChart').getContext('2d');
    window.performanceChart = new Chart(performanceCtx, {
        type: 'line',
        data: {
            labels: generateDateLabels(90),
            datasets: [
                {
                    label: '我的组合',
                    data: generateRandomData(100000, 130000, 90),
                    borderColor: '#667eea',
                    tension: 0.4
                },
                {
                    label: '沪深300',
                    data: generateRandomData(100000, 115000, 90),
                    borderColor: '#dc3545',
                    tension: 0.4,
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return '¥' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
    
    // 风险收益散点图
    const riskReturnCtx = document.getElementById('riskReturnChart').getContext('2d');
    window.riskReturnChart = new Chart(riskReturnCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: '基金',
                data: [
                    { x: 15, y: 12 },
                    { x: 20, y: 18 },
                    { x: 10, y: 8 },
                    { x: 25, y: 22 },
                    { x: 12, y: 10 }
                ],
                backgroundColor: '#667eea',
                pointRadius: 8,
                pointHoverRadius: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '年化波动率 (%)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '年化收益率 (%)'
                    }
                }
            }
        }
    });
}

// 更新资产配置图表
function updateAllocationChart(holdings) {
    if (!window.allocationChart) return;
    
    // 按基金类型分组
    const typeAllocation = {};
    holdings.forEach(holding => {
        const type = holding.fund_type || '其他';
        typeAllocation[type] = (typeAllocation[type] || 0) + holding.market_value;
    });
    
    const labels = Object.keys(typeAllocation);
    const data = Object.values(typeAllocation);
    
    window.allocationChart.data.labels = labels;
    window.allocationChart.data.datasets[0].data = data;
    window.allocationChart.update();
}

// 工具函数

// API请求封装
async function fetchAPI(url, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(API_BASE + url, options);
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '请求失败');
    }
    
    return response.json();
}

// 格式化货币
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '¥0.00';
    return '¥' + parseFloat(amount).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// 格式化数字
function formatNumber(number) {
    if (number === null || number === undefined) return '0';
    return parseFloat(number).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

// 生成日期标签
function generateDateLabels(days) {
    const labels = [];
    const today = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }));
    }
    
    return labels;
}

// 生成随机数据（用于演示）
function generateRandomData(min, max, count) {
    const data = [];
    let current = min;
    
    for (let i = 0; i < count; i++) {
        current += (Math.random() - 0.48) * (max - min) * 0.02;
        current = Math.max(min, Math.min(max, current));
        data.push(Math.round(current));
    }
    
    return data;
}

// 显示提示消息
function showToast(message) {
    const toastEl = document.getElementById('liveToast');
    const toastMessage = document.getElementById('toastMessage');
    toastMessage.textContent = message;
    
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// 计算风险指标（示例）
function calculateRiskMetrics() {
    // 这里应该从API获取真实数据计算
    return {
        volatility: 15.2,
        maxDrawdown: -8.5,
        sharpeRatio: 1.25,
        beta: 0.85,
        alpha: 2.3
    };
}

// 显示风险指标
function displayRiskMetrics() {
    const metrics = calculateRiskMetrics();
    const container = document.getElementById('riskMetrics');
    
    container.innerHTML = `
        <div class="row">
            <div class="col-6">
                <div class="mb-3">
                    <small class="text-muted">年化波动率</small>
                    <div class="h5 mb-0">${metrics.volatility}%</div>
                </div>
            </div>
            <div class="col-6">
                <div class="mb-3">
                    <small class="text-muted">最大回撤</small>
                    <div class="h5 mb-0 text-danger">${metrics.maxDrawdown}%</div>
                </div>
            </div>
            <div class="col-6">
                <div class="mb-3">
                    <small class="text-muted">夏普比率</small>
                    <div class="h5 mb-0">${metrics.sharpeRatio}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="mb-3">
                    <small class="text-muted">贝塔系数</small>
                    <div class="h5 mb-0">${metrics.beta}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="mb-3">
                    <small class="text-muted">阿尔法</small>
                    <div class="h5 mb-0 text-success">${metrics.alpha}%</div>
                </div>
            </div>
        </div>
    `;
}

// 页面加载完成后显示风险指标
document.addEventListener('DOMContentLoaded', function() {
    displayRiskMetrics();
});