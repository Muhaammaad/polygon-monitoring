# Uber Polygon Monitoring System

## Overview

The Uber Polygon Monitoring System is a comprehensive monitoring solution that tracks and validates driver activities within defined geographic zones (polygons) for multiple cities. It ensures drivers are operating in authorized areas and sends notifications when policy violations are detected.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN APPLICATION                        │
│                       (main.py)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┬──────────────────┐
     │               │               │                  │
┌────▼────┐    ┌────▼────┐    ┌────▼────┐    ┌───────▼──────┐
│ Config  │    │ Checks  │    │Database │    │Notifications │
│ Manager │    │ System  │    │ Layer   │    │   Manager    │
└─────────┘    └─────────┘    └─────────┘    └──────────────┘
     │              │              │                  │
     │         ┌────▼────┐         │                  │
     │         │ Login   │         │            ┌─────▼──────┐
     │         │ Check   │         │            │  Telegram  │
     │         └─────────┘         │            └────────────┘
     │         ┌─────────┐         │            ┌────────────┐
     │         │Delivery │         │            │    SMS     │
     │         │ Check   │         │            │ (Twilio)   │
     │         └─────────┘         │            └────────────┘
     │         ┌─────────┐         │
     │         │ Center  │         │
     │         │ Check   │         │
     │         └─────────┘         │
     │              │              │
     └──────────────┴──────────────┘
                    │
            ┌───────▼────────┐
            │ City Polygons  │
            │ (Geospatial)   │
            └────────────────┘
```

## Key Components

### 1. Configuration System (`core/config/`)
- **Purpose**: Manages multi-city configurations with zone definitions, check parameters, and notification settings
- **Files**:
  - `__init__.py`: Main configuration loader with validation using Pydantic models
- **Features**:
  - Per-city configuration (JSON/YAML)
  - Environment variable support (.env)
  - Status mapping and activity groups
  - Check-specific parameters (time windows, zones)

### 2. Polygon System (`core/polygons/`)
- **Purpose**: Manages geographic zones (polygons) for each city
- **Files**:
  - `polygon_registry.py`: Loads and validates polygon definitions from CSV files
- **Zone Types**:
  - **Login Zone**: Area where drivers can log in
  - **Delivery Zone**: Area where deliveries are allowed
  - **Waiting Zone**: Designated waiting areas for drivers
- **Format**: WKT (Well-Known Text) polygons stored in CSV files

### 3. Checks System (`core/checks/`)
Implements business logic for detecting policy violations.

#### Base Check (`base_check.py`)
Abstract base class defining the check lifecycle:
1. **query()**: Retrieve candidates from database
2. **evaluate()**: Check each candidate against rules
3. **execute()**: Orchestrate query + evaluate + insert warnings

#### Login Check (`login_check.py`)
- **Purpose**: Validates that drivers log in within authorized login zones
- **Logic**: 
  - Queries recent LOGIN_EVENT activities
  - Checks if coordinates fall within city's login polygons
  - Generates warning if outside authorized zones

#### Delivery Check (`delivery_check.py`)
- **Purpose**: Ensures deliveries occur within designated delivery zones
- **Logic**:
  - Queries recent DELIVERY_EVENT activities
  - Validates coordinates against delivery polygons
  - Triggers alert for out-of-zone deliveries

#### Center Check (`center_check.py`)
- **Purpose**: Monitors driver activity in city center/waiting zones
- **Logic**:
  - Queries WAITING_EVENT activities
  - Validates presence in designated waiting zones
  - Reports violations for unauthorized waiting areas

### 4. Database Layer (`core/db/`)
- **database.py**: Connection pool and query execution
- **repositories.py**: Data access patterns for activity logs and warnings
- **db_connections.py**: Connection management utilities

**Key Functions**:
- `get_db()`: Get/create database connection
- `execute_query()`: Execute parameterized queries
- `close_db()`: Clean connection shutdown

**Database Schema**:
```sql
-- Activity Log Table
activity_log (
    id INT PRIMARY KEY,
    uuid VARCHAR(255),
    city_code VARCHAR(50),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    status VARCHAR(50),
    ts TIMESTAMP
)

