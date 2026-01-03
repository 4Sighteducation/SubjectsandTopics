#!/usr/bin/env python3
"""
Run database migration: staging → production
Moves Edexcel data to production tables so FLASH app can use it
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment
load_dotenv()

def run_migration():
    """Execute the migration SQL"""
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Need service role for migrations
    
    if not url or not key:
        print("❌ Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env file")
        print("\nPlease add to .env file:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_SERVICE_ROLE_KEY=your-service-role-key")
        sys.exit(1)
    
    print("🚀 Starting migration: staging → production")
    print(f"📡 Connecting to: {url}")
    
    # Create client
    supabase: Client = create_client(url, key)
    
    # Read SQL file
    sql_file = os.path.join(os.path.dirname(__file__), 
                           'database', 'migrations', 'migrate-staging-to-production.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ Error: SQL file not found: {sql_file}")
        sys.exit(1)
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"📄 Read SQL file: {len(sql)} characters")
    
    # Split SQL into individual statements (rough split on semicolons)
    # Note: This is a simple approach - more complex SQL might need better parsing
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"🔧 Executing {len(statements)} SQL statements...")
    
    try:
        # Execute the migration
        # Note: Supabase Python client doesn't have direct SQL execution
        # We need to use RPC or REST API
        
        # For now, let's use the PostgREST API directly
        import requests
        
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Execute via RPC if you have a function, or use psycopg2
        print("\n⚠️  Note: Supabase Python client doesn't support direct SQL execution")
        print("📋 Please run the SQL file manually in Supabase SQL Editor:")
        print(f"\n   File: {sql_file}")
        print("\nSteps:")
        print("1. Open Supabase Dashboard")
        print("2. Go to SQL Editor")
        print("3. Click 'New Query'")
        print("4. Copy the SQL from the file above")
        print("5. Click 'Run'")
        print("\n✅ The script will show verification results at the end")
        
        # Alternative: Check if we can verify the data is there
        print("\n🔍 Checking current data...")
        
        # Check if Edexcel exists
        response = supabase.table('exam_boards').select('*').eq('code', 'Edexcel').execute()
        if response.data:
            print("✅ Edexcel exam board found")
        else:
            print("❌ Edexcel exam board not found - migration not run yet")
        
        # Check subjects
        response = supabase.table('exam_board_subjects').select('id', count='exact').eq('exam_board_id', 
            supabase.table('exam_boards').select('id').eq('code', 'Edexcel').execute().data[0]['id'] if response.data else None
        ).execute()
        
        if response.count:
            print(f"✅ Found {response.count} Edexcel subjects in production")
        else:
            print("❌ No Edexcel subjects in production - migration needed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()



