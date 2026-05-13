# Galaxy Classification Database Setup

This document describes the database schema and setup for the Galaxy Classification System (GCS) web application.

## Recent Updates (April 2026)

### Design Fixes Applied
- ✅ **Fixed duplicate script sections** in dossier.html
- ✅ **Cleaned up app.py imports** and Flask app initialization
- ✅ **Added loading states** and error handling to dossier page
- ✅ **Improved responsive design** for mobile devices
- ✅ **Added image serving API** for stored galaxy images
- ✅ **Enhanced prediction modal** with loading spinner
- ✅ **Added refresh functionality** to dossier page

### New API Endpoints
- `GET /api/health` - System health check
- `GET /api/observation/<id>/image` - Serve stored images
- `GET /api/observations` - Get recent observations
- `GET /api/stats` - Get classification statistics
- `POST /api/feedback` - Save user corrections

## Database Schema

The application uses SQLite for persistent storage of:
- Galaxy observations and classifications
- Astronomical metadata from external catalogs
- Chat conversations with the AI assistant
- User feedback and corrections
- Model performance metrics

## Database Schema

The database consists of the following tables:

### Core Tables

1. **observations** - Stores galaxy observation data
   - observation_id (TEXT, UNIQUE) - Unique identifier like "GCS-J1951-0258"
   - ra, dec (REAL) - Right Ascension and Declination coordinates
   - survey_source (TEXT) - Data source (DESI DR10, SDSS9, etc.)
   - image_data (BLOB) - Stored galaxy image
   - fov (REAL) - Field of view
   - captured_at (TIMESTAMP) - When observation was made

2. **classifications** - AI model predictions
   - observation_id (INTEGER, FK) - Links to observations
   - model_version (TEXT) - Model file used (e.g., "best_0.8200.pth")
   - predicted_class (TEXT) - One of: "Disturbed / Merging", "Smooth", "Spiral", "Edge-on"
   - confidence (REAL) - Prediction confidence 0.0-1.0
   - is_manual_override (BOOLEAN) - Whether manually corrected
   - manual_class (TEXT) - Manual correction if applicable

3. **astronomical_metadata** - External catalog data
   - observation_id (INTEGER, FK)
   - catalog_source (TEXT) - "NOIRLab TAP", "Legacy Survey", etc.
   - object_type, flux_g, flux_r, redshift, magnitudes
   - metadata_json (TEXT) - Additional JSON data

### Chat System

4. **chat_sessions** - Chat conversation sessions
   - session_id (TEXT, UNIQUE)
   - title (TEXT) - Optional session title

5. **chat_messages** - Individual messages
   - session_id (INTEGER, FK)
   - role (TEXT) - "user" or "assistant"
   - content (TEXT) - Message content
   - timestamp (TIMESTAMP)

### Analytics & Feedback

6. **user_feedback** - User corrections and feedback
   - observation_id (INTEGER, FK)
   - original_prediction, user_correction
   - feedback_type (TEXT) - "correction", "confirmation", "uncertain"

7. **model_metrics** - Model performance tracking
   - model_version, accuracy, precision, recall, f1_score

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   The database is automatically created when you first run the application:
   ```python
   from galaxy_classification.database import GalaxyDatabase
   db = GalaxyDatabase()  # Creates galaxy_classification.db
   ```

3. **Run the Application**
   ```bash
   cd web
   python app.py
   ```

## API Endpoints

### Observations
- `GET /api/observations` - Get recent observations
- `GET /api/observation/<id>` - Get specific observation details

### Chat
- `GET /api/chat/history/<session_id>` - Get chat history

### Analytics
- `GET /api/stats` - Get classification statistics
- `POST /api/feedback` - Save user feedback/corrections

## Data Flow

1. **Observation Capture**
   - User captures galaxy image in survey interface
   - Image + coordinates sent to `/predict` endpoint
   - Database stores observation and classification

2. **AI Chat**
   - Messages sent to `/chat` endpoint
   - Both user and AI messages stored in database

3. **User Corrections**
   - Manual overrides saved via `/api/feedback`
   - Links corrections to original observations

4. **Dossier Display**
   - Frontend loads observations via `/api/observations`
   - Displays stored classifications and metadata

## Database Maintenance

### Backup
```bash
cp galaxy_classification.db galaxy_classification_backup.db
```

### Reset Database
```python
import os
os.remove('galaxy_classification.db')
# Restart application to recreate
```

### Query Examples

Get recent classifications:
```sql
SELECT o.observation_id, o.ra, o.dec, c.predicted_class, c.confidence
FROM observations o
JOIN classifications c ON o.id = c.observation_id
ORDER BY c.classified_at DESC
LIMIT 10;
```

Get classification accuracy:
```sql
SELECT predicted_class, COUNT(*), AVG(confidence)
FROM classifications
GROUP BY predicted_class;
```

## Testing

Run the test script to verify API functionality:

```bash
python test_api.py
```

This will test:
- Database connectivity
- API endpoints
- Data retrieval
- Error handling

## Troubleshooting

### Database Issues
```bash
# Reset database
rm galaxy_classification.db
python -c "from galaxy_classification.database import GalaxyDatabase; GalaxyDatabase()"
```

### API Issues
- Ensure Flask app is running: `cd webapp && python app.py`
- Check for import errors in console
- Verify database file exists and is writable

### Frontend Issues
- Clear browser cache
- Check browser console for JavaScript errors
- Ensure all API endpoints return valid JSON