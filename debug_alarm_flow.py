#!/usr/bin/env python3
"""
Debug script to test alarm flow for a specific city and UUID
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import get_config
from core.db.database import get_db
from core.polygons import get_polygon_registry
from core.checks.login_check import LoginCheck
from core.notifications import get_notification_manager
import pymysql

def debug_alarm_flow(city_code, test_uuid=None):
    """Debug the complete alarm flow for a city"""
    
    print(f"\n{'='*60}")
    print(f"DEBUGGING ALARM FLOW FOR CITY: {city_code}")
    print(f"{'='*60}\n")
    
    # 1. Check city config
    print("✓ STEP 1: Check City Configuration")
    print("-" * 60)
    config = get_config()
    city_config = config.get_city_config(city_code)
    
    if not city_config:
        print(f"❌ FAILED: City '{city_code}' not found in config!")
        print(f"Available cities: {config.city_codes}")
        return
    
    print(f"✓ City loaded: {city_config.city_code}")
    print(f"  - Language: {city_config.language.default}")
    print(f"  - Zones: {city_config.zones}")
    print(f"  - Login check enabled: {city_config.checks.get('login_check', {}).enabled if hasattr(city_config.checks.get('login_check', {}), 'enabled') else city_config.checks.get('login_check', {}).get('enabled')}")
    
    # 2. Check database connectivity and recent data
    print(f"\n✓ STEP 2: Check Database Activity")
    print("-" * 60)
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    
    query = """
    SELECT location, status, COUNT(*) as count, MAX(ts) as latest
    FROM uber_activity_log_live 
    WHERE location = %s
    AND ts > DATE_SUB(NOW(), INTERVAL 10 MINUTE)
    GROUP BY location, status
    """
    cursor.execute(query, (city_config.city_code,))
    results = cursor.fetchall()
    
    if not results:
        print(f"❌ WARNING: No recent activity found for city '{city_config.city_code}' in last 10 minutes")
        print(f"   Check if 'location' column in uber_activity_log_live matches: '{city_config.city_code}'")
    else:
        print(f"✓ Found recent activity:")
        for row in results:
            print(f"  - Status: {row['status']}, Count: {row['count']}, Latest: {row['latest']}")
    
    # 3. Check polygons
    print(f"\n✓ STEP 3: Check Polygon Files")
    print("-" * 60)
    cities_dir = Path(__file__).parent / "cities" / city_code.lower()
    
    for zone in city_config.zones:
        zone_path = cities_dir / "polygons" / zone
        if zone_path.exists():
            geojson_files = list(zone_path.glob("*.geojson"))
            print(f"✓ {zone}: {len(geojson_files)} polygon file(s)")
            if not geojson_files:
                print(f"  ⚠️  WARNING: No .geojson files in {zone_path}")
        else:
            print(f"❌ {zone}: Directory not found at {zone_path}")
    
    # 4. Test polygon loading
    print(f"\n✓ STEP 4: Test Polygon Loading")
    print("-" * 60)
    try:
        registry = get_polygon_registry()
        city_dir_name = config.resolve_city_dir_by_code(city_config.city_code) or city_code.lower()
        cities_base = str(Path(__file__).parent / "cities")
        registry.load_city(city_config.city_code, cities_base, city_dir_name)
        print(f"✓ Polygons loaded successfully for {city_config.city_code}")
    except Exception as e:
        print(f"❌ FAILED to load polygons: {e}")
    
    # 5. Check user (if UUID provided)
    if test_uuid:
        print(f"\n✓ STEP 5: Check Test User: {test_uuid}")
        print("-" * 60)
        query = """
        SELECT uuid_id, first_name, prefix, phone, telegram_id, telegram_language
        FROM users 
        WHERE uuid_id = %s
        """
        cursor.execute(query, (test_uuid,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ FAILED: User '{test_uuid}' not found in users table")
        else:
            print(f"✓ User found:")
            print(f"  - Name: {user.get('first_name', 'N/A')}")
            print(f"  - Telegram ID: {user.get('telegram_id', 'NOT SET')}")
            print(f"  - Phone: {user.get('prefix', '')}{user.get('phone', 'NOT SET')}")
            print(f"  - Language: {user.get('telegram_language', 'N/A')}")
            
            if not user.get('telegram_id') and not user.get('phone'):
                print(f"  ⚠️  WARNING: User has neither telegram_id nor phone - cannot send notifications!")
    
    # 6. Check notification templates
    print(f"\n✓ STEP 6: Check Notification Templates")
    print("-" * 60)
    templates_dir = Path(__file__).parent / "core" / "notifications" / "templates"
    lang = city_config.language.default
    
    template_files = [
        "login_outside_zone.txt",
        "login_inside_zone.txt",
        "not_waiting_in_center.txt",
        "not_delivering_in_zone.txt"
    ]
    
    for template in template_files:
        tg_path = templates_dir / "telegram" / lang / template
        sms_path = templates_dir / "sms" / lang / template
        
        tg_exists = "✓" if tg_path.exists() else "❌"
        sms_exists = "✓" if sms_path.exists() else "❌"
        print(f"  {template}: Telegram {tg_exists} | SMS {sms_exists}")
    
    # 7. Check environment variables
    print(f"\n✓ STEP 7: Check Environment Variables")
    print("-" * 60)
    import os
    env_vars = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'DB_HOST': os.getenv('DB_HOST', ''),
        'DB_USER': os.getenv('DB_USER', ''),
        'DB_NAME': os.getenv('DB_NAME', ''),
        'APP_ENV': os.getenv('APP_ENV', 'production'),
    }
    
    for key, value in env_vars.items():
        status = "✓" if value else "❌ NOT SET"
        masked = value[:10] + "..." if len(value) > 10 else value
        print(f"  {key}: {status} ({masked if value else 'MISSING'})")
    
    cursor.close()
    
    print(f"\n{'='*60}")
    print("DEBUGGING COMPLETE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_alarm_flow.py <CITY_CODE> [UUID]")
        print("Example: python debug_alarm_flow.py BASEL 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)
    
    city = sys.argv[1]
    uuid = sys.argv[2] if len(sys.argv) > 2 else None
    
    debug_alarm_flow(city, uuid)
