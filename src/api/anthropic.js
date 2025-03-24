import axios from 'axios';
import config from '../config.js';

/**
 * Class to interact with Anthropic's Claude API via OpenRouter
 */
class AnthropicAPI {
  constructor() {
    this.baseUrl = config.api.openrouter.baseUrl;
    this.model = config.api.openrouter.defaultModel;
    this.apiKey = config.api.openrouter.key;
    this.timeout = config.api.openrouter.timeout;
    
    // Request queue for rate limiting
    this.requestQueue = [];
    this.processingQueue = false;
    this.requestsThisMinute = 0;
    this.requestsResetTimeout = null;
    
    // Reset request counter every minute
    this.resetRequestCounter();
  }
  
  /**
   * Reset the request counter every minute
   */
  resetRequestCounter() {
    if (this.requestsResetTimeout) {
      clearTimeout(this.requestsResetTimeout);
    }
    
    this.requestsResetTimeout = setTimeout(() => {
      this.requestsThisMinute = 0;
      this.resetRequestCounter();
    }, 60000); // 1 minute
  }
  
  /**
   * Process the request queue respecting rate limits
   */
  async processQueue() {
    if (this.processingQueue || this.requestQueue.length === 0) {
      return;
    }
    
    this.processingQueue = true;
    
    while (this.requestQueue.length > 0) {
      // Check if we're under rate limits
      if (this.requestsThisMinute >= config.rateLimit.maxRequestsPerMinute) {
        console.log(`Rate limit reached (${this.requestsThisMinute}/${config.rateLimit.maxRequestsPerMinute}). Waiting...`);
        // Wait for the next minute to reset the counter
        await new Promise(resolve => setTimeout(resolve, 5000));
        continue;
      }
      
      const { prompt, resolve, reject } = this.requestQueue.shift();
      
      try {
        this.requestsThisMinute++;
        const result = await this.makeApiCall(prompt);
        resolve(result);
      } catch (error) {
        reject(error);
      }
      
      // Small delay between requests
      await new Promise(r => setTimeout(r, 1000));
    }
    
    this.processingQueue = false;
  }
  
  /**
   * Make the actual API call to OpenRouter for Claude
   * @param {string} prompt - The prompt to send to Claude
   * @returns {Promise<object>} - The response from Claude
   */
  async makeApiCall(prompt) {
    try {
      const response = await axios({
        method: 'post',
        url: `${this.baseUrl}/chat/completions`,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          'HTTP-Referer': 'https://4sighteducation.com', // Required by OpenRouter
          'X-Title': 'Curriculum Topic Generator'
        },
        data: {
          model: this.model,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ],
          temperature: 0.1, // Lower temperature for more deterministic results
          top_p: 0.95,
          max_tokens: 1500, // Adjust as needed based on expected response size
        },
        timeout: this.timeout
      });
      
      if (response.status !== 200) {
        throw new Error(`API returned status code ${response.status}: ${response.statusText}`);
      }
      
      return response.data;
    } catch (error) {
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error('API Error Response:', error.response.data);
        throw new Error(`API error (${error.response.status}): ${error.response.data.error?.message || 'Unknown error'}`);
      } else if (error.request) {
        // The request was made but no response was received
        console.error('API Request Error:', error.request);
        throw new Error('No response received from API');
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('API Setup Error:', error.message);
        throw new Error(`API setup error: ${error.message}`);
      }
    }
  }
  
  /**
   * Generate curriculum topics using Claude
   * @param {string} prompt - The formatted prompt for topic generation
   * @returns {Promise<object>} - The parsed topic list
   */
  generateTopics(prompt) {
    return new Promise((resolve, reject) => {
      // Add request to queue
      this.requestQueue.push({ prompt, resolve, reject });
      
      // Start processing the queue if not already running
      if (!this.processingQueue) {
        this.processQueue();
      }
    });
  }
  
  /**
   * Extract and parse the topic list from Claude's response
   * @param {object} response - The response from Claude
   * @returns {Array} - The parsed topic list
   */
  static parseTopicResponse(response) {
    try {
      if (!response?.choices || !response.choices[0]?.message?.content) {
        throw new Error('Invalid API response structure');
      }
      
      const content = response.choices[0].message.content.trim();
      
      // Try to find and extract JSON from the response
      let jsonMatch = content.match(/\[\s*\{.*\}\s*\]/s);
      if (!jsonMatch) {
        throw new Error('No valid JSON array found in response');
      }
      
      const jsonStr = jsonMatch[0];
      return JSON.parse(jsonStr);
    } catch (error) {
      console.error('Error parsing topic response:', error);
      throw new Error(`Failed to parse topic response: ${error.message}`);
    }
  }
}

// Export a singleton instance
const anthropicAPI = new AnthropicAPI();
export default anthropicAPI;
