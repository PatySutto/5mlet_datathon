// Estado da aplicação
const state = {
    uploadedFile: null,
    fileId: null,
    taskId: null,
    pollingInterval: null
};

// Elementos DOM
const elements = {
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    filePreview: document.getElementById('filePreview'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFileBtn: document.getElementById('removeFileBtn'),
    validationResults: document.getElementById('validationResults'),
    validationWarnings: document.getElementById('validationWarnings'),
    totalRecords: document.getElementById('totalRecords'),
    validRecords: document.getElementById('validRecords'),
    rejectedRecords: document.getElementById('rejectedRecords'),
    parametersSection: document.getElementById('parametersSection'),
    startTrainingBtn: document.getElementById('startTrainingBtn'),
    progressSection: document.getElementById('progressSection'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    stageIndicator: document.getElementById('stageIndicator'),
    logContent: document.getElementById('logContent'),
    resultsSection: document.getElementById('resultsSection'),
    errorSection: document.getElementById('errorSection'),
    errorContent: document.getElementById('errorContent'),
    newTrainingBtn: document.getElementById('newTrainingBtn'),
    retryBtn: document.getElementById('retryBtn')
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    setupDropZone();
    setupButtons();
});

// Setup Drag-and-Drop
function setupDropZone() {
    const { dropZone, fileInput } = elements;

    // Click to select
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag over
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    // Drag leave
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    // Drop
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

// Setup Buttons
function setupButtons() {
    elements.removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetUpload();
    });

    elements.startTrainingBtn.addEventListener('click', startTraining);
    elements.newTrainingBtn.addEventListener('click', resetAll);
    elements.retryBtn.addEventListener('click', resetToParameters);
}

// Handle File Selection
function handleFileSelect(file) {
    // Validar extensão
    const validExtensions = ['.xlsx', '.xls'];
    const fileName = file.name.toLowerCase();
    const isValid = validExtensions.some(ext => fileName.endsWith(ext));

    if (!isValid) {
        showError('Formato de arquivo inválido. Use .xlsx ou .xls');
        return;
    }

    // Validar tamanho (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('Arquivo muito grande. Tamanho máximo: 10MB');
        return;
    }

    state.uploadedFile = file;
    showFilePreview(file);
    uploadFile(file);
}

// Show File Preview
function showFilePreview(file) {
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
    elements.filePreview.style.display = 'block';
    elements.dropZone.style.display = 'none';
}

// Upload File
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        addLog('📤 Enviando arquivo...');
        
        const response = await fetch('/api/training/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Erro no upload');
        }

        state.fileId = data.file_id;
        showValidationResults(data.validation);
        elements.parametersSection.style.display = 'block';
        addLog('✅ Arquivo validado com sucesso', 'success');

    } catch (error) {
        addLog(`❌ Erro: ${error.message}`, 'error');
        showError(`Erro ao fazer upload: ${error.message}`);
        resetUpload();
    }
}

// Show Validation Results
function showValidationResults(validation) {
    elements.totalRecords.textContent = validation.total_records;
    elements.validRecords.textContent = validation.valid_records;
    elements.rejectedRecords.textContent = validation.rejected_records;

    if (validation.warnings && validation.warnings.length > 0) {
        elements.validationWarnings.innerHTML = validation.warnings
            .map(w => `<p>⚠️ ${w}</p>`)
            .join('');
        elements.validationWarnings.style.display = 'block';
    } else {
        elements.validationWarnings.style.display = 'none';
    }

    elements.validationResults.style.display = 'block';
}

// Start Training
async function startTraining() {
    elements.startTrainingBtn.disabled = true;

    const parameters = {
        max_depth: parseInt(document.getElementById('maxDepth').value),
        n_estimators: parseInt(document.getElementById('nEstimators').value),
        learning_rate: parseFloat(document.getElementById('learningRate').value),
        test_size: parseFloat(document.getElementById('testSize').value),
        random_state: 42,
        use_feast: document.getElementById('useFeast').checked
    };

    try {
        addLog('🚀 Iniciando treinamento...');
        
        const response = await fetch('/api/training/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(parameters)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Erro ao iniciar treinamento');
        }

        state.taskId = data.task_id;
        hideAll();
        elements.progressSection.style.display = 'block';
        addLog(`✅ Task iniciada: ${state.taskId}`, 'success');
        
        // Iniciar polling
        startPolling();

    } catch (error) {
        addLog(`❌ Erro: ${error.message}`, 'error');
        showError(`Erro ao iniciar treinamento: ${error.message}`);
        elements.startTrainingBtn.disabled = false;
    }
}

