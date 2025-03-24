/**
 * Curriculum Topic Generator
 * Client-side application script
 */

// State management
const appState = {
  collections: [],
  currentCollection: null,
  apiStatus: false,
  isLoading: false,
  error: null
};

// DOM Elements
const elements = {
  // Form elements
  form: document.getElementById('generation-form'),
  examBoardSelect: document.getElementById('exam-board'),
  examTypeSelect: document.getElementById('exam-type'),
  subjectSelect: document.getElementById('subject'),
  customSubjectInput: document.getElementById('custom-subject'),
  generateButton: document.getElementById('generate-button'),
  
  // Status elements
  apiStatus: document.getElementById('api-status'),
  apiStatusText: document.getElementById('api-status-text'),
  
  // Results elements
  resultsPanel: document.getElementById('results-panel'),
  resultExamBoard: document.getElementById('result-exam-board'),
  resultExamType: document.getElementById('result-exam-type'),
  resultSubject: document.getElementById('result-subject'),
  loadingContainer: document.getElementById('loading-container'),
  resultsContainer: document.getElementById('results-container'),
  errorContainer: document.getElementById('error-container'),
  errorMessage: document.getElementById('error-message'),
  tryAgainButton: document.getElementById('try-again'),
  topicsCount: document.getElementById('topics-count'),
  topicsBody: document.getElementById('topics-body'),
  
  // Export buttons
  exportJsonButton: document.getElementById('export-json'),
  exportCsvButton: document.getElementById('export-csv'),
  exportKnackButton: document.getElementById('export-knack'),
  
  // Collections panel
  savedCollectionsPanel: document.getElementById('saved-collections-panel'),
  noCollectionsMessage: document.getElementById('no-collections-message'),
  collectionsList: document.getElementById('collections-list'),
  bulkExportControls: document.querySelector('.bulk-export-controls'),
  bulkExportJsonButton: document.getElementById('bulk-export-json'),
  bulkExportCsvButton: document.getElementById('bulk-export-csv'),
  bulkExportKnackButton: document.getElementById('bulk-export-knack'),
  
  // Modal elements
  exportModal: document.getElementById('export-modal'),
  closeModal: document.querySelector('.close-modal'),
  exportLinks: document.getElementById('export-links')
};

/**
 * Initialize the application
 */
async function initApp() {
  // Fetch config data from the server
  try {
    const response = await fetch('/api/config');
    const config = await response.json();
    
    // Populate form options
    populateExamBoards(config.examBoards);
    populateExamTypes(config.examTypes);
    populateSubjects(config.commonSubjects);
    
    // Set API status
    appState.apiStatus = config.apiStatus;
    updateApiStatus();
    
    // Set up event listeners
    setupEventListeners();
  } catch (error) {
    console.error('Error initializing application:', error);
    showError('Failed to initialize the application. Please refresh the page and try again.');
  }
}

/**
 * Populate exam board select options
 */
function populateExamBoards(examBoards) {
  examBoards.forEach(board => {
    const option = document.createElement('option');
    option.value = board.name;
    option.textContent = board.name;
    elements.examBoardSelect.appendChild(option);
  });
}

/**
 * Populate exam type select options
 */
function populateExamTypes(examTypes) {
  examTypes.forEach(type => {
    const option = document.createElement('option');
    option.value = type.name;
    option.textContent = type.name;
    elements.examTypeSelect.appendChild(option);
  });
}

/**
 * Populate subject select options
 */
function populateSubjects(subjects) {
  subjects.forEach(subject => {
    const option = document.createElement('option');
    option.value = subject;
    option.textContent = subject;
    elements.subjectSelect.appendChild(option);
  });
}

/**
 * Update the API status indicator
 */
function updateApiStatus() {
  if (appState.apiStatus) {
    elements.apiStatus.classList.add('connected');
    elements.apiStatus.classList.remove('disconnected');
    elements.apiStatusText.textContent = 'API Connected';
  } else {
    elements.apiStatus.classList.add('disconnected');
    elements.apiStatus.classList.remove('connected');
    elements.apiStatusText.textContent = 'API Key Missing';
  }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // Form submission
  elements.form.addEventListener('submit', handleFormSubmit);
  
  // Try again button
  elements.tryAgainButton.addEventListener('click', resetForm);
  
  // Export buttons
  elements.exportJsonButton.addEventListener('click', () => exportCollection('json'));
  elements.exportCsvButton.addEventListener('click', () => exportCollection('csv'));
  elements.exportKnackButton.addEventListener('click', () => exportCollection('knack'));
  
  // Bulk export buttons
  elements.bulkExportJsonButton.addEventListener('click', () => bulkExport('json'));
  elements.bulkExportCsvButton.addEventListener('click', () => bulkExport('csv'));
  elements.bulkExportKnackButton.addEventListener('click', () => bulkExport('knack'));
  
  // Modal close button
  elements.closeModal.addEventListener('click', () => {
    elements.exportModal.style.display = 'none';
  });
  
  // Close modal when clicking outside of it
  window.addEventListener('click', event => {
    if (event.target === elements.exportModal) {
      elements.exportModal.style.display = 'none';
    }
  });
  
  // Subject input handling
  elements.subjectSelect.addEventListener('change', () => {
    if (elements.subjectSelect.value) {
      elements.customSubjectInput.value = '';
    }
  });
  
  elements.customSubjectInput.addEventListener('input', () => {
    if (elements.customSubjectInput.value) {
      elements.subjectSelect.value = '';
    }
  });
}

