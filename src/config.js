import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

// Load environment variables
dotenv.config();

// Get directory name in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const config = {
  // API Configuration
  api: {
    openrouter: {
      key: process.env.OPENROUTER_API_KEY,
      baseUrl: 'https://openrouter.ai/api/v1',
      defaultModel: 'anthropic/claude-3-opus', // Can be changed to sonnet, haiku, etc.
      timeout: 120000, // 2 minutes
    }
  },
  
  // Server Configuration
  server: {
    port: process.env.PORT || 3000,
    environment: process.env.NODE_ENV || 'development',
  },
  
  // Output Configuration
  output: {
    directory: process.env.OUTPUT_DIR || path.join(__dirname, '..', 'output'),
    jsonDir: path.join(process.env.OUTPUT_DIR || path.join(__dirname, '..', 'output'), 'json'),
    csvDir: path.join(process.env.OUTPUT_DIR || path.join(__dirname, '..', 'output'), 'csv'),
  },
  
  // Rate Limiting
  rateLimit: {
    maxRequestsPerMinute: 10,
    maxConcurrentRequests: 2,
  },
  
  // Data Configuration
  data: {
    // Exam boards
    examBoards: [
      { id: 'aqa', name: 'AQA' },
      { id: 'edexcel', name: 'Edexcel' },
      { id: 'ocr', name: 'OCR' },
      { id: 'wjec', name: 'WJEC/Eduqas' },
      { id: 'sqa', name: 'SQA' },
      { id: 'ib', name: 'International Baccalaureate' },
      { id: 'cambridge', name: 'Cambridge International' }
    ],
    
    // Exam types
    examTypes: [
      { id: 'gcse', name: 'GCSE' },
      { id: 'alevel', name: 'A-Level' },
      { id: 'as', name: 'AS-Level' },
      { id: 'ib', name: 'International Baccalaureate' },
      { id: 'nat5', name: 'National 5' },
      { id: 'higher', name: 'Higher' },
      { id: 'advhigher', name: 'Advanced Higher' },
      { id: 'btec2', name: 'BTEC Level 2' },
      { id: 'btec3', name: 'BTEC Level 3' }
    ],
    
    // Common subjects
    commonSubjects: [
      // Sciences
      'Biology', 'Chemistry', 'Physics', 'Combined Science',
      
      // Humanities
      'History', 'Geography', 'Religious Studies', 'Sociology', 'Psychology',
      
      // Languages
      'English Language', 'English Literature', 'French', 'Spanish', 'German',
      
      // Mathematics
      'Mathematics', 'Further Mathematics', 'Statistics',
      
      // Arts
      'Art and Design', 'Drama', 'Music', 'Dance',
      
      // Others
      'Business Studies', 'Economics', 'Computer Science', 'Physical Education'
    ]
  }
};

export default config;
