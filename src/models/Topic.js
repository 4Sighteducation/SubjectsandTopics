import { v4 as uuidv4 } from 'uuid';

/**
 * Topic class to represent a curriculum topic
 */
class Topic {
  /**
   * Create a new Topic
   * @param {Object} params - Topic parameters
   * @param {string} params.id - The hierarchical ID (e.g., "1.1")
   * @param {string} params.topic - The combined topic string
   * @param {string} params.mainTopic - The main topic
   * @param {string} params.subtopic - The subtopic
   * @param {string} [params.uuid] - Optional UUID (generated if not provided)
   * @param {string} [params.examBoard] - Optional exam board reference
   * @param {string} [params.examType] - Optional exam type reference
   * @param {string} [params.subject] - Optional subject reference
   */
  constructor({
    id,
    topic,
    mainTopic,
    subtopic,
    uuid = null,
    examBoard = null,
    examType = null,
    subject = null
  }) {
    this.id = id || '0.0';
    this.topic = topic || `${mainTopic}: ${subtopic}`;
    this.mainTopic = mainTopic || '';
    this.subtopic = subtopic || '';
    this.uuid = uuid || this.generateUuid(examBoard, examType, subject, id);
    this.examBoard = examBoard;
    this.examType = examType;
    this.subject = subject;
    this.createdAt = new Date().toISOString();
  }

  /**
   * Generate a deterministic UUID for the topic
   * @param {string} examBoard - Exam board
   * @param {string} examType - Exam type
   * @param {string} subject - Subject
   * @param {string} id - Hierarchical ID
   * @returns {string} - Generated UUID
   */
  generateUuid(examBoard, examType, subject, id) {
    // If we have all the metadata, create a deterministic ID
    if (examBoard && examType && subject && id) {
      const boardPrefix = examBoard.toLowerCase().substring(0, 3);
      const typePrefix = examType.toLowerCase().replace('-', '').substring(0, 4);
      const subjectPrefix = subject.toLowerCase().replace(/[^a-z0-9]/g, '').substring(0, 3);
      const normalizedId = id.replace('.', '-');
      
      return `t-${boardPrefix}-${typePrefix}-${subjectPrefix}-${normalizedId}-${this.shortRandomId()}`;
    }
    
    // Otherwise, use a random UUID
    return `t-${uuidv4()}`;
  }
  
  /**
   * Generate a short random ID (6 characters)
   * @returns {string} - Short random ID
   */
  shortRandomId() {
    return Math.random().toString(36).substring(2, 8);
  }
  
  /**
   * Convert the topic to a plain object
   * @returns {Object} - Plain object representation
   */
  toObject() {
    return {
      id: this.id,
      uuid: this.uuid,
      topic: this.topic,
      mainTopic: this.mainTopic,
      subtopic: this.subtopic,
      examBoard: this.examBoard,
      examType: this.examType,
      subject: this.subject,
      createdAt: this.createdAt
    };
  }
  
  /**
   * Convert the topic to JSON
   * @returns {string} - JSON string
   */
  toJSON() {
    return JSON.stringify(this.toObject());
  }
  
  /**
   * Create a Topic from an API response
   * @param {Object} data - API response data
   * @param {Object} metadata - Additional metadata
   * @returns {Topic} - New Topic instance
   */
  static fromAPIResponse(data, metadata = {}) {
    return new Topic({
      id: data.id,
      topic: data.topic,
      mainTopic: data.mainTopic,
      subtopic: data.subtopic,
      examBoard: metadata.examBoard,
      examType: metadata.examType,
      subject: metadata.subject
    });
  }
}

export default Topic;
