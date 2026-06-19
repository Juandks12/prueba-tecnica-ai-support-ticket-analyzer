// --- CONTROLADOR DEL DASHBOARD (HTML5/JS NATIVO) ---

const API_BASE = '/api'; // Resuelto por el proxy reverso de Nginx en Docker

// Estado global de la aplicación
let state = {
    currentPage: 1,
    limit: 10,
    totalTickets: 0,
    filters: {
        category: '',
        priority: '',
        status: '',
        search: ''
    },
    charts: {
        categories: null,
        priorities: null
    }
};

// --- INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupEventListeners();
});

function initApp() {
    loadMetrics();
    loadTickets();
}

// --- CONFIGURACIÓN DE EVENTOS ---
function setupEventListeners() {
    // Filtros dropdown
    document.getElementById('filter-category').addEventListener('change', (e) => {
        state.filters.category = e.target.value;
        state.currentPage = 1;
        loadTickets();
    });

    document.getElementById('filter-priority').addEventListener('change', (e) => {
        state.filters.priority = e.target.value;
        state.currentPage = 1;
        loadTickets();
    });

    document.getElementById('filter-status').addEventListener('change', (e) => {
        state.filters.status = e.target.value;
        state.currentPage = 1;
        loadTickets();
    });

    // Búsqueda de texto con retraso (debounce)
    let searchTimeout;
    document.getElementById('search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.filters.search = e.target.value.trim();
            state.currentPage = 1;
            loadTickets();
        }, 400); // Esperar 400ms tras dejar de escribir
    });

    // Botón reiniciar filtros
    document.getElementById('btn-reset-filters').addEventListener('click', () => {
        document.getElementById('filter-category').value = '';
        document.getElementById('filter-priority').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('search-input').value = '';
        
        state.filters = { category: '', priority: '', status: '', search: '' };
        state.currentPage = 1;
        loadTickets();
    });

    // Paginación
    document.getElementById('btn-prev-page').addEventListener('click', () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            loadTickets();
        }
    });

    document.getElementById('btn-next-page').addEventListener('click', () => {
        const totalPages = Math.ceil(state.totalTickets / state.limit);
        if (state.currentPage < totalPages) {
            state.currentPage++;
            loadTickets();
        }
    });

    // Ingesta de datos
    document.getElementById('btn-ingest').addEventListener('click', triggerIngestion);

    // Modal de Detalle
    document.getElementById('btn-close-modal').addEventListener('click', closeModal);
    document.getElementById('ticket-modal').addEventListener('click', (e) => {
        if (e.target.id === 'ticket-modal') closeModal();
    });

    // Agente de IA Chat
    document.getElementById('btn-send-agent').addEventListener('click', sendAgentQuestion);
    document.getElementById('agent-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendAgentQuestion();
    });

    // Toggle de proveedor IA (Mock / DeepSeek)
    const providerToggle = document.getElementById('provider-toggle');
    if (providerToggle) {
        providerToggle.addEventListener('change', () => {
            const mockLabel = document.querySelector('.mock-label');
            const deepseekLabel = document.querySelector('.deepseek-label');
            const providerTag = document.getElementById('llm-provider-tag');
            if (providerToggle.checked) {
                mockLabel.classList.remove('active');
                deepseekLabel.classList.add('active');
                if (providerTag) providerTag.textContent = 'LLM: DeepSeek';
            } else {
                mockLabel.classList.add('active');
                deepseekLabel.classList.remove('active');
                if (providerTag) providerTag.textContent = 'LLM: Mock';
            }
        });
    }
}

// --- CONSUMO DE LA API ---

// 1. Obtener y renderizar Métricas
async function loadMetrics() {
    try {
        const response = await fetch(`${API_BASE}/metrics`);
        if (!response.ok) throw new Error('Error al cargar métricas');
        const data = await response.json();
        
        renderKPIs(data);
        renderCharts(data);
    } catch (error) {
        console.error('Error cargando métricas:', error);
        document.getElementById('kpi-top-product').innerText = 'Error al cargar';
    }
}