/**
 * Handle form submission
 */
async function handleFormSubmit(event) {
  event.preventDefault();
  
  // Validate form
  const examBoard = elements.examBoardSelect.value;
  const examType = elements.examTypeSelect.value;
  const subject = elements.subjectSelect.value || elements.customSubjectInput.value;
  
  if (!examBoard || !examType || !subject) {
    showError('Please select an exam board, exam type, and subject.');
    return;
  }
  
  // Show loading state
  setLoadingState(true);
  elements.resultsPanel.style.display = 'block';
  elements.resultsContainer.style.display = 'none';
  elements.errorContainer.style.display = 'none';
  elements.loadingContainer.style.display = 'block';
  
  // Set result metadata
  elements.resultExamBoard.textContent = examBoard;
  elements.resultExamType.textContent = examType;
  elements.resultSubject.textContent = subject;
  
  try {
    // Make API request
    const response = await fetch('/api/generate-topics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        examBoard,
        examType,
        subject
      }),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'An error occurred while generating topics.');
    }
    
    // Update app state with new collection
    appState.currentCollection = data.collection;
    appState.collections.push(data.collection);
    
    // Display the results
    displayTopics(data.collection);
    updateSavedCollections();
    
    // Hide loading state
    setLoadingState(false);
  } catch (error) {
    console.error('Error generating topics:', error);
    
    // Show error message
    elements.loadingContainer.style.display = 'none';
    elements.errorContainer.style.display = 'block';
    elements.errorMessage.textContent = error.message || 'An error occurred. Please try again.';
    
    // Reset loading state
    setLoadingState(false);
  }
}

/**
 * Set loading state
 */
function setLoadingState(isLoading) {
  appState.isLoading = isLoading;
  elements.generateButton.disabled = isLoading;
  
  if (isLoading) {
    elements.generateButton.innerHTML = '<span class="spinner-small"></span> Generating...';
  } else {
    elements.generateButton.innerHTML = '<span class="icon">✨</span> Generate Topics';
  }
}

/**
 * Display topics in the results table
 */
function displayTopics(collection) {
  const { topics } = collection;
  
  // Clear existing topics
  elements.topicsBody.innerHTML = '';
  
  // Update count
  elements.topicsCount.textContent = topics.length;
  
  // Add topics to table
  topics.forEach(topic => {
    const row = document.createElement('tr');
    
    const idCell = document.createElement('td');
    idCell.textContent = topic.id;
    
    const topicCell = document.createElement('td');
    topicCell.textContent = topic.topic;
    
    const mainTopicCell = document.createElement('td');
    mainTopicCell.textContent = topic.mainTopic;
    
    const subtopicCell = document.createElement('td');
    subtopicCell.textContent = topic.subtopic;
    
    row.appendChild(idCell);
    row.appendChild(topicCell);
    row.appendChild(mainTopicCell);
    row.appendChild(subtopicCell);
    
    elements.topicsBody.appendChild(row);
  });
  
  // Show results
  elements.loadingContainer.style.display = 'none';
  elements.resultsContainer.style.display = 'block';
}

/**
 * Update saved collections list
 */
function updateSavedCollections() {
  const collections = appState.collections;
  
  if (collections.length === 0) {
    elements.noCollectionsMessage.style.display = 'block';
    elements.collectionsList.innerHTML = '';
    elements.bulkExportControls.style.display = 'none';
  } else {
    elements.noCollectionsMessage.style.display = 'none';
    elements.collectionsList.innerHTML = '';
    elements.bulkExportControls.style.display = 'block';
    
    collections.forEach((collection, index) => {
      const card = createCollectionCard(collection, index);
      elements.collectionsList.appendChild(card);
    });
  }
}

/**
 * Create a collection card
 */
