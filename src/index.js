import express from 'express';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import morgan from 'morgan';
import open from 'open';
import config from './config.js';
import anthropicAPI from './api/anthropic.js';
import { generateTopicPrompt } from './prompts/topicPrompt.js';
import Collection from './models/Collection.js';
import Topic from './models/Topic.js';
import jsonExporter from './exporters/jsonExporter.js';
import csvExporter from './exporters/csvExporter.js';

// Set up __dirname for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize Express app
const app = express();
const port = config.server.port;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev')); // Logging

// Serve static files from the ui directory
app.use(express.static(path.join(__dirname, 'ui')));

// API endpoints

/**
 * GET /api/config
 * Returns configuration data for the frontend
 */
app.get('/api/config', (req, res) => {
  // Send a safe subset of the config
  res.json({
    examBoards: config.data.examBoards,
    examTypes: config.data.examTypes,
    commonSubjects: config.data.commonSubjects,
    apiStatus: !!config.api.openrouter.key
  });
});

/**
 * POST /api/generate-topics
 * Generates topics using Claude API
 */
app.post('/api/generate-topics', async (req, res) => {
  try {
    const { examBoard, examType, subject } = req.body;
    
    // Validate required parameters
    if (!examBoard || !examType || !subject) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameters: examBoard, examType, and subject are required'
      });
    }
    
    console.log(`Generating topics for ${examBoard} ${examType} ${subject}...`);
    
    // Generate the prompt
    const prompt = generateTopicPrompt(examBoard, examType, subject);
    
    // Call the API
    const apiResponse = await anthropicAPI.generateTopics(prompt);
    
    // Parse the response
    const topicsData = anthropicAPI.constructor.parseTopicResponse(apiResponse);
    
    // Create a collection with the generated topics
    const collection = Collection.fromAPIResponse({ 
      topicsData,
      examBoard,
      examType,
      subject
    });
    
    // Update topic IDs to ensure they are sequential
    collection.updateTopicIds();
    
    // Return the collection
    res.json({
      success: true,
      collection: collection.toObject()
    });
  } catch (error) {
    console.error('Error generating topics:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/export
 * Exports collections in JSON and/or CSV format
 */
app.post('/api/export', async (req, res) => {
  try {
    const { collections, format, filename } = req.body;
    
    // Validate collections
    if (!collections || !Array.isArray(collections) || collections.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No collections provided or invalid collections format'
      });
    }
    
    // Convert plain objects to Collection instances
    const collectionInstances = collections.map(coll => 
      new Collection({
        id: coll.id,
        examBoard: coll.examBoard,
        examType: coll.examType,
        subject: coll.subject,
        version: coll.version,
        topics: coll.topics.map(t => new Topic(t)),
      })
    );
    
    // Determine export format (default to both)
    const exportFormat = format || 'both';
    let jsonPath, csvPath;
    
    // Export based on format
    if (exportFormat === 'json' || exportFormat === 'both') {
      jsonPath = await jsonExporter.exportFlattenedTopics(collectionInstances, filename ? `${filename}.json` : null);
    }
    
    if (exportFormat === 'csv' || exportFormat === 'both') {
      csvPath = await csvExporter.exportFlattenedTopics(collectionInstances, filename ? `${filename}.csv` : null);
    }
    
    // Also export in Knack-friendly format
    const knackPath = await csvExporter.exportForKnack(collectionInstances, filename ? `${filename}_knack.csv` : null);
    
    res.json({
      success: true,
      exportedFiles: {
        json: jsonPath,
        csv: csvPath,
        knack: knackPath
      }
    });
  } catch (error) {
    console.error('Error exporting collections:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /output/:type/:filename
 * Download a generated file
 */
app.get('/output/:type/:filename', (req, res) => {
  try {
    const { type, filename } = req.params;
    
    // Validate type
    if (type !== 'json' && type !== 'csv') {
      return res.status(400).json({
        success: false,
        error: 'Invalid file type'
      });
    }
    
    // Determine file path
    const filePath = path.join(
      type === 'json' ? config.output.jsonDir : config.output.csvDir,
      filename
    );
    
    // Check if file exists
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({
        success: false,
        error: 'File not found'
      });
    }
    
    // Send file
    res.download(filePath);
  } catch (error) {
    console.error('Error downloading file:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    success: false,
    error: err.message || 'Internal Server Error'
  });
});

// Start server
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
  
  // Open the browser automatically in development mode
  if (config.server.environment === 'development') {
    open(`http://localhost:${port}`);
  }
});

// Create placeholder files for output directories to track them in git
const createPlaceholder = (dir) => {
  const placeholderPath = path.join(dir, '.gitkeep');
  if (!fs.existsSync(placeholderPath)) {
    fs.writeFileSync(placeholderPath, '# This file exists to track the directory in Git\n');
  }
};

createPlaceholder(config.output.jsonDir);
createPlaceholder(config.output.csvDir);