-- Warnings Table
warnings (
    id INT PRIMARY KEY,
    uuid VARCHAR(255),
    city_code VARCHAR(50),
    check_name VARCHAR(100),
    warning_note TEXT,
    created_at TIMESTAMP
)
```

### 5. Notifications System (`core/notifications/`)
Multi-channel notification delivery for policy violations.

**Supported Channels**:
- **Telegram**: Primary notification channel
- **SMS (Twilio)**: Fallback when Telegram fails

**Features**:
- Template-based messages
- Retry logic with exponential backoff
- Per-city notification preferences
- Delivery status tracking

### 6. Scheduler (`core/schedular/`)
- **executor.py**: Manages periodic check execution
- **Features**:
  - Configurable intervals (default: 3 minutes)
  - Sequential city processing
  - Error handling and recovery
  - Execution logging

### 7. Logging System (`core/logging/`)
- **json_formatter.py**: Structured JSON logging
- **setup.py**: Logger configuration
- **Features**:
  - Structured logs for analysis
  - Log level configuration
  - External library log management

## Application Flow

### 1. Startup Sequence
```
main.py
  ├─> Load environment variables (.env)
  ├─> Initialize configuration (load city configs)
  ├─> Set up logging
  ├─> Initialize polygon manager (load zone definitions)
  ├─> Start scheduler
  └─> Begin monitoring loop
```

### 2. Check Execution Cycle
```
For each configured city:
  ├─> Run Login Check
  │     ├─> Query recent login events
  │     ├─> Evaluate each against login zones
  │     ├─> Generate warnings for violations
  │     └─> Send notifications
  │
  ├─> Run Delivery Check
  │     ├─> Query recent delivery events
  │     ├─> Validate against delivery zones
  │     ├─> Create warnings
  │     └─> Notify stakeholders
  │
  └─> Run Center Check
        ├─> Query waiting events
        ├─> Check authorized waiting zones
        ├─> Record violations
        └─> Trigger alerts
```

### 3. Warning Flow
```
Violation Detected
  ├─> Create warning record in database
  ├─> Format notification message (template)
  ├─> Attempt Telegram delivery
  │     ├─> Success: Log delivery
  │     └─> Failure: Try SMS fallback
  ├─> Log notification result
  └─> Continue monitoring
```

## City Configuration

Each city has a dedicated directory under `cities/` with the following structure:

```
cities/
  └── geneva/
      ├── config.json          # City-specific configuration
      ├── config.yaml          # Alternative YAML format
      └── polygons/            # Zone definitions
          ├── login_zone/
          │   └── login_zone.csv
          ├── delivery_zone/
          │   └── delivery_zone.csv
          └── waiting_zone/
              └── waiting_zone.csv
```

### Configuration Example (config.json)

#### Understanding Status Mapping
The configuration uses a two-level status mapping system to connect database values to checks:

1. **`status.mapping`**: Maps raw database status values to canonical/simplified names
   - **Keys**: Actual status strings stored in `uber_activity_log_live.status` column
   - **Values**: Simplified canonical names used for grouping

2. **`status.groups`**: Groups canonical statuses into logical categories for checks
   - **Keys**: Group names referenced by checks (e.g., `login_candidates`, `waiting_candidates`)
   - **Values**: Lists of canonical status names from the mapping

**Example Flow:**
```
Database: "MONITORING_SUPPLY_STATUS_ONLINE"
    ↓ (via mapping)
Canonical: "online"
    ↓ (via groups)
Group: "waiting_candidates"
    ↓ (used by)
