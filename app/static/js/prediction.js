/**
 * Prediction Screen Logic
 * Handles model selection, feature input, and prediction display
 */

// DOM Elements
const predictionElements = {
    // Screens
    trainingScreen: document.getElementById('trainingScreen'),
    predictionScreen: document.getElementById('predictionScreen'),
    
    // Tabs
    tabButtons: document.querySelectorAll('.tab-btn'),
    
    // Model selector
    modelSelector: document.getElementById('modelSelector'),
    
    // Feature inputs
    ipvInput: document.getElementById('ipv'),
    ipsInput: document.getElementById('ips'),
    ianInput: document.getElementById('ian'),
    iegInput: document.getElementById('ieg'),
    indeInput: document.getElementById('inde'),
    iaaInput: document.getElementById('iaa'),
    idaInput: document.getElementById('ida'),
    
    // Buttons
    predictBtn: document.getElementById('predictBtn'),
    newPredictionBtn: document.getElementById('newPredictionBtn'),
    retryPredictionBtn: document.getElementById('retryPredictionBtn'),
    
    // Results
    predictionResults: document.getElementById('predictionResults'),
    predictedStone: document.getElementById('predictedStone'),
    confidenceValue: document.getElementById('confidenceValue'),
    confidenceFill: document.getElementById('confidenceFill'),
    probabilityBars: document.getElementById('probabilityBars'),
    modelUsed: document.getElementById('modelUsed'),
    
    // Error
    predictionError: document.getElementById('predictionError'),
    predictionErrorContent: document.getElementById('predictionErrorContent')
};

// State
let availableModels = [];
let currentPrediction = null;

/**
 * Initialize prediction screen
 */
async function initPrediction() {
    console.log('Initializing prediction screen...');
    
    // Setup tab navigation
    setupTabNavigation();
    
    // Load available models
    await loadAvailableModels();
    
    // Setup event listeners
    setupPredictionListeners();
}

/**
 * Setup tab navigation
 */
function setupTabNavigation() {
    predictionElements.tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const screenName = btn.dataset.screen;
            switchToScreen(screenName);
        });
    });
}

/**
 * Switch between training and prediction screens
 */
function switchToScreen(screenName) {
    // Update tab buttons
    predictionElements.tabButtons.forEach(btn => {
        if (btn.dataset.screen === screenName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Show/hide screens
    if (screenName === 'training') {
        predictionElements.trainingScreen.style.display = 'block';
        predictionElements.predictionScreen.style.display = 'none';
    } else if (screenName === 'prediction') {
        predictionElements.trainingScreen.style.display = 'none';
        predictionElements.predictionScreen.style.display = 'block';
        
        // Reload models when switching to prediction screen
        loadAvailableModels();
    }
}

/**
 * Load available models from API
 */
async function loadAvailableModels() {
    try {
        const response = await fetch('/api/models');
        
        if (!response.ok) {
            throw new Error('Falha ao carregar modelos');
        }
        
        const models = await response.json();
        availableModels = models;
        
        // Populate selector
        populateModelSelector(models);
        
    } catch (error) {
        console.error('Error loading models:', error);
        predictionElements.modelSelector.innerHTML = 
            '<option value="">Erro ao carregar modelos</option>';
    }
}

/**
 * Populate model selector dropdown
 */
function populateModelSelector(models) {
    if (!models || models.length === 0) {
        predictionElements.modelSelector.innerHTML = 
            '<option value="">Nenhum modelo disponível</option>';
        predictionElements.predictBtn.disabled = true;
        return;
    }
    
    // Clear and populate
    predictionElements.modelSelector.innerHTML = '';
    
    // Add default option (latest model) - shows full filename
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = `Mais Recente: ${models[0].files.model}`;
    predictionElements.modelSelector.appendChild(defaultOption);
    
    // Add all models with full filename
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.model_id;
        option.textContent = model.files.model;
        predictionElements.modelSelector.appendChild(option);
    });
    
    predictionElements.predictBtn.disabled = false;
}

/**
 * Setup event listeners for prediction
 */
function setupPredictionListeners() {
    // Predict button
    predictionElements.predictBtn.addEventListener('click', handlePredict);
    
    // New prediction button
    predictionElements.newPredictionBtn.addEventListener('click', resetPredictionForm);
    
    // Retry button
    predictionElements.retryPredictionBtn.addEventListener('click', () => {
        predictionElements.predictionError.style.display = 'none';
    });
    
    // Enter key on inputs
    const inputs = [
        predictionElements.ipvInput,
        predictionElements.ipsInput,
        predictionElements.ianInput,
        predictionElements.iegInput,
        predictionElements.indeInput,
        predictionElements.iaaInput,
        predictionElements.idaInput
    ];
    
    inputs.forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handlePredict();
            }
        });
    });
}

