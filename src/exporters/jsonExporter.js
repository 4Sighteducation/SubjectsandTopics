import fs from 'fs';
import path from 'path';
import config from '../config.js';

/**
 * Utility for exporting collections to JSON files
 */
class JsonExporter {
  /**
   * Create a new JsonExporter
   * @param {string} [outputDir] - Optional custom output directory
   */
  constructor(outputDir = null) {
    this.outputDir = outputDir || config.output.jsonDir;
    this.ensureDirectoryExists();
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
    const { examBoard, examType, subject, id } = collection;
    const sanitizedSubject = subject.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    return `${examBoard.toLowerCase()}_${examType.toLowerCase()}_${sanitizedSubject}_${timestamp}.json`;
  }

  /**
   * Export a collection to JSON file
   * @param {Object} collection - The collection to export
   * @param {string} [filename] - Optional custom filename
   * @returns {string} - Path to exported file
   */
  exportCollection(collection, filename = null) {
    const outputFilename = filename || this.generateFilename(collection);
    const outputPath = path.join(this.outputDir, outputFilename);
    
    // Convert collection to a JSON object
    const data = collection.toObject ? collection.toObject() : collection;
    
    // Write to file
    fs.writeFileSync(outputPath, JSON.stringify(data, null, 2));
    
    console.log(`Collection exported to ${outputPath}`);
    return outputPath;
  }

  /**
   * Export multiple collections to JSON files
   * @param {Array<Object>} collections - The collections to export
   * @returns {Array<string>} - Paths to exported files
   */
  exportCollections(collections) {
    return collections.map(collection => this.exportCollection(collection));
  }

  /**
   * Export a JSON array to file
   * @param {Array<Object>} data - The data to export
   * @param {string} filename - The filename
   * @returns {string} - Path to exported file
   */
  exportData(data, filename) {
    const outputPath = path.join(this.outputDir, filename);
    
    // Write to file
    fs.writeFileSync(outputPath, JSON.stringify(data, null, 2));
    
    console.log(`Data exported to ${outputPath}`);
    return outputPath;
  }

  /**
   * Export a flattened list of all topics from multiple collections
   * @param {Array<Object>} collections - The collections to export
   * @param {string} [filename] - Optional custom filename
   * @returns {string} - Path to exported file
   */
  exportFlattenedTopics(collections, filename = null) {
    const allTopics = [];
    
    // Extract topics from all collections
    collections.forEach(collection => {
      const { examBoard, examType, subject } = collection;
      
      (collection.topics || []).forEach(topic => {
        // Add collection info to each topic
        allTopics.push({
          ...topic,
          examBoard,
          examType,
          subject,
          collectionId: collection.id
        });
      });
    });
    
    // Generate filename if not provided
    const outputFilename = filename || `all_topics_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    
    return this.exportData(allTopics, outputFilename);
  }
}

// Export a singleton instance
const jsonExporter = new JsonExporter();
export default jsonExporter;