// 2. Obtener y renderizar Tickets en la Tabla
async function loadTickets() {
    const tableBody = document.getElementById('tickets-table-body');
    tableBody.innerHTML = `<tr><td colspan="9" class="td-loader">Cargando registros...</td></tr>`;

    const skip = (state.currentPage - 1) * state.limit;
    
    // Armar Query Params
    let queryParams = new URLSearchParams({
        skip: skip,
        limit: state.limit
    });
    if (state.filters.category) queryParams.append('category', state.filters.category);
    if (state.filters.priority) queryParams.append('priority', state.filters.priority);
    if (state.filters.status) queryParams.append('status', state.filters.status);
    if (state.filters.search) queryParams.append('search', state.filters.search);

    try {
        const response = await fetch(`${API_BASE}/tickets?${queryParams.toString()}`);
        if (!response.ok) throw new Error('Error al cargar tickets');
        const data = await response.json();

        state.totalTickets = data.total;
        renderTicketsTable(data.tickets);
        updatePagination();
    } catch (error) {
        console.error('Error cargando tickets:', error);
        tableBody.innerHTML = `<tr><td colspan="9" class="td-loader" style="color: #f43f5e;">Ocurrió un error al cargar la lista de tickets. Revisa la conexión al Backend.</td></tr>`;
    }
}

// 3. Ejecutar Ingesta de datos
async function triggerIngestion() {
    const statusMsg = document.getElementById('ingest-status-msg');
    const ingestBtn = document.getElementById('btn-ingest');
    
    statusMsg.innerText = 'Encolando proceso de ingesta...';
    statusMsg.style.color = '#06b6d4';
    ingestBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/ingest`, { method: 'POST' });
        if (!response.ok) throw new Error('Error al iniciar ingesta');
        
        statusMsg.innerText = 'Ingestando en segundo plano. Actualizando datos...';
        statusMsg.style.color = '#10b981';

        // Auto-actualizar el Dashboard cada 2 segundos por un período de tiempo
        let pollCount = 0;
        const interval = setInterval(() => {
            loadMetrics();
            loadTickets();
            pollCount++;
            if (pollCount >= 5) {
                clearInterval(interval);
                ingestBtn.disabled = false;
                statusMsg.innerText = 'Actualización completada.';
                setTimeout(() => { statusMsg.innerText = ''; }, 3000);
            }
        }, 2000);

    } catch (error) {
        console.error('Error ejecutando ingesta:', error);
        statusMsg.innerText = 'Falló el inicio de la ingesta.';
        statusMsg.style.color = '#f43f5e';
        ingestBtn.disabled = false;
    }
}

// 4. Preguntas al Agente de IA (RAG)
async function sendAgentQuestion() {
    const input = document.getElementById('agent-input');
    const question = input.value.trim();
    if (!question) return;

    input.value = '';

    const providerToggle = document.getElementById('provider-toggle');
    const provider = providerToggle && providerToggle.checked ? 'deepseek' : 'mock';
    const providerLabel = provider === 'deepseek' ? 'DeepSeek' : 'Mock';
    appendChatMessage('user', question);

    const loaderId = appendChatMessage('bot', `<em>Consultando con ${providerLabel}...</em>`);

    try {
        const response = await fetch(`${API_BASE}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question, provider: provider })
        });
        
        const loaderBubble = document.getElementById(loaderId);
        if (loaderBubble) loaderBubble.remove();

        if (!response.ok) throw new Error('Error en el servicio de IA');
        const data = await response.json();
        
        appendChatMessage('bot', formatMarkdown(data.answer));
    } catch (error) {
        console.error('Error en consulta de IA:', error);
        const loaderBubble = document.getElementById(loaderId);
        if (loaderBubble) loaderBubble.remove();
        appendChatMessage('bot', '<span style="color: #f43f5e;">Lo siento, no pude procesar la respuesta en este momento. Verifica la conexión a la API.</span>');
    }
}

// --- RENDERIZADORES DE UI ---

// Renderizar KPIs
function renderKPIs(data) {
    document.getElementById('kpi-total').innerText = data.total_tickets;
    
    const highAndCritical = (data.priorities['High'] || 0) + (data.priorities['Critical'] || 0);
    document.getElementById('kpi-critical').innerText = highAndCritical;
    
    document.getElementById('kpi-satisfaction').innerText = data.average_satisfaction ? data.average_satisfaction.toFixed(1) + ' / 5.0' : 'N/A';
    
    const topProducts = Object.keys(data.top_products);
    document.getElementById('kpi-top-product').innerText = topProducts.length > 0 ? topProducts[0] : 'Ninguno';
}

