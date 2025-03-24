import fs from 'fs';
import path from 'path';
import { createObjectCsvWriter } from 'csv-writer';
import config from '../config.js';

/**
 * Utility for exporting collections to CSV files
 */
class CsvExporter {
  /**
   * Create a new CsvExporter
   * @param {string} [outputDir] - Optional custom output directory
   */
  constructor(outputDir = null) {
    this.outputDir = outputDir || config.output.csvDir;
    this.ensureDirectoryExists();
    
    // Default CSV headers
    this.defaultHeaders = [
      { id: 'id', title: 'ID' },
      { id: 'uuid', title: 'UUID' },
      { id: 'topic', title: 'Topic' },
      { id: 'mainTopic', title: 'Main Topic' },
      { id: 'subtopic', title: 'Subtopic' },
      { id: 'examBoard', title: 'Exam Board' },
      { id: 'examType', title: 'Exam Type' },
      { id: 'subject', title: 'Subject' },
      { id: 'collectionId', title: 'Collection ID' },
      { id: 'createdAt', title: 'Created At' }
    ];
  }

  /**
   * Ensure the output directory exists
   */
  ensureDirectoryExists() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  /**
   * Generate a filename for a collection
   * @param {Object} collection - The collection to export
   * @returns {string} - Generated filename
   */
  generateFilename(collection) {
    const { examBoard, examType, subject } = collection;
    const sanitizedSubject = subject.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    return `${examBoard.toLowerCase()}_${examType.toLowerCase()}_${sanitizedSubject}_${timestamp}.csv`;
  }

  /**
   * Export a collection to CSV file
   * @param {Object} collection - The collection to export
   * @param {string} [filename] - Optional custom filename
   * @returns {Promise<string>} - Path to exported file
   */
  async exportCollection(collection, filename = null) {
    const outputFilename = filename || this.generateFilename(collection);
    const outputPath = path.join(this.outputDir, outputFilename);
    
    // Process collection data
    const records = this.processCollectionForCsv(collection);
    
    // Create CSV writer
    const csvWriter = createObjectCsvWriter({
      path: outputPath,
      header: this.defaultHeaders
    });
    
    // Write to file
    await csvWriter.writeRecords(records);
    
    console.log(`Collection exported to ${outputPath}`);
    return outputPath;
  }

  /**
   * Export multiple collections to CSV files
   * @param {Array<Object>} collections - The collections to export
   * @returns {Promise<Array<string>>} - Paths to exported files
   */
  async exportCollections(collections) {
    const results = [];
    
    for (const collection of collections) {
      const path = await this.exportCollection(collection);
      results.push(path);
    }
    
    return results;
  }

  /**
   * Export a flattened list of all topics from multiple collections
   * @param {Array<Object>} collections - The collections to export
   * @param {string} [filename] - Optional custom filename
   * @returns {Promise<string>} - Path to exported file
   */
  async exportFlattenedTopics(collections, filename = null) {
    const allRecords = [];
    
    // Extract topics from all collections
    collections.forEach(collection => {
      const { examBoard, examType, subject, id: collectionId } = collection;
      
      (collection.topics || []).forEach(topic => {
        let topicData = topic;
        
        // If topic is an object with toObject method, convert it
        if (topic.toObject && typeof topic.toObject === 'function') {
          topicData = topic.toObject();
        }
        
        // Add collection info to each topic
        allRecords.push({
          ...topicData,
          examBoard,
          examType,
          subject,
          collectionId
        });
      });
    });
    
    // Generate filename if not provided
    const outputFilename = filename || `all_topics_${new Date().toISOString().replace(/[:.]/g, '-')}.csv`;
    const outputPath = path.join(this.outputDir, outputFilename);
    
    // Create CSV writer
    const csvWriter = createObjectCsvWriter({
      path: outputPath,
      header: this.defaultHeaders
    });
    
    // Write to file
    await csvWriter.writeRecords(allRecords);
    
    console.log(`Flattened topics exported to ${outputPath}`);
    return outputPath;
  }

  /**
   * Export data using custom headers
   * @param {Array<Object>} data - The data to export
   * @param {Array<Object>} headers - The headers configuration
   * @param {string} filename - The filename
   * @returns {Promise<string>} - Path to exported file
   */
  async exportCustomData(data, headers, filename) {
    const outputPath = path.join(this.outputDir, filename);
    
    // Create CSV writer
    const csvWriter = createObjectCsvWriter({
      path: outputPath,
      header: headers
    });
    
    // Write to file
    await csvWriter.writeRecords(data);
    
    console.log(`Data exported to ${outputPath}`);
    return outputPath;
  }

  /**
   * Process a collection for CSV export
   * @param {Object} collection - The collection to process
   * @returns {Array<Object>} - Records ready for CSV export
   */
  processCollectionForCsv(collection) {
    const { examBoard, examType, subject, id: collectionId } = collection;
    
    // Process topics
    return (collection.topics || []).map(topic => {
      let topicData = topic;
      
      // If topic is an object with toObject method, convert it
      if (topic.toObject && typeof topic.toObject === 'function') {
        topicData = topic.toObject();
      }
      
      // Add collection info to each topic
      return {
        ...topicData,
        examBoard,
        examType,
        subject,
        collectionId
      };
    });
  }
  
  /**
   * Generate CSV in Knack-friendly format
   * @param {Array<Object>} collections - Collections to export
   * @param {string} [filename] - Optional custom filename
   * @returns {Promise<string>} - Path to exported file
   */
  async exportForKnack(collections, filename = null) {
    // Knack-specific headers
    const knackHeaders = [
      { id: 'uuid', title: 'Topic UUID' },
      { id: 'id', title: 'Topic ID' },
      { id: 'topic', title: 'Topic Display Name' },
      { id: 'mainTopic', title: 'Main Topic' },
      { id: 'subtopic', title: 'Subtopic' },
      { id: 'examBoard', title: 'Exam Board' },
      { id: 'examType', title: 'Exam Type' },
      { id: 'subject', title: 'Subject' },
      { id: 'collectionId', title: 'Collection ID' }
    ];
    
    const allRecords = [];
    
    // Extract topics from all collections
    collections.forEach(collection => {
      const { examBoard, examType, subject, id: collectionId } = collection;
      
      (collection.topics || []).forEach(topic => {
        let topicData = topic;
        
        // If topic is an object with toObject method, convert it
        if (topic.toObject && typeof topic.toObject === 'function') {
          topicData = topic.toObject();
        }
        
        // Add collection info to each topic
        allRecords.push({
          ...topicData,
          examBoard,
          examType,
          subject,
          collectionId
        });
      });
    });
    
    // Generate filename if not provided
    const outputFilename = filename || `knack_import_${new Date().toISOString().replace(/[:.]/g, '-')}.csv`;
    
    return this.exportCustomData(allRecords, knackHeaders, outputFilename);
  }
}

// Export a singleton instance
const csvExporter = new CsvExporter();
export default csvExporter;
