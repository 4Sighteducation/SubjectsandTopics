/**
 * Simple Firecrawl API Test
 * Tests if your API key works
 */

import Firecrawl from '@mendable/firecrawl-js';
import dotenv from 'dotenv';

dotenv.config();

const FIRECRAWL_API_KEY = process.env.FIRECRAWL_API_KEY;

console.log('🔑 Testing Firecrawl API key...');
console.log('   Key starts with:', FIRECRAWL_API_KEY?.substring(0, 10) + '...');
console.log('   Key length:', FIRECRAWL_API_KEY?.length);

const fc = new Firecrawl({ apiKey: FIRECRAWL_API_KEY });

try {
  console.log('\n📡 Testing simple scrape...');
  const result = await fc.scrapeUrl('https://example.com', {
    formats: ['markdown']
  });
  
  console.log('✅ API KEY WORKS!');
  console.log('   Scraped example.com successfully');
  console.log('   Content length:', result.markdown?.length || 0);
  console.log('\n🎯 Your Firecrawl setup is correct!');
  console.log('   Ready to scrape AQA Biology');
  
} catch (error) {
  console.error('\n❌ API KEY FAILED:', error.message);
  console.log('\n🔍 Troubleshooting:');
  console.log('   1. Check https://firecrawl.dev/app/api-keys');
  console.log('   2. Verify your API key is active');
  console.log('   3. Check you have credits remaining');
  console.log('   4. Try creating a new API key');
  console.log('\nError details:', error);
}