/**
 * Collect feature values from inputs
 */
function collectFeatureValues() {
    return {
        IPV: parseFloat(predictionElements.ipvInput.value),
        IPS: parseFloat(predictionElements.ipsInput.value),
        IAN: parseFloat(predictionElements.ianInput.value),
        IEG: parseFloat(predictionElements.iegInput.value),
        INDE: parseFloat(predictionElements.indeInput.value),
        IAA: parseFloat(predictionElements.iaaInput.value),
        IDA: parseFloat(predictionElements.idaInput.value)
    };
}

/**
 * Validate feature inputs
 */
function validateInputs(features) {
    const errors = [];
    
    Object.entries(features).forEach(([key, value]) => {
        if (isNaN(value) || value === null) {
            errors.push(`${key} deve ser um número válido`);
        }
    });
    
    return errors;
}

/**
 * Handle prediction request
 */
async function handlePredict() {
    // Collect features
    const features = collectFeatureValues();
    
    // Validate
    const errors = validateInputs(features);
    if (errors.length > 0) {
        showPredictionError(`Erros de validação:\n${errors.join('\n')}`);
        return;
    }
    
    // Get selected model (empty string = latest)
    const modelId = predictionElements.modelSelector.value || null;
    
    // Prepare request
    const requestData = {
        ...features,
        model_id: modelId
    };
    
    // Disable button during request
    predictionElements.predictBtn.disabled = true;
    predictionElements.predictBtn.textContent = '⏳ Processando...';
    
    try {
        const response = await fetch('/api/prediction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || 'Erro na predição');
        }
        
        const result = await response.json();
        currentPrediction = result;
        
        // Show results
        showPredictionResults(result);
        
    } catch (error) {
        console.error('Prediction error:', error);
        showPredictionError(error.message);
    } finally {
        // Re-enable button
        predictionElements.predictBtn.disabled = false;
        predictionElements.predictBtn.textContent = '🔮 Realizar Predição';
    }
}

/**
 * Display prediction results
 */
function showPredictionResults(result) {
    // Hide error if visible
    predictionElements.predictionError.style.display = 'none';
    
    // Show predicted stone
    predictionElements.predictedStone.textContent = result.pedra_predita;
    predictionElements.predictedStone.className = `stone-name stone-${result.pedra_predita.toLowerCase()}`;
    
    // Show confidence
    const confidencePercent = (result.confianca * 100).toFixed(1);
    predictionElements.confidenceValue.textContent = `${confidencePercent}%`;
    predictionElements.confidenceFill.style.width = `${confidencePercent}%`;
    
    // Color confidence bar based on value
    if (result.confianca >= 0.7) {
        predictionElements.confidenceFill.className = 'confidence-fill high';
    } else if (result.confianca >= 0.5) {
        predictionElements.confidenceFill.className = 'confidence-fill medium';
    } else {
        predictionElements.confidenceFill.className = 'confidence-fill low';
    }
    
    // Show probabilities
    displayProbabilityBars(result.probabilidades);
    
    // Show model used
    predictionElements.modelUsed.textContent = result.model_used;
    
    // Show results section
    predictionElements.predictionResults.style.display = 'block';
    
    // Scroll to results
    predictionElements.predictionResults.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Display probability bars for all classes
 */
function displayProbabilityBars(probabilities) {
    // Sort by probability (descending)
    const sorted = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);
    
    // Clear existing bars
    predictionElements.probabilityBars.innerHTML = '';
    
    // Create bars
    sorted.forEach(([className, probability]) => {
        const barContainer = document.createElement('div');
        barContainer.className = 'probability-bar-container';
        
        const label = document.createElement('span');
        label.className = 'probability-label';
        label.textContent = className;
        
        const barWrapper = document.createElement('div');
        barWrapper.className = 'probability-bar-wrapper';
        
        const bar = document.createElement('div');
        bar.className = 'probability-bar';
        bar.style.width = `${probability * 100}%`;
        
        const value = document.createElement('span');
        value.className = 'probability-value';
        value.textContent = `${(probability * 100).toFixed(1)}%`;
        
        barWrapper.appendChild(bar);
        barContainer.appendChild(label);
        barContainer.appendChild(barWrapper);
        barContainer.appendChild(value);
        
        predictionElements.probabilityBars.appendChild(barContainer);
    });
}

/**
 * Show prediction error
 */