// Renderizar Gráficos con Chart.js
function renderCharts(data) {
    const ctxCats = document.getElementById('chart-categories').getContext('2d');
    const ctxPrios = document.getElementById('chart-priorities').getContext('2d');

    // Destruir instancias anteriores para evitar bugs al refrescar
    if (state.charts.categories) state.charts.categories.destroy();
    if (state.charts.priorities) state.charts.priorities.destroy();

    // Paleta de colores consistente con style.css
    const categoryColors = ['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#06b6d4'];
    const priorityColors = {
        'Low': '#10b981',
        'Medium': '#3b82f6',
        'High': '#f59e0b',
        'Critical': '#f43f5e'
    };

    // 1. Gráfico de Categorías (Dona)
    const catKeys = Object.keys(data.categories);
    const catVals = Object.values(data.categories);
    state.charts.categories = new Chart(ctxCats, {
        type: 'doughnut',
        data: {
            labels: catKeys,
            datasets: [{
                data: catVals,
                backgroundColor: categoryColors.slice(0, catKeys.length),
                borderWidth: 1,
                borderColor: 'rgba(255, 255, 255, 0.05)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8', font: { size: 9 }, boxWidth: 10 }
                },
                title: { display: true, text: 'Tickets por Categoría', color: '#f8fafc' }
            }
        }
    });

    // 2. Gráfico de Prioridades (Barras)
    const prioOrder = ['Low', 'Medium', 'High', 'Critical'];
    const prioVals = prioOrder.map(p => data.priorities[p] || 0);
    state.charts.priorities = new Chart(ctxPrios, {
        type: 'bar',
        data: {
            labels: prioOrder,
            datasets: [{
                label: 'Tickets',
                data: prioVals,
                backgroundColor: prioOrder.map(p => priorityColors[p]),
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Distribución de Prioridades', color: '#f8fafc' }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255, 255, 255, 0.04)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

// Renderizar la Tabla de registros
function renderTicketsTable(tickets) {
    const tableBody = document.getElementById('tickets-table-body');
    const tableShowingText = document.getElementById('table-showing-text');
    
    if (tickets.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="9" class="td-loader">No se encontraron tickets con los filtros aplicados.</td></tr>`;
        tableShowingText.innerText = 'Mostrando 0 tickets';
        return;
    }

    const startIdx = (state.currentPage - 1) * state.limit + 1;
    const endIdx = startIdx + tickets.length - 1;
    tableShowingText.innerText = `Mostrando ${startIdx}-${endIdx} de ${state.totalTickets} tickets`;

    tableBody.innerHTML = '';
    
    tickets.forEach(ticket => {
        const tr = document.createElement('tr');
        
        // Estilizar prioridad badge
        const prioLower = ticket.ai_priority.toLowerCase();
        const prioBadge = `<span class="badge badge-${prioLower}">${ticket.ai_priority}</span>`;

        // Estilizar estado badge
        let statusClass = 'badge-open';
        if (ticket.ticket_status.toLowerCase() === 'pending customer response') statusClass = 'badge-pending';
        if (ticket.ticket_status.toLowerCase() === 'closed') statusClass = 'badge-closed';
        const statusBadge = `<span class="badge ${statusClass}">${ticket.ticket_status}</span>`;

        // Estilizar sentimiento badge
        let sentClass = 'badge-neutral';
        const sentLower = ticket.ai_sentiment.toLowerCase();
        if (sentLower.includes('calm')) sentClass = 'badge-calm';
        if (sentLower.includes('frust')) sentClass = 'badge-frustrated';
        if (sentLower.includes('ang') || sentLower.includes('urg')) sentClass = 'badge-angry';
        const sentimentBadge = `<span class="badge badge-sentiment ${sentClass}">${ticket.ai_sentiment}</span>`;

        tr.innerHTML = `
            <td>#${ticket.ticket_id}</td>
            <td style="font-weight: 500;">${ticket.customer_name}</td>
            <td>${ticket.product_purchased}</td>
            <td>${ticket.ai_category}</td>
            <td>${prioBadge}</td>
            <td>${sentimentBadge}</td>
            <td><span class="badge badge-outline">${ticket.ai_team}</span></td>
            <td>${statusBadge}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="openTicketDetail(${JSON.stringify(ticket).replace(/"/g, '&quot;')})">Ver Detalle</button>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

// Paginación de tabla
function updatePagination() {
    const totalPages = Math.ceil(state.totalTickets / state.limit) || 1;
    document.getElementById('pagination-info').innerText = `Página ${state.currentPage} de ${totalPages}`;
    
    document.getElementById('btn-prev-page').disabled = state.currentPage === 1;
    document.getElementById('btn-next-page').disabled = state.currentPage === totalPages;
}

// --- DETALLE DEL TICKET (MODAL) ---
function openTicketDetail(ticket) {
    document.getElementById('m-ticket-id').innerText = ticket.ticket_id;
    document.getElementById('m-customer-name').innerText = ticket.customer_name;
    document.getElementById('m-customer-email').innerText = ticket.customer_email || 'N/A';
    document.getElementById('m-customer-age').innerText = ticket.customer_age || 'N/A';
    document.getElementById('m-customer-gender').innerText = ticket.customer_gender;
    
    document.getElementById('m-product').innerText = ticket.product_purchased;
    document.getElementById('m-purchase-date').innerText = ticket.date_of_purchase || 'N/A';
    document.getElementById('m-channel').innerText = ticket.ticket_channel;

    // Badges IA
    const prioLower = ticket.ai_priority.toLowerCase();
    const prioBadge = document.getElementById('m-ai-priority');
    prioBadge.className = `badge badge-${prioLower}`;
    prioBadge.innerText = ticket.ai_priority;

    const catBadge = document.getElementById('m-ai-category');
    catBadge.className = 'badge badge-accent';
    catBadge.innerText = ticket.ai_category;

    const teamBadge = document.getElementById('m-ai-team');
    teamBadge.className = 'badge badge-outline';
    teamBadge.innerText = ticket.ai_team;

    const sentBadge = document.getElementById('m-ai-sentiment');
    sentBadge.className = 'badge badge-sentiment';
    let sentClass = 'badge-neutral';
    const sentLower = ticket.ai_sentiment.toLowerCase();
    if (sentLower.includes('calm')) sentClass = 'badge-calm';
    if (sentLower.includes('frust')) sentClass = 'badge-frustrated';
    if (sentLower.includes('ang') || sentLower.includes('urg')) sentClass = 'badge-angry';
    sentBadge.classList.add(sentClass);
    sentBadge.innerText = ticket.ai_sentiment;

    // Estados
    const statusLower = ticket.ticket_status.toLowerCase();
    let statusClass = 'badge-open';
    if (statusLower === 'pending customer response') statusClass = 'badge-pending';
    if (statusLower === 'closed') statusClass = 'badge-closed';
    
    const statB = document.getElementById('m-status');
    statB.className = `badge ${statusClass}`;
    statB.innerText = ticket.ticket_status;

    document.getElementById('m-first-response').innerText = ticket.first_response_time || 'Sin respuesta aún';
    document.getElementById('m-resolution').innerText = ticket.time_to_resolution || 'No resuelto';
    document.getElementById('m-satisfaction').innerText = ticket.customer_satisfaction_rating ? ticket.customer_satisfaction_rating + ' / 5.0' : 'N/A';

    document.getElementById('m-ai-summary').innerText = `"${ticket.ai_summary}"`;
    document.getElementById('m-description').innerText = ticket.ticket_description;

    document.getElementById('ticket-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('ticket-modal').classList.remove('active');
}

// --- ASISTENTE CHAT CHIPS & FORMATO ---

// Añadir mensaje a la caja de chat
function appendChatMessage(sender, htmlContent) {
    const history = document.getElementById('chat-history');
    const msgId = 'msg-' + Math.random().toString(36).substr(2, 9);
    
    const wrapper = document.createElement('div');
    wrapper.className = `chat-message ${sender}`;
    wrapper.id = msgId;
    
    wrapper.innerHTML = `
        <div class="message-bubble">
            ${htmlContent}
        </div>
    `;
    
    history.appendChild(wrapper);
    history.scrollTop = history.scrollHeight;
    
    return msgId;
}

// Formateador simple de markdown
function formatMarkdown(text) {
    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
        
    // Dar formato básico a listas
    html = html.replace(/- (.*?)<br>/g, '<li>$1</li>');
    html = html.replace(/(<li>.*?<\/li>)/g, '<ul>$1</ul>');
    // Eliminar listas anidadas duplicadas
    html = html.replace(/<\/ul><ul>/g, '');
    
    return html;
}
