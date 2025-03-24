import { v4 as uuidv4 } from 'uuid';
import Topic from './Topic.js';

/**
 * Collection class to represent a set of curriculum topics
 */
class Collection {
  /**
   * Create a new Collection
   * @param {Object} params - Collection parameters
   * @param {string} params.examBoard - The exam board 
   * @param {string} params.examType - The exam type
   * @param {string} params.subject - The subject
   * @param {string} [params.version] - Optional version string
   * @param {Array<Topic|Object>} [params.topics] - Optional array of topics
   * @param {string} [params.id] - Optional collection ID (generated if not provided)
   */
  constructor({
    examBoard,
    examType,
    subject,
    version = null,
    topics = [],
    id = null
  }) {
    this.examBoard = examBoard;
    this.examType = examType;
    this.subject = subject;
    this.version = version || this.generateVersionString();
    this.id = id || this.generateId();
    this.createdAt = new Date().toISOString();
    this.updatedAt = this.createdAt;
    
    // Convert topic objects to Topic instances if needed
    this.topics = topics.map(topic => {
      if (topic instanceof Topic) {
        return topic;
      } else {
        return new Topic({
          ...topic,
          examBoard: this.examBoard,
          examType: this.examType,
          subject: this.subject
        });
      }
    });
  }

  /**
   * Generate a deterministic ID for the collection
   * @returns {string} - Generated ID
   */
  generateId() {
    if (this.examBoard && this.examType && this.subject) {
      const boardPrefix = this.examBoard.toLowerCase().substring(0, 3);
      const typePrefix = this.examType.toLowerCase().replace('-', '').substring(0, 4);
      const subjectPrefix = this.subject.toLowerCase().replace(/[^a-z0-9]/g, '').substring(0, 3);
      const timestamp = new Date().getTime().toString(36);
      
      return `c-${boardPrefix}-${typePrefix}-${subjectPrefix}-${timestamp}`;
    }
    
    return `c-${uuidv4()}`;
  }
  
  /**
   * Generate a version string for the collection
   * @returns {string} - Version string (YYYY.MM)
   */
  generateVersionString() {
    const now = new Date();
    return `${now.getFullYear()}.${(now.getMonth() + 1).toString().padStart(2, '0')}`;
  }
  
  /**
   * Add a topic to the collection
   * @param {Topic|Object} topic - Topic to add
   */
  addTopic(topic) {
    const topicInstance = topic instanceof Topic
      ? topic
      : new Topic({
          ...topic,
          examBoard: this.examBoard,
          examType: this.examType,
          subject: this.subject
        });
    
    this.topics.push(topicInstance);
    this.updatedAt = new Date().toISOString();
  }
  
  /**
   * Update the ID numbers for topics
   * This ensures sequential numbering (1.1, 1.2, etc.)
   */
  updateTopicIds() {
    // Group topics by main topic
    const mainTopicGroups = {};
    
    this.topics.forEach(topic => {
      const mainTopic = topic.mainTopic;
      if (!mainTopicGroups[mainTopic]) {
        mainTopicGroups[mainTopic] = [];
      }
      mainTopicGroups[mainTopic].push(topic);
    });
    
    // Assign new IDs
    let mainTopicCounter = 1;
    const updatedTopics = [];
    
    Object.keys(mainTopicGroups).sort().forEach(mainTopic => {
      const topics = mainTopicGroups[mainTopic];
      let subtopicCounter = 1;
      
      topics.forEach(topic => {
        const newId = `${mainTopicCounter}.${subtopicCounter}`;
        topic.id = newId;
        updatedTopics.push(topic);
        subtopicCounter++;
      });
      
      mainTopicCounter++;
    });
    
    this.topics = updatedTopics;
    this.updatedAt = new Date().toISOString();
  }
  
  /**
   * Convert the collection to a plain object
   * @returns {Object} - Plain object representation
   */
  toObject() {
    return {
      id: this.id,
      examBoard: this.examBoard,
      examType: this.examType,
      subject: this.subject,
      version: this.version,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      topics: this.topics.map(topic => topic.toObject())
    };
  }
  
  /**
   * Convert the collection to JSON
   * @returns {string} - JSON string
   */
  toJSON() {
    return JSON.stringify(this.toObject());
  }
  
  /**
   * Create a Collection from API response data
   * @param {Object} params - Parameters
   * @param {Array} params.topicsData - Topics from API
   * @param {string} params.examBoard - Exam board
   * @param {string} params.examType - Exam type
   * @param {string} params.subject - Subject
   * @returns {Collection} - New Collection instance
   */
  static fromAPIResponse({ topicsData, examBoard, examType, subject }) {
    const topics = topicsData.map(topicData => 
      Topic.fromAPIResponse(topicData, { examBoard, examType, subject })
    );
    
    return new Collection({
      examBoard,
      examType,
      subject,
      topics
    });
  }
}

export default Collection;