function showPredictionError(message) {
    predictionElements.predictionErrorContent.textContent = message;
    predictionElements.predictionError.style.display = 'block';
    predictionElements.predictionResults.style.display = 'none';
    
    // Scroll to error
    predictionElements.predictionError.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Reset prediction form
 */
function resetPredictionForm() {
    // Clear inputs
    predictionElements.ipvInput.value = '';
    predictionElements.ipsInput.value = '';
    predictionElements.ianInput.value = '';
    predictionElements.iegInput.value = '';
    predictionElements.indeInput.value = '';
    predictionElements.iaaInput.value = '';
    predictionElements.idaInput.value = '';
    
    // Hide results and error
    predictionElements.predictionResults.style.display = 'none';
    predictionElements.predictionError.style.display = 'none';
    
    // Focus first input
    predictionElements.ipvInput.focus();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================================
// BATCH PREDICTION (Upload Excel)
// ============================================================================

const batchElements = {
    uploadZone: document.getElementById('batchUploadZone'),
    fileInput: document.getElementById('batchFileInput'),
    filePreview: document.getElementById('batchFilePreview'),
    fileName: document.getElementById('batchFileName'),
    fileSize: document.getElementById('batchFileSize'),
    removeBtn: document.getElementById('removeBatchFileBtn'),
    predictBtn: document.getElementById('predictBatchBtn'),
    progress: document.getElementById('batchProgress'),
    result: document.getElementById('batchResult'),
    total: document.getElementById('batchTotal'),
    success: document.getElementById('batchSuccess'),
    model: document.getElementById('batchModel'),
    downloadBtn: document.getElementById('downloadBatchBtn')
};

let selectedBatchFile = null;

// Setup batch prediction listeners
function setupBatchPrediction() {
    if (!batchElements.uploadZone) return;
    
    // Click to upload
    batchElements.uploadZone.addEventListener('click', () => {
        batchElements.fileInput.click();
    });
    
    // File selected
    batchElements.fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleBatchFileSelect(file);
        }
    });
    
    // Drag and drop
    batchElements.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        batchElements.uploadZone.classList.add('drag-over');
    });
    
    batchElements.uploadZone.addEventListener('dragleave', () => {
        batchElements.uploadZone.classList.remove('drag-over');
    });
    
    batchElements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        batchElements.uploadZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file) {
            handleBatchFileSelect(file);
        }
    });
    
    // Remove file
    batchElements.removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetBatchUpload();
    });
    
    // Process button
    batchElements.predictBtn.addEventListener('click', processBatchPrediction);
}

function handleBatchFileSelect(file) {
    // Validate file type
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        alert('Por favor, selecione um arquivo Excel (.xlsx ou .xls)');
        return;
    }
    
    selectedBatchFile = file;
    
    // Show file info
    batchElements.fileName.textContent = file.name;
    batchElements.fileSize.textContent = formatFileSize(file.size);
    
    // Update UI
    batchElements.uploadZone.style.display = 'none';
    batchElements.filePreview.style.display = 'flex';
    batchElements.predictBtn.style.display = 'block';
    batchElements.result.style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function processBatchPrediction() {
    if (!selectedBatchFile) return;
    
    // Show progress
    batchElements.predictBtn.style.display = 'none';
    batchElements.progress.style.display = 'block';
    batchElements.result.style.display = 'none';
    
    // Prepare form data
    const formData = new FormData();
    formData.append('file', selectedBatchFile);
    
    const modelId = predictionElements.modelSelector.value;
    if (modelId) {
        formData.append('model_id', modelId);
    }
    
    try {
        const response = await fetch('/api/prediction/batch', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || 'Erro no processamento');
        }
        
        const result = await response.json();
        
        // Show results
        showBatchResult(result);
        
    } catch (error) {
        console.error('Batch prediction error:', error);
        alert(`Erro: ${error.message}`);
        batchElements.predictBtn.style.display = 'block';
    } finally {
        batchElements.progress.style.display = 'none';
    }
}

function showBatchResult(result) {
    batchElements.total.textContent = result.total_records;
    batchElements.success.textContent = result.successful_predictions;
    batchElements.model.textContent = result.model_used;
    
    // Setup download button
    batchElements.downloadBtn.href = result.download_url;
    batchElements.downloadBtn.download = `predicao_resultado_${new Date().getTime()}.xlsx`;
    
    batchElements.result.style.display = 'block';
    
    // Scroll to result
    batchElements.result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function resetBatchUpload() {
    selectedBatchFile = null;
    batchElements.fileInput.value = '';
    batchElements.uploadZone.style.display = 'block';
    batchElements.filePreview.style.display = 'none';
    batchElements.predictBtn.style.display = 'none';
    batchElements.progress.style.display = 'none';
    batchElements.result.style.display = 'none';
}

// Initialize batch prediction when DOM is ready
setupBatchPrediction();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPrediction);
} else {
    initPrediction();
}