function createCollectionCard(collection, index) {
  const card = document.createElement('div');
  card.className = 'collection-card';
  
  const title = document.createElement('h3');
  title.className = 'collection-title';
  title.textContent = `${collection.examBoard} ${collection.examType} ${collection.subject}`;
  
  const metadata = document.createElement('div');
  metadata.className = 'collection-metadata';
  metadata.innerHTML = `
    <span>Version: ${collection.version}</span>
    <span>Created: ${new Date(collection.createdAt).toLocaleDateString()}</span>
  `;
  
  const topicsCount = document.createElement('div');
  topicsCount.className = 'collection-topics-count';
  topicsCount.textContent = `${collection.topics.length} Topics`;
  
  const viewButton = document.createElement('button');
  viewButton.className = 'secondary-button';
  viewButton.textContent = 'View';
  viewButton.addEventListener('click', () => {
    appState.currentCollection = collection;
    displayTopics(collection);
    elements.resultsPanel.style.display = 'block';
    elements.resultExamBoard.textContent = collection.examBoard;
    elements.resultExamType.textContent = collection.examType;
    elements.resultSubject.textContent = collection.subject;
    
    // Scroll to results panel
    elements.resultsPanel.scrollIntoView({ behavior: 'smooth' });
  });
  
  const deleteButton = document.createElement('button');
  deleteButton.className = 'secondary-button';
  deleteButton.innerHTML = '<span class="icon">🗑️</span>';
  deleteButton.title = 'Delete Collection';
  deleteButton.addEventListener('click', () => {
    if (confirm(`Are you sure you want to delete this collection for ${collection.subject}?`)) {
      appState.collections.splice(index, 1);
      updateSavedCollections();
      
      // If the deleted collection is the currently displayed one, reset the results panel
      if (appState.currentCollection && appState.currentCollection.id === collection.id) {
        elements.resultsPanel.style.display = 'none';
        appState.currentCollection = null;
      }
    }
  });
  
  const actions = document.createElement('div');
  actions.className = 'collection-actions';
  actions.appendChild(viewButton);
  actions.appendChild(deleteButton);
  
  card.appendChild(title);
  card.appendChild(metadata);
  card.appendChild(topicsCount);
  card.appendChild(actions);
  
  return card;
}

/**
 * Export current collection
 */
async function exportCollection(format) {
  if (!appState.currentCollection) {
    showError('No collection to export.');
    return;
  }
  
  try {
    const response = await fetch('/api/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        collections: [appState.currentCollection],
        format: format === 'knack' ? 'csv' : format,
        filename: `${appState.currentCollection.examBoard.toLowerCase()}_${appState.currentCollection.examType.toLowerCase()}_${appState.currentCollection.subject.toLowerCase().replace(/\s+/g, '_')}`
      }),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'An error occurred during export.');
    }
    
    // Show export links in modal
    showExportLinks(data.exportedFiles, format);
  } catch (error) {
    console.error('Error exporting collection:', error);
    showError('Export failed: ' + (error.message || 'Unknown error'));
  }
}

/**
 * Bulk export all collections
 */
async function bulkExport(format) {
  if (appState.collections.length === 0) {
    showError('No collections to export.');
    return;
  }
  
  try {
    const response = await fetch('/api/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        collections: appState.collections,
        format: format === 'knack' ? 'csv' : format,
        filename: `all_topics_${new Date().toISOString().substring(0, 10)}`
      }),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'An error occurred during export.');
    }
    
    // Show export links in modal
    showExportLinks(data.exportedFiles, format);
  } catch (error) {
    console.error('Error bulk exporting collections:', error);
    showError('Bulk export failed: ' + (error.message || 'Unknown error'));
  }
}

/**
 * Show export links in modal
 */
function showExportLinks(files, format) {
  elements.exportLinks.innerHTML = '';
  
  // Create links based on export format
  if (format === 'json' || format === 'both' || format === 'knack') {
    if (files.json) {
      const jsonPath = files.json.split('/').pop();
      const li = document.createElement('li');
      li.innerHTML = `<a href="/output/json/${jsonPath}" download><span class="icon">📄</span> Download JSON</a>`;
      elements.exportLinks.appendChild(li);
    }
  }
  
  if (format === 'csv' || format === 'both' || format === 'knack') {
    if (files.csv) {
      const csvPath = files.csv.split('/').pop();
      const li = document.createElement('li');
      li.innerHTML = `<a href="/output/csv/${csvPath}" download><span class="icon">📊</span> Download CSV</a>`;
      elements.exportLinks.appendChild(li);
    }
  }
  
  if (format === 'knack') {
    if (files.knack) {
      const knackPath = files.knack.split('/').pop();
      const li = document.createElement('li');
      li.innerHTML = `<a href="/output/csv/${knackPath}" download><span class="icon">💾</span> Download Knack Format CSV</a>`;
      elements.exportLinks.appendChild(li);
    }
  }
  
  // Show modal
  elements.exportModal.style.display = 'flex';
}

/**
 * Show an error message
 */
function showError(message) {
  elements.loadingContainer.style.display = 'none';
  elements.resultsContainer.style.display = 'none';
  elements.errorContainer.style.display = 'block';
  elements.errorMessage.textContent = message;
  elements.resultsPanel.style.display = 'block';
}

/**
 * Reset the form
 */
function resetForm() {
  elements.resultsPanel.style.display = 'none';
  elements.form.reset();
  appState.currentCollection = null;
}

// Initialize the application
document.addEventListener('DOMContentLoaded', initApp);