Check: center_check queries for drivers with status "MONITORING_SUPPLY_STATUS_ONLINE"
```

#### Geneva Example (French locale)
```json
{
  "city_code": "GE",
  "language": {
    "default": "FR",
    "supported": ["FR", "DE"]
  },
  "zones": ["login_zone", "waiting_zone", "delivery_zone"],
  "status": {
    "mapping": {
      "LOGIN_EVENT": "login_event",
      "ONLINE": "online",
      "DELIVERING": "delivering",
      "PAUSED": "paused",
      "OFFLINE": "offline"
    },
    "groups": {
      "login_candidates": ["login_event"],
      "waiting_candidates": ["online", "paused"],
      "delivery_candidates": ["online", "delivering"]
    },
    "unknown_policy": "log_and_skip"
  },
  "checks": {
    "login_check": {
      "enabled": true,
      "time_window_minutes": 3,
      "status_group": "login_candidates",
      "target_zone": "login_zone"
    },
    "center_check": {
      "enabled": true,
      "time_window_minutes": 10,
      "status_group": "waiting_candidates",
      "allowed_zones": ["waiting_zone"]
    },
    "delivery_check": {
      "enabled": true,
      "time_window_minutes": 6,
      "status_group": "delivery_candidates",
      "target_zone": "delivery_zone"
    }
  },
  "notifications": {
    "telegram": {"enabled": true},
    "sms_fallback": {"enabled": true}
  }
}
```

#### Berlin Example (German locale with vendor-specific statuses)
```json
{
  "city_code": "DE_BER",
  "language": {
    "default": "DE",
    "supported": ["DE"]
  },
  "zones": ["login_zone", "waiting_zone", "delivery_zone"],
  "status": {
    "mapping": {
      "LOGIN_EVENT": "login_event",
      "MONITORING_SUPPLY_STATUS_ONLINE": "online",
      "MONITORING_SUPPLY_STATUS_EN_ROUTE": "delivering",
      "MONITORING_SUPPLY_STATUS_ON_TRIP": "delivering",
      "PAUSED": "paused",
      "OFFLINE": "offline"
    },
    "groups": {
      "login_candidates": ["login_event"],
      "waiting_candidates": ["online"],
      "delivery_candidates": ["delivering"]
    },
    "unknown_policy": "log_and_skip"
  },
  "checks": {
    "login_check": {
      "enabled": true,
      "time_window_minutes": 3,
      "status_group": "login_candidates",
      "target_zone": "login_zone"
    },
    "center_check": {
      "enabled": true,
      "time_window_minutes": 10,
      "status_group": "waiting_candidates",
      "allowed_zones": ["waiting_zone"]
    },
    "delivery_check": {
      "enabled": true,
      "time_window_minutes": 6,
      "status_group": "delivery_candidates",
      "target_zone": "delivery_zone"
    }
  },
  "notifications": {
    "telegram": {"enabled": true},
    "sms_fallback": {"enabled": true}
  }
}
```

**Key Points:**
- Multiple database statuses can map to the same canonical name (e.g., both `MONITORING_SUPPLY_STATUS_EN_ROUTE` and `MONITORING_SUPPLY_STATUS_ON_TRIP` → `"delivering"`)
- Status group names must match the `status_group` field in check configurations
- Always use the **exact** database status strings as keys in the `mapping` object
- If `mapping` and `groups` don't align, checks will return 0 results and alarms won't trigger

### Polygon Definition (CSV Format)
```csv
"POLYGON((6.1200 46.1900, 6.1700 46.1900, 6.1700 46.2100, 6.1200 46.2100, 6.1200 46.1900))","Geneva Login Zone"
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL database
- Telegram Bot Token (for notifications)
- Twilio Account (for SMS fallback)

### Installation Steps

1. **Clone the repository**:
   ```bash
   cd c:\Polygon\uber_polygon_monitoring_system
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env` and update values:
   ```bash
   copy .env.example .env
   ```

   Edit `.env`:
   ```env
   # Database Configuration
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=uber_monitoring
   
   # Telegram Configuration
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_IT_CHANNEL_ID=your_channel_id
   
   # Twilio Configuration (SMS Fallback)
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_FROM_NUMBER=+41234567890
   
   # Application Settings
   LOG_LEVEL=INFO
   SCHEDULER_INTERVAL=3
   ENABLE_SMS_FALLBACK=true
   ```

