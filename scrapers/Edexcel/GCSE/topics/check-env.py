"""
Quick Environment Checker
=========================

Checks if Supabase environment variables are properly configured.

Usage:
    python check-env.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")

print("=" * 80)
print("ENVIRONMENT VARIABLE CHECKER")
print("=" * 80)
print(f"\nChecking .env file at: {env_path}")
print()

if not env_path.exists():
    print("❌ .env file not found!")
    print(f"   Expected location: {env_path}")
    print("\nPlease create a .env file with:")
    print("   SUPABASE_URL=https://your-project.supabase.co")
    print("   SUPABASE_SERVICE_KEY=your-service-key")
    print("   (or SUPABASE_ANON_KEY=your-anon-key)")
    exit(1)

print("✅ .env file found")
load_dotenv(env_path)

# Check variables
supabase_url = os.getenv('SUPABASE_URL')
supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')

print("\nEnvironment Variables:")
print("-" * 80)

if supabase_url:
    print(f"✅ SUPABASE_URL: {supabase_url[:50]}...")
    # Check if URL looks valid
    if not supabase_url.startswith('http'):
        print("   ⚠️  WARNING: URL doesn't start with http/https")
    if 'supabase.co' not in supabase_url:
        print("   ⚠️  WARNING: URL doesn't contain 'supabase.co'")
else:
    print("❌ SUPABASE_URL: NOT SET")

if supabase_service_key:
    print(f"✅ SUPABASE_SERVICE_KEY: {supabase_service_key[:20]}... (length: {len(supabase_service_key)})")
elif supabase_anon_key:
    print(f"✅ SUPABASE_ANON_KEY: {supabase_anon_key[:20]}... (length: {len(supabase_anon_key)})")
else:
    print("❌ SUPABASE_SERVICE_KEY: NOT SET")
    print("❌ SUPABASE_ANON_KEY: NOT SET")
    print("   ⚠️  Need at least one of these!")

print("-" * 80)

# Test connection
if supabase_url and (supabase_service_key or supabase_anon_key):
    print("\nTesting Supabase connection...")
    try:
        from supabase import create_client
        key = supabase_service_key or supabase_anon_key
        client = create_client(supabase_url, key)
        print("✅ Supabase client created successfully!")
        print("\n✅ All checks passed! You're ready to run the scraper.")
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        print("\nPossible issues:")
        print("  1. Network connectivity problem")
        print("  2. Invalid Supabase URL")
        print("  3. Invalid API key")
        print("  4. Firewall blocking connection")
else:
    print("\n❌ Cannot test connection - missing environment variables")

print("=" * 80)