// Start Polling
function startPolling() {
    state.pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/training/status/${state.taskId}`);
            const status = await response.json();

            if (!response.ok) {
                throw new Error('Erro ao consultar status');
            }

            updateProgress(status);

            if (status.status === 'completed') {
                stopPolling();
                await loadResults();
            } else if (status.status === 'failed') {
                stopPolling();
                showTrainingError(status.error || 'Erro desconhecido');
            }

        } catch (error) {
            console.error('Erro no polling:', error);
        }
    }, 2000); // 2 segundos
}

// Stop Polling
function stopPolling() {
    if (state.pollingInterval) {
        clearInterval(state.pollingInterval);
        state.pollingInterval = null;
    }
}

// Update Progress
function updateProgress(status) {
    // Atualizar barra de progresso
    elements.progressFill.style.width = `${status.progress}%`;
    elements.progressText.textContent = `${status.progress}%`;

    // Atualizar stage indicator
    const stages = elements.stageIndicator.querySelectorAll('.stage');
    stages.forEach(stage => {
        const stageName = stage.dataset.stage;
        stage.classList.remove('active', 'completed');
        
        if (stageName === status.stage) {
            stage.classList.add('active');
        }
    });

    // Adicionar log
    addLog(status.message);
}

// Load Results
async function loadResults() {
    try {
        const response = await fetch(`/api/training/result/${state.taskId}`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error('Erro ao carregar resultados');
        }

        showResults(result);

    } catch (error) {
        showError(`Erro ao carregar resultados: ${error.message}`);
    }
}

// Show Results
function showResults(result) {
    hideAll();
    elements.resultsSection.style.display = 'block';

    // Métricas gerais
    document.getElementById('accuracyValue').textContent = 
        (result.metrics.accuracy * 100).toFixed(2) + '%';
    document.getElementById('precisionValue').textContent = 
        (result.metrics.precision_macro * 100).toFixed(2) + '%';
    document.getElementById('recallValue').textContent = 
        (result.metrics.recall_macro * 100).toFixed(2) + '%';
    document.getElementById('f1Value').textContent = 
        (result.metrics.f1_macro * 100).toFixed(2) + '%';

    // Importância das features
    showFeatureImportance(result.feature_importance);

    // Informações do modelo
    document.getElementById('modelId').textContent = result.model_id;
    document.getElementById('trainingDuration').textContent = 
        `${result.duration_seconds.toFixed(1)}s`;
    document.getElementById('modelFile').textContent = result.model_files.model;

    addLog('🎉 Resultados carregados com sucesso', 'success');
}

// Show Feature Importance
function showFeatureImportance(importance) {
    const container = document.getElementById('importanceBars');
    container.innerHTML = '';

    // Ordenar por importância
    const sorted = Object.entries(importance)
        .sort(([,a], [,b]) => b - a);

    sorted.forEach(([feature, value]) => {
        const percentage = (value * 100).toFixed(1);
        
        const barHtml = `
            <div class="importance-bar">
                <div class="importance-label">
                    <span><strong>${feature}</strong></span>
                    <span>${percentage}%</span>
                </div>
                <div class="importance-track">
                    <div class="importance-fill" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
        
        container.innerHTML += barHtml;
    });
}

// Show Training Error
function showTrainingError(error) {
    hideAll();
    elements.errorSection.style.display = 'block';
    elements.errorContent.textContent = error;
    addLog(`❌ Treinamento falhou: ${error}`, 'error');
}

// Add Log Entry
function addLog(message, type = '') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    elements.logContent.appendChild(entry);
    elements.logContent.scrollTop = elements.logContent.scrollHeight;
}

// Reset Functions
function resetUpload() {
    state.uploadedFile = null;
    state.fileId = null;
    elements.filePreview.style.display = 'none';
    elements.dropZone.style.display = 'block';
    elements.validationResults.style.display = 'none';
    elements.parametersSection.style.display = 'none';
    elements.fileInput.value = '';
}

function resetToParameters() {
    hideAll();
    elements.filePreview.style.display = 'block';
    elements.validationResults.style.display = 'block';
    elements.parametersSection.style.display = 'block';
    elements.startTrainingBtn.disabled = false;
}

function resetAll() {
    stopPolling();
    state.uploadedFile = null;
    state.fileId = null;
    state.taskId = null;
    hideAll();
    resetUpload();
    elements.logContent.innerHTML = '';
}

function hideAll() {
    elements.parametersSection.style.display = 'none';
    elements.progressSection.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    elements.errorSection.style.display = 'none';
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showError(message) {
    alert(message); // Pode ser substituído por modal customizado
}
