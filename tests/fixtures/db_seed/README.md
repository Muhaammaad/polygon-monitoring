# Test Fixtures - Database Seed Scripts

## Overview
These SQL scripts provide deterministic test data for validating the login_check functionality according to V2 requirements (Section 13).

## Files

### 1. seed_users_simple.sql
Creates three test users for login_check validation:
- `uuid-in`: User who logs in INSIDE the polygon
- `uuid-out`: User who logs in OUTSIDE the polygon  
- `uuid-old`: User who is NOT a new login (has older activity)

### 2. seed_login_check_simple.sql
Seeds `uber_activity_log_live` with activity records:
- **uuid-in**: NEW login at (lat: 46.5200, lon: 6.6200) - INSIDE polygon
- **uuid-out**: NEW login at (lat: 46.5200, lon: 7.7000) - OUTSIDE polygon
- **uuid-old**: Has older activity (30 min ago) + recent login → NOT considered "new"

### 3. cleanup_simple.sql
Removes all test data after validation.

## Test Polygon
The test polygon is defined in: `cities/test_city/polygons/login_zone/simple_login_zone.csv`

```
POLYGON((6.60 46.50, 6.64 46.50, 6.64 46.54, 6.60 46.54, 6.60 46.50))
```

**Bounds**:
- Longitude: 6.60 to 6.64
- Latitude: 46.50 to 46.54

## Usage

### 1. Load Test Data
```bash
mysql -u root -p onduty_bi < tests/fixtures/db_seed/seed_users_simple.sql
mysql -u root -p onduty_bi < tests/fixtures/db_seed/seed_login_check_simple.sql
```

### 2. Run Login Check
```bash
python -c "from core.checks.login_check import LoginCheck; from core.config import get_config; city = get_config().get_city_config('TEST'); check = LoginCheck(); results = check.execute(city); print(f'{len(results)} warnings generated'); [print(f\"  {r['uuid']}: {r['note']}\") for r in results]"
```

### 3. Verify Results
```bash
mysql -u root -p onduty_bi -e "SELECT driver_id, note FROM uber_warnings WHERE driver_id IN ('uuid-in','uuid-out','uuid-old')"
```

### 4. Cleanup
```bash
mysql -u root -p onduty_bi < tests/fixtures/db_seed/cleanup_simple.sql
```

## Expected Results

### Query Output
The login candidate query MUST return:
- ✅ `uuid-in`
- ✅ `uuid-out`

The query MUST NOT return:
- ❌ `uuid-old` (excluded due to older activity)

### Warnings Generated

| UUID | Expected Warning | Reason |
|------|-----------------|---------|
| uuid-in | `login_inside_zone` | Inside polygon, new login |
| uuid-out | `login_outside_zone` | Outside polygon, new login |
| uuid-old | *no warning* | NOT a new login (has older record) |

## Verification Query

### Check Candidates
```sql
SELECT DISTINCT t1.uuid
FROM uber_activity_log_live t1
WHERE t1.ts BETWEEN NOW() - INTERVAL 3 MINUTE AND NOW()
AND t1.location = 'TEST'
AND NOT EXISTS (
  SELECT 1
  FROM uber_activity_log_live t2
  WHERE t2.uuid = t1.uuid
  AND t2.location = 'TEST'
  AND t2.ts BETWEEN NOW() - INTERVAL 2 HOUR AND NOW() - INTERVAL 3 MINUTE
);
```

**Expected Output**: `uuid-in`, `uuid-out`

### Check Warnings
```sql
SELECT driver_id, note
FROM uber_warnings
WHERE driver_id IN ('uuid-in','uuid-out','uuid-old');
```

**Expected Output**:
```
+------------+---------------------+
| driver_id  | note                |
+------------+---------------------+
| uuid-in    | login_inside_zone   |
| uuid-out   | login_outside_zone  |
+------------+---------------------+
```

## CI Integration

These scripts are designed for automated CI testing:

1. Spin up MySQL (Docker/Testcontainers)
2. Apply seed scripts
3. Execute login_check
4. Verify warnings match expected results
5. Cleanup

CI MUST fail if expected results don't match.

## Notes

- All timestamps use `NOW()` with intervals for determinism
- City code is `TEST` matching `cities/test_city/config.yaml`
- Polygon coordinates are intentionally simple for clarity
- Scripts are idempotent (DELETE before INSERT)
