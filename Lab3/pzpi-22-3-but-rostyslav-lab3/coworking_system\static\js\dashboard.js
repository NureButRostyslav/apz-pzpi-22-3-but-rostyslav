document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

    // Fetch and display expenses
    const expenseTable = document.getElementById('expense-table');
    const expenseFilter = document.getElementById('expense-filter');
    const expenseChart = document.getElementById('expenseChart').getContext('2d');
    let chartInstance;

    async function fetchExpenses(params = {}) {
        const query = new URLSearchParams(params).toString();
        const response = await fetch(`/api/expenses/?${query}`, { headers });
        const data = await response.json();
        expenseTable.innerHTML = '';
        data.forEach(expense => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${expense.user}</td>
                <td>${expense.resource}</td>
                <td>${moment(expense.start_time).format('LLL')}</td>
                <td>${moment(expense.end_time).format('LLL')}</td>
                <td>${expense.total_cost.toFixed(2)}</td>
                <td><button onclick="deleteExpense(${expense.id})">{% trans "Delete" %}</button></td>
            `;
            expenseTable.appendChild(row);
        });

        // Update chart
        const labels = data.map(e => e.resource);
        const costs = data.map(e => e.total_cost);
        if (chartInstance) chartInstance.destroy();
        chartInstance = new Chart(expenseChart, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: '{% trans "Total Cost" %}',
                        data: costs,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                scales: { y: { beginAtZero: true } },
                plugins: { legend: { display: true } }
            }
        });
    }

    expenseFilter.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(expenseFilter);
        const params = Object.fromEntries(formData);
        await fetchExpenses(params);
    });

    // Download PDF report
    document.getElementById('download-pdf').addEventListener('click', () => {
        const element = document.getElementById('expenses');
        html2pdf().set({
            margin: 1,
            filename: 'expense_report.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
        }).from(element).save();
    });

    // Export to CSV
    document.getElementById('export-csv').addEventListener('click', async () => {
        const response = await fetch('/api/expenses/', { headers });
        const data = await response.json();
        const csv = [
            'User,Resource,Start Time,End Time,Total Cost',
            ...data.map(e => `${e.user},${e.resource},${e.start_time},${e.end_time},${e.total_cost}`)
        ].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'expenses.csv';
        a.click();
        URL.revokeObjectURL(url);
    });

    // Delete expense
    window.deleteExpense = async (id) => {
        if (confirm('{% trans "Are you sure you want to delete this expense?" %}')) {
            await fetch(`/api/expenses/${id}/`, { method: 'DELETE', headers });
            await fetchExpenses();
        }
    };

    // Manage budgets
    const budgetForm = document.getElementById('budget-form');
    const budgetTable = document.getElementById('budget-table');
    if (budgetForm) {
        budgetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(budgetForm);
            const data = Object.fromEntries(formData);
            await fetch('/api/budgets/', {
                method: 'POST',
                headers,
                body: JSON.stringify(data)
            });
            alert('{% trans "Budget saved successfully" %}');
            fetchBudgets();
        });

        async function fetchBudgets() {
            const response = await fetch('/api/budgets/', { headers });
            const data = await response.json();
            budgetTable.innerHTML = '';
            data.forEach(budget => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${budget.corporate_account_id}</td>
                    <td>${budget.limit_amount.toFixed(2)}</td>
                    <td>${budget.start_date || '-'}</td>
                    <td>${budget.end_date || '-'}</td>
                    <td><button onclick="deleteBudget(${budget.id})">{% trans "Delete" %}</button></td>
                `;
                budgetTable.appendChild(row);
            });
        }
        fetchBudgets();
    }

    // Delete budget
    window.deleteBudget = async (id) => {
        if (confirm('{% trans "Are you sure you want to delete this budget?" %}')) {
            await fetch(`/api/budgets/${id}/`, { method: 'DELETE', headers });
            fetchBudgets();
        }
    };

    // Manage limits
    const limitForm = document.getElementById('limit-form');
    const limitTable = document.getElementById('limit-table');
    if (limitForm) {
        limitForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(limitForm);
            const data = Object.fromEntries(formData);
            await fetch('/api/limits/', {
                method: 'POST',
                headers,
                body: JSON.stringify(data)
            });
            alert('{% trans "Limit set successfully" %}');
            fetchLimits();
        });

        async function fetchLimits() {
            const response = await fetch('/api/limits/', { headers });
            const data = await response.json();
            limitTable.innerHTML = '';
            data.forEach(limit => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${limit.user}</td>
                    <td>${limit.limit_amount.toFixed(2)}</td>
                    <td>${limit.category || '-'}</td>
                    <td><button onclick="deleteLimit(${limit.id})">{% trans "Delete" %}</button></td>
                `;
                limitTable.appendChild(row);
            });
        }
        fetchLimits();
    }

    // Delete limit
    window.deleteLimit = async (id) => {
        if (confirm('{% trans "Are you sure you want to delete this limit?" %}')) {
            await fetch(`/api/limits/${id}/`, { method: 'DELETE', headers });
            fetchLimits();
        }
    };

    // Manage notifications
    const notificationForm = document.getElementById('notification-form');
    if (notificationForm) {
        notificationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(notificationForm);
            const data = Object.fromEntries(formData);
            await fetch('/api/notifications/', {
                method: 'POST',
                headers,
                body: JSON.stringify(data)
            });
            alert('{% trans "Notification settings saved" %}');
        });
    }

    // Fetch and display logs
    const logTable = document.getElementById('log-table');
    const logFilter = document.getElementById('log-filter');
    if (logTable) {
        async function fetchLogs(params = {}) {
            const query = new URLSearchParams(params).toString();
            const response = await fetch(`/api/action-logs/?${query}`, { headers });
            const data = await response.json();
            logTable.innerHTML = '';
            data.forEach(log => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${log.admin}</td>
                    <td>${log.action}</td>
                    <td>${moment(log.timestamp).format('LLL')}</td>
                `;
                logTable.appendChild(row);
            });
        }
        logFilter.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(logFilter);
            const params = Object.fromEntries(formData);
            await fetchLogs(params);
        });
        fetchLogs();
    }

    // Initial fetch
    fetchExpenses();
});