5. **Initialize database**:
   ```sql
   CREATE DATABASE uber_monitoring;
   
   CREATE TABLE activity_log (
       id INT AUTO_INCREMENT PRIMARY KEY,
       uuid VARCHAR(255) NOT NULL,
       city_code VARCHAR(50) NOT NULL,
       latitude DECIMAL(10,8) NOT NULL,
       longitude DECIMAL(11,8) NOT NULL,
       status VARCHAR(50) NOT NULL,
       ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       INDEX idx_city_status_ts (city_code, status, ts),
       INDEX idx_uuid (uuid)
   );
   
   CREATE TABLE warnings (
       id INT AUTO_INCREMENT PRIMARY KEY,
       uuid VARCHAR(255) NOT NULL,
       city_code VARCHAR(50) NOT NULL,
       check_name VARCHAR(100) NOT NULL,
       warning_note TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       INDEX idx_city_check (city_code, check_name),
       INDEX idx_created_at (created_at)
   );
   ```

6. **Configure cities**:
   - Add/modify city configurations in `cities/` directory
   - Ensure polygon CSV files are present for each zone
   - Validate configurations using the config loader

## Running the Application

### Start the monitoring system:
```bash
python main.py
```

### CLI Interface (Optional):
```bash
python cli/main.py
```

### Expected Output:
```
INFO: Starting Uber Polygon Monitoring System
INFO: Loaded city: geneva with zones: login_zone, delivery_zone, waiting_zone
INFO: Loaded city: zurich with zones: login_zone, delivery_zone, waiting_zone
INFO: Scheduler started with interval: 3 minutes
INFO: Running checks for geneva...
INFO: LoginCheck: Found 5 candidates
INFO: LoginCheck: 2 warnings generated
INFO: Notifications sent via Telegram: 2
```

## Testing

The system includes comprehensive tests in the `tests/` directory:

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_login_check.py

# Run with coverage
pytest --cov=core tests/
```

## Maintenance & Operations

### Monitoring Checklist
- ✓ Database connection health
- ✓ Telegram bot connectivity
- ✓ SMS fallback availability
- ✓ Disk space for logs
- ✓ Check execution frequency
- ✓ Warning generation rates

### Log Files
- Location: Configured in `core/logging/setup.py`
- Format: JSON (structured)
- Rotation: Daily or by size

### Common Operations

**Add a new city**:
1. Create directory: `cities/new_city/`
2. Add `config.json` with city parameters
3. Create polygon CSV files in `polygons/` subdirectories
4. Restart the application

**Modify check parameters**:
1. Edit `cities/{city}/config.json`
2. Update `time_window_minutes` or zone references
3. Restart application (hot-reload not supported)

**Disable notifications for a city**:
```json
"notifications": {
  "telegram": {"enabled": false},
  "sms_fallback": {"enabled": false}
}
```

## Security Considerations

- Store `.env` file outside version control
- Use strong database credentials
- Rotate API tokens regularly
- Limit database user permissions (SELECT, INSERT only)
- Enable SSL/TLS for database connections in production
- Validate polygon data integrity

## Troubleshooting

### Database Connection Issues
```python
# Check connection
python -c "from core.db.database import get_db; print(get_db())"
```

### Polygon Loading Errors
- Verify CSV format (WKT polygons)
- Check file paths in city configuration
- Validate polygon geometry using Shapely

### Notification Failures
- Verify Telegram bot token
- Check Twilio credentials
- Review notification logs
- Test channels independently

## Performance Optimization

- **Database Indexing**: Ensure indexes on `city_code`, `status`, `ts`
- **Query Optimization**: Use time windows to limit result sets
- **Polygon Caching**: Polygons loaded once at startup
- **Connection Pooling**: Reuse database connections
- **Async Notifications**: Non-blocking notification delivery

## Dependencies

```
shapely>=2.0.0          # Geospatial operations
pymysql>=1.0.2          # Database connectivity
python-dotenv>=0.19.0   # Environment configuration
PyYAML>=6.0             # YAML parsing
pydantic>=1.8.2         # Data validation
python-telegram-bot>=13.7  # Telegram integration
twilio>=7.0.0           # SMS notifications
```

## License & Support

For technical support or questions about the system:
- Review this documentation
- Check log files for error details
- Verify configuration files
- Test database connectivity

## System Requirements

- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB RAM
- **Storage**: 1GB+ for logs and data
- **Network**: Stable internet for notifications
- **Database**: MySQL 5.7+ or MariaDB 10.3+

---

**Version**: 2.0  
**Last Updated**: January 2026  
**Status**: Production Ready
