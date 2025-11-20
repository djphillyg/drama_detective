# MongoDB Migration & Multi-User Design

## Overview

Migrate from file-based session storage to MongoDB with multi-user support, designed for local development (Docker Compose) and Railway production deployment.

## Deployment Path

```
Local Development
├── Docker Compose MongoDB (localhost:27017)
├── Backend runs locally (connects to Docker MongoDB)
└── Frontend runs locally (connects to local backend)

↓ Deploy to Railway

Production (Railway)
├── Railway MongoDB Plugin (managed service)
├── Backend service (connects to Railway MongoDB via internal URL)
└── Frontend service (connects to backend via Railway URL)
```

---

## Multi-User Architecture

### User Context Flow

```
Frontend: User logs in
    ↓
Backend: Verify password → Generate JWT with user_id
    ↓
Frontend: Store JWT, send in Authorization header
    ↓
Backend: Decode JWT → Extract user_id
    ↓
SessionManager: Filter sessions by user_id
    ↓
MongoDB: Query { user_id: "user-123" }
```

### Session Model Extensions

```python
# backend/src/models.py

class Session(BaseModel):
    # Existing fields
    session_id: str
    incident_name: str
    created_at: str
    status: SessionStatus
    # ... all existing fields ...

    # NEW: Multi-user support
    user_id: str = ""  # Empty string for backward compatibility
    user_email: Optional[str] = None  # Optional: track user email

    # NEW: Voice mode support (from voice-mode-design.md)
    mode: Literal["text", "voice"] = "text"
    hume_conversation_id: Optional[str] = None
    voice_call_started_at: Optional[str] = None
    voice_call_ended_at: Optional[str] = None
    voice_call_duration_seconds: Optional[int] = None

    # NEW: Metadata
    updated_at: Optional[str] = None  # Track last update for optimistic locking
```

### MongoDB Schema

```javascript
// Collection: sessions
{
  _id: ObjectId("..."),                    // MongoDB internal ID
  session_id: "uuid-v4",                   // Our unique ID (indexed)
  user_id: "user-123",                     // CRITICAL: For multi-user filtering (indexed)
  user_email: "user@example.com",          // Optional: for display/debugging

  // Incident details
  incident_name: "bathroom-drama",
  interviewee_name: "Alex",
  interviewee_role: "participant",
  confidence_threshold: 90,

  // Session state
  status: "active" | "processing" | "complete" | "failed",
  mode: "text" | "voice",

  // Voice-specific fields (null for text mode)
  hume_conversation_id: "hume-conv-456",
  voice_call_started_at: ISODate("2025-11-18T10:00:00Z"),
  voice_call_ended_at: ISODate("2025-11-18T10:12:34Z"),
  voice_call_duration_seconds: 754,

  // Interview data
  summary: "Long text...",
  extracted_summary: {
    actors: [...],
    point_of_conflict: {...},
    general_details: {...},
    missing_info: [...]
  },
  goals: [
    {
      description: "Understand timeline",
      status: "in_progress",
      confidence: 65
    }
  ],
  facts: [
    {
      topic: "Timeline",
      claim: "Incident happened last Tuesday",
      timestamp: "last Tuesday",
      confidence: "certain"
    }
  ],
  messages: [
    {
      role: "assistant",
      content: "Tell me what happened",
      timestamp: "2025-11-18T10:00:00Z"
    }
  ],
  answers: [...],
  current_question: "...",
  turn_count: 12,

  // Timestamps
  created_at: ISODate("2025-11-18T10:00:00Z"),
  updated_at: ISODate("2025-11-18T10:12:45Z")
}
```

### Indexes (Critical for Performance)

```javascript
// backend/scripts/mongo-init.js

db.sessions.createIndex({ "session_id": 1 }, { unique: true });
db.sessions.createIndex({ "user_id": 1, "created_at": -1 });  // List user's sessions
db.sessions.createIndex({ "status": 1 });                     // Filter by status
db.sessions.createIndex({ "mode": 1 });                       // Filter by mode
db.sessions.createIndex({ "hume_conversation_id": 1 }, { sparse: true });  // Voice lookups

// Compound index for common queries
db.sessions.createIndex({
  "user_id": 1,
  "status": 1,
  "created_at": -1
});
```

---

## Docker Compose Setup

### Local Development Configuration

```yaml
# docker-compose.yml

version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: drama-detective-mongo
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: drama_admin
      MONGO_INITDB_ROOT_PASSWORD: dev_password_change_me
      MONGO_INITDB_DATABASE: drama_detective
    volumes:
      # Persist data between restarts
      - mongo_data:/data/db
      # Initialize database with indexes
      - ./backend/scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/drama_detective --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  mongo-express:
    image: mongo-express:1.0-20
    container_name: drama-detective-mongo-ui
    restart: unless-stopped
    ports:
      - "8081:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: drama_admin
      ME_CONFIG_MONGODB_ADMINPASSWORD: dev_password_change_me
      ME_CONFIG_MONGODB_URL: mongodb://drama_admin:dev_password_change_me@mongodb:27017/
      ME_CONFIG_BASICAUTH_USERNAME: admin
      ME_CONFIG_BASICAUTH_PASSWORD: admin
    depends_on:
      mongodb:
        condition: service_healthy

volumes:
  mongo_data:
    driver: local
```

### MongoDB Initialization Script

```javascript
// backend/scripts/mongo-init.js

// This script runs when MongoDB container first starts

// Switch to drama_detective database
db = db.getSiblingDB('drama_detective');

// Create sessions collection with validation
db.createCollection("sessions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["session_id", "user_id", "created_at", "status"],
      properties: {
        session_id: {
          bsonType: "string",
          description: "Unique session identifier - required"
        },
        user_id: {
          bsonType: "string",
          description: "User who owns this session - required"
        },
        status: {
          enum: ["active", "processing", "complete", "failed", "paused"],
          description: "Session status - required"
        },
        mode: {
          enum: ["text", "voice"],
          description: "Interview mode"
        }
      }
    }
  }
});

// Create indexes
db.sessions.createIndex({ "session_id": 1 }, { unique: true });
db.sessions.createIndex({ "user_id": 1, "created_at": -1 });
db.sessions.createIndex({ "status": 1 });
db.sessions.createIndex({ "mode": 1 });
db.sessions.createIndex({ "hume_conversation_id": 1 }, { sparse: true });
db.sessions.createIndex({ "user_id": 1, "status": 1, "created_at": -1 });

print("✅ Drama Detective database initialized with indexes");
```

---

## Railway Deployment Configuration

### Railway MongoDB Plugin Setup

1. **Add MongoDB Plugin**:
   - Railway Dashboard → Project → New → Database → MongoDB
   - Railway auto-generates: `MONGO_URL` environment variable

2. **Environment Variables** (Railway Backend Service):
   ```
   SESSION_STORAGE=mongo
   MONGODB_URI=${MONGO_URL}  # Railway injects this automatically
   MONGODB_DATABASE=drama_detective
   ```

3. **Initial Deployment Script**:
   ```bash
   # Railway will run this on first deploy
   # backend/scripts/railway_setup.sh

   #!/bin/bash

   echo "🚂 Setting up Railway MongoDB..."

   # Run schema migrations
   python scripts/run_migrations.py up

   # Optional: Seed demo data (only on first deploy)
   if [ "$SEED_DEMO_DATA" = "true" ]; then
     python scripts/seed_database.py --scenario demo
   fi

   echo "✅ Railway setup complete"
   ```

4. **Railway Configuration**:
   ```toml
   # railway.toml (in backend/)

   [build]
   builder = "NIXPACKS"

   [deploy]
   startCommand = "bash scripts/railway_setup.sh && uvicorn src.api.app:app --host 0.0.0.0 --port $PORT"
   healthcheckPath = "/health"
   healthcheckTimeout = 100
   restartPolicyType = "ON_FAILURE"
   ```

### Local ↔ Railway Connection String Handling

```python
# backend/src/config.py

import os
from typing import Literal

def get_mongodb_uri() -> str:
    """
    Get MongoDB connection URI based on environment.

    Local dev: mongodb://drama_admin:dev_password@localhost:27017/drama_detective
    Railway: Uses MONGO_URL provided by Railway plugin
    """
    # Railway provides MONGO_URL automatically
    railway_mongo = os.getenv("MONGO_URL")
    if railway_mongo:
        return railway_mongo

    # Local development
    local_mongo = os.getenv("MONGODB_URI")
    if local_mongo:
        return local_mongo

    # Default to local Docker Compose
    return "mongodb://drama_admin:dev_password_change_me@localhost:27017/drama_detective"

def get_storage_type() -> Literal["file", "mongo"]:
    """
    Determine storage backend.

    Railway: Always use mongo
    Local: Environment variable (defaults to file for backward compatibility)
    """
    # Force mongo on Railway
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return "mongo"

    return os.getenv("SESSION_STORAGE", "file")  # type: ignore
```

---

## Storage Layer Implementation

### Abstract Interface

```python
# backend/src/storage/base.py

from abc import ABC, abstractmethod
from typing import Optional
from ..models import Session

class SessionStorage(ABC):
    """Abstract interface for session storage backends."""

    @abstractmethod
    def create(self, **kwargs) -> Session:
        """Create a new session."""
        pass

    @abstractmethod
    def save(self, session: Session) -> None:
        """Save/update a session."""
        pass

    @abstractmethod
    def load(self, session_id: str, user_id: Optional[str] = None) -> Session:
        """Load a session by ID. Filter by user_id if provided."""
        pass

    @abstractmethod
    def list_all(self, user_id: Optional[str] = None, status: Optional[str] = None) -> list[Session]:
        """List sessions. Filter by user_id and/or status if provided."""
        pass

    @abstractmethod
    def delete(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a session. Returns True if deleted."""
        pass

    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        pass
```

### MongoDB Implementation

```python
# backend/src/storage/mongo_storage.py

from datetime import datetime
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import uuid

from .base import SessionStorage
from ..models import Session, SessionStatus

class MongoSessionStorage(SessionStorage):
    """MongoDB-backed session storage with multi-user support."""

    def __init__(self, mongo_uri: str, database_name: str = "drama_detective"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]
        self.sessions = self.db.sessions

    def create(
        self,
        incident_name: str,
        interviewee_name: str,
        interviewee_role: str,
        user_id: str,  # REQUIRED for multi-user
        confidence_threshold: int = 90,
        mode: str = "text",
        user_email: Optional[str] = None
    ) -> Session:
        """Create new session with user context."""
        session = Session(
            session_id=str(uuid.uuid4()),
            incident_name=incident_name,
            interviewee_name=interviewee_name,
            interviewee_role=interviewee_role,
            user_id=user_id,
            user_email=user_email,
            confidence_threshold=confidence_threshold,
            mode=mode,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            status=SessionStatus.ACTIVE
        )
        return session

    def save(self, session: Session) -> None:
        """Save or update session."""
        session.updated_at = datetime.utcnow().isoformat()

        # Upsert: insert if new, update if exists
        self.sessions.update_one(
            {"session_id": session.session_id},
            {"$set": session.model_dump()},
            upsert=True
        )

    def load(self, session_id: str, user_id: Optional[str] = None) -> Session:
        """
        Load session by ID.
        If user_id provided, verify session belongs to that user.
        """
        query = {"session_id": session_id}

        # Multi-user security: only load if session belongs to user
        if user_id:
            query["user_id"] = user_id

        doc = self.sessions.find_one(query)

        if not doc:
            if user_id:
                raise PermissionError(f"Session {session_id} not found or access denied")
            else:
                raise FileNotFoundError(f"Session {session_id} not found")

        # Remove MongoDB's _id before converting to Session
        doc.pop("_id", None)
        return Session(**doc)

    def list_all(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        mode: Optional[str] = None
    ) -> list[Session]:
        """
        List sessions with optional filters.

        Args:
            user_id: Filter by user (CRITICAL for multi-user)
            status: Filter by status (active, complete, etc.)
            mode: Filter by mode (text, voice)
        """
        query = {}

        if user_id:
            query["user_id"] = user_id
        if status:
            query["status"] = status
        if mode:
            query["mode"] = mode

        # Sort by created_at descending (newest first)
        cursor = self.sessions.find(query).sort("created_at", -1)

        sessions = []
        for doc in cursor:
            doc.pop("_id", None)
            sessions.append(Session(**doc))

        return sessions

    def delete(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a session.
        If user_id provided, only delete if session belongs to that user.
        """
        query = {"session_id": session_id}

        if user_id:
            query["user_id"] = user_id

        result = self.sessions.delete_one(query)
        return result.deleted_count > 0

    def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return self.sessions.count_documents({"session_id": session_id}) > 0

    # VOICE MODE: Incremental update methods for webhook efficiency

    def append_message(self, session_id: str, message: dict) -> None:
        """Append message without loading entire session (webhook optimization)."""
        self.sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.utcnow().isoformat()}
            }
        )

    def update_voice_metadata(
        self,
        session_id: str,
        hume_conversation_id: Optional[str] = None,
        voice_call_started_at: Optional[str] = None,
        voice_call_ended_at: Optional[str] = None,
        voice_call_duration_seconds: Optional[int] = None
    ) -> None:
        """Update voice-specific metadata (webhook optimization)."""
        update_fields = {"updated_at": datetime.utcnow().isoformat()}

        if hume_conversation_id:
            update_fields["hume_conversation_id"] = hume_conversation_id
        if voice_call_started_at:
            update_fields["voice_call_started_at"] = voice_call_started_at
        if voice_call_ended_at:
            update_fields["voice_call_ended_at"] = voice_call_ended_at
        if voice_call_duration_seconds is not None:
            update_fields["voice_call_duration_seconds"] = voice_call_duration_seconds

        self.sessions.update_one(
            {"session_id": session_id},
            {"$set": update_fields}
        )
```

### File Storage (Existing - Unchanged)

```python
# backend/src/storage/file_storage.py

# Move existing SessionManager logic here
# Keep exactly as-is for backward compatibility
# This ensures file-based sessions still work locally
```

### SessionManager Facade

```python
# backend/src/session.py (refactored)

from typing import Optional
from .storage.base import SessionStorage
from .storage.file_storage import FileSessionStorage
from .storage.mongo_storage import MongoSessionStorage
from .config import get_storage_type, get_mongodb_uri
from .models import Session

class SessionManager:
    """
    Facade for session storage.
    Automatically selects file or MongoDB backend based on environment.

    Usage remains identical:
        sm = SessionManager()
        session = sm.create_session(...)
        sm.save_session(session)
    """

    def __init__(self, storage: Optional[SessionStorage] = None, user_id: Optional[str] = None):
        """
        Initialize SessionManager with auto-detected or explicit storage.

        Args:
            storage: Optional explicit storage backend
            user_id: Current user context for multi-user filtering
        """
        if storage:
            self.storage = storage
        else:
            # Auto-detect based on environment
            storage_type = get_storage_type()

            if storage_type == "mongo":
                mongo_uri = get_mongodb_uri()
                self.storage = MongoSessionStorage(mongo_uri)
            else:
                self.storage = FileSessionStorage()

        self.user_id = user_id  # Store user context

    def create_session(
        self,
        incident_name: str,
        interviewee_name: str,
        interviewee_role: str,
        confidence_threshold: int = 90,
        mode: str = "text",
        user_email: Optional[str] = None
    ) -> Session:
        """Create new session (auto-injects user_id if available)."""
        return self.storage.create(
            incident_name=incident_name,
            interviewee_name=interviewee_name,
            interviewee_role=interviewee_role,
            user_id=self.user_id or "",  # Empty string for CLI usage
            confidence_threshold=confidence_threshold,
            mode=mode,
            user_email=user_email
        )

    def save_session(self, session: Session) -> None:
        """Save session."""
        self.storage.save(session)

    def load_session(self, session_id: str) -> Session:
        """Load session (auto-filters by user_id if available)."""
        return self.storage.load(session_id, user_id=self.user_id)

    def list_sessions(self, status: Optional[str] = None, mode: Optional[str] = None) -> list[Session]:
        """List sessions (auto-filters by user_id if available)."""
        return self.storage.list_all(user_id=self.user_id, status=status, mode=mode)

    def delete_session(self, session_id: str) -> bool:
        """Delete session (auto-filters by user_id if available)."""
        return self.storage.delete(session_id, user_id=self.user_id)

    # Voice mode helpers
    def append_message(self, session_id: str, message: dict) -> None:
        """Append message (webhook optimization)."""
        if hasattr(self.storage, 'append_message'):
            self.storage.append_message(session_id, message)
        else:
            # Fallback: load, modify, save
            session = self.load_session(session_id)
            session.messages.append(message)
            self.save_session(session)
```

---

## Migration Scripts

### File to MongoDB Migration

```python
# backend/scripts/migrate_file_to_mongo.py

"""
One-time migration from file-based sessions to MongoDB.
Idempotent: can be run multiple times safely.
"""

import json
import os
from pathlib import Path
from pymongo import MongoClient
from src.models import Session
from src.config import get_mongodb_uri

def migrate(data_dir: Path = None, user_id: str = "migrated-user"):
    """
    Migrate all file-based sessions to MongoDB.

    Args:
        data_dir: Path to .drama/.sessions directory
        user_id: User ID to assign to migrated sessions (default: "migrated-user")
    """
    # Find sessions directory
    if data_dir is None:
        env_data_dir = os.getenv("DATA_DIR")
        if env_data_dir:
            data_dir = Path(env_data_dir) / ".sessions"
        else:
            project_root = Path(__file__).parent.parent.parent
            if project_root == Path("/"):
                data_dir = Path("/tmp/.drama/.sessions")
            else:
                data_dir = project_root / ".drama" / ".sessions"

    if not data_dir.exists():
        print(f"❌ Session directory not found: {data_dir}")
        return

    # Connect to MongoDB
    mongo_uri = get_mongodb_uri()
    client = MongoClient(mongo_uri)
    db = client.drama_detective
    sessions_collection = db.sessions

    # Find all JSON files
    json_files = list(data_dir.glob("*.json"))
    print(f"📁 Found {len(json_files)} session files")

    migrated = 0
    skipped = 0
    errors = 0

    for json_file in json_files:
        try:
            # Load session data
            with open(json_file) as f:
                data = json.load(f)

            session_id = data.get("session_id")

            # Check if already migrated
            if sessions_collection.count_documents({"session_id": session_id}) > 0:
                print(f"⏭️  Skipping {session_id} - already in MongoDB")
                skipped += 1
                continue

            # Add user_id if missing (for old sessions)
            if "user_id" not in data or not data["user_id"]:
                data["user_id"] = user_id

            # Add mode if missing (default to text)
            if "mode" not in data:
                data["mode"] = "text"

            # Add updated_at if missing
            if "updated_at" not in data:
                data["updated_at"] = data.get("created_at")

            # Validate session
            session = Session(**data)

            # Insert into MongoDB
            sessions_collection.insert_one(session.model_dump())
            print(f"✅ Migrated {session_id}")
            migrated += 1

        except Exception as e:
            print(f"❌ Error migrating {json_file.name}: {e}")
            errors += 1

    print(f"\n📊 Migration Summary:")
    print(f"   Migrated: {migrated}")
    print(f"   Skipped: {skipped}")
    print(f"   Errors: {errors}")
    print(f"   Total: {len(json_files)}")

    # Optionally backup and delete JSON files
    if migrated > 0:
        response = input("\n🗑️  Delete migrated JSON files? (y/N): ")
        if response.lower() == "y":
            for json_file in json_files:
                with open(json_file) as f:
                    data = json.load(f)
                if sessions_collection.count_documents({"session_id": data["session_id"]}) > 0:
                    json_file.unlink()
                    print(f"🗑️  Deleted {json_file.name}")

if __name__ == "__main__":
    import sys

    user_id = "migrated-user"
    if len(sys.argv) > 1:
        user_id = sys.argv[1]

    print(f"🚀 Starting migration (assigning user_id: {user_id})...")
    migrate(user_id=user_id)
```

### Schema Migrations

```python
# backend/scripts/run_migrations.py

"""
Schema migration runner for MongoDB.
Tracks which migrations have been applied.
"""

import importlib
from pathlib import Path
from pymongo import MongoClient
from src.config import get_mongodb_uri

def get_applied_migrations(db) -> set:
    """Get list of already-applied migrations."""
    migrations_collection = db.migrations
    applied = migrations_collection.find({}, {"migration_id": 1})
    return {m["migration_id"] for m in applied}

def mark_migration_applied(db, migration_id: str):
    """Mark a migration as applied."""
    db.migrations.insert_one({
        "migration_id": migration_id,
        "applied_at": datetime.utcnow().isoformat()
    })

def run_migrations(direction="up"):
    """
    Run pending migrations.

    Args:
        direction: "up" to apply migrations, "down" to rollback
    """
    mongo_uri = get_mongodb_uri()
    client = MongoClient(mongo_uri)
    db = client.drama_detective

    # Find all migration files
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.py"))

    applied = get_applied_migrations(db)

    for migration_file in migration_files:
        migration_id = migration_file.stem  # e.g., "001_initial_schema"

        if direction == "up":
            if migration_id in applied:
                print(f"⏭️  Skipping {migration_id} - already applied")
                continue

            # Import and run migration
            module = importlib.import_module(f"migrations.{migration_id}")
            print(f"🚀 Applying {migration_id}...")
            module.up(db)
            mark_migration_applied(db, migration_id)
            print(f"✅ Applied {migration_id}")

        elif direction == "down":
            if migration_id not in applied:
                continue

            # Import and rollback
            module = importlib.import_module(f"migrations.{migration_id}")
            print(f"⏮️  Rolling back {migration_id}...")
            module.down(db)
            db.migrations.delete_one({"migration_id": migration_id})
            print(f"✅ Rolled back {migration_id}")

if __name__ == "__main__":
    import sys
    from datetime import datetime

    direction = sys.argv[1] if len(sys.argv) > 1 else "up"
    run_migrations(direction)
```

### Example Migration

```python
# backend/migrations/001_initial_schema.py

"""
Initial MongoDB schema setup: indexes and validation.
"""

def up(db):
    """Apply migration: create indexes."""
    sessions = db.sessions

    # Create indexes
    sessions.create_index("session_id", unique=True)
    sessions.create_index([("user_id", 1), ("created_at", -1)])
    sessions.create_index("status")
    sessions.create_index("mode")
    sessions.create_index("hume_conversation_id", sparse=True)

    print("   ✅ Created indexes")

def down(db):
    """Rollback migration: drop indexes."""
    sessions = db.sessions

    sessions.drop_index("session_id_1")
    sessions.drop_index("user_id_1_created_at_-1")
    sessions.drop_index("status_1")
    sessions.drop_index("mode_1")
    sessions.drop_index("hume_conversation_id_1")

    print("   ✅ Dropped indexes")
```

---

## Seeding Scripts

```python
# backend/scripts/seed_database.py

"""
Seed database with test data for different scenarios.
"""

import argparse
from datetime import datetime, timedelta
from pymongo import MongoClient
from src.config import get_mongodb_uri
from src.models import Session, SessionStatus

SCENARIOS = {
    "demo": [
        # Complete investigation - good for demos
        {
            "session_id": "demo-complete-001",
            "user_id": "demo-user",
            "incident_name": "The Bathroom Conspiracy",
            "interviewee_name": "Alex",
            "interviewee_role": "participant",
            "status": "complete",
            "mode": "text",
            "goals": [
                {"description": "Understand timeline", "status": "complete", "confidence": 90},
                {"description": "Identify all actors", "status": "complete", "confidence": 95}
            ],
            "facts": [
                {"topic": "Timeline", "claim": "Incident occurred last Tuesday", "timestamp": "last Tuesday", "confidence": "certain"},
                {"topic": "Actors", "claim": "Sarah and Jamie were involved", "timestamp": "", "confidence": "certain"}
            ],
            "turn_count": 12,
            "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "updated_at": (datetime.utcnow() - timedelta(days=2)).isoformat()
        }
    ],
    "test": [
        # Minimal sessions for automated tests
        {
            "session_id": "test-session-001",
            "user_id": "test-user",
            "incident_name": "test-incident",
            "status": "active",
            "mode": "text",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ],
    "dev": [
        # Variety of sessions for development
        # Active text session
        {
            "session_id": "dev-active-text",
            "user_id": "dev-user",
            "incident_name": "Active Text Investigation",
            "status": "active",
            "mode": "text",
            "turn_count": 5,
            "created_at": datetime.utcnow().isoformat()
        },
        # Complete voice session
        {
            "session_id": "dev-complete-voice",
            "user_id": "dev-user",
            "incident_name": "Voice Interview Complete",
            "status": "complete",
            "mode": "voice",
            "voice_call_duration_seconds": 654,
            "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
        }
    ]
}

def seed(scenario="dev", clean=False):
    """Seed database with test data."""
    mongo_uri = get_mongodb_uri()
    client = MongoClient(mongo_uri)
    db = client.drama_detective

    if clean:
        print("🗑️  Cleaning existing sessions...")
        db.sessions.delete_many({})

    sessions_data = SCENARIOS.get(scenario, SCENARIOS["dev"])

    for session_data in sessions_data:
        # Fill in defaults
        session_data.setdefault("interviewee_name", "")
        session_data.setdefault("interviewee_role", "participant")
        session_data.setdefault("confidence_threshold", 90)
        session_data.setdefault("summary", "")
        session_data.setdefault("goals", [])
        session_data.setdefault("facts", [])
        session_data.setdefault("messages", [])
        session_data.setdefault("answers", [])
        session_data.setdefault("current_question", "")
        session_data.setdefault("turn_count", 0)
        session_data.setdefault("updated_at", session_data["created_at"])

        # Validate with Pydantic
        session = Session(**session_data)

        # Insert
        db.sessions.update_one(
            {"session_id": session.session_id},
            {"$set": session.model_dump()},
            upsert=True
        )
        print(f"✅ Seeded {session.session_id}")

    print(f"\n📊 Seeded {len(sessions_data)} sessions (scenario: {scenario})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["demo", "test", "dev"], default="dev")
    parser.add_argument("--clean", action="store_true", help="Clean existing sessions first")
    args = parser.parse_args()

    seed(scenario=args.scenario, clean=args.clean)
```

---

## Testing Strategy

### Test Configuration

```python
# tests/conftest.py

import pytest
import mongomock
from testcontainers.mongodb import MongoDbContainer
from src.storage.mongo_storage import MongoSessionStorage
from src.storage.file_storage import FileSessionStorage

def pytest_addoption(parser):
    parser.addoption(
        "--use-real-mongo",
        action="store_true",
        help="Run tests against real MongoDB (slower, more accurate)"
    )

@pytest.fixture(scope="session")
def mongo_container(request):
    """Start MongoDB container for integration tests."""
    if request.config.getoption("--use-real-mongo"):
        with MongoDbContainer("mongo:7.0") as mongo:
            yield mongo
    else:
        yield None

@pytest.fixture
def mongo_storage(request, mongo_container):
    """Provide MongoDB storage for tests."""
    if request.config.getoption("--use-real-mongo"):
        # Real MongoDB
        mongo_uri = mongo_container.get_connection_url()
        storage = MongoSessionStorage(mongo_uri, database_name="test_drama")
        yield storage
        # Cleanup
        storage.db.sessions.delete_many({})
    else:
        # Mongomock (in-memory)
        client = mongomock.MongoClient()
        db = client.test_drama
        storage = MongoSessionStorage.__new__(MongoSessionStorage)
        storage.client = client
        storage.db = db
        storage.sessions = db.sessions
        yield storage

@pytest.fixture
def file_storage(tmp_path):
    """Provide file-based storage for tests."""
    storage = FileSessionStorage(data_dir=tmp_path)
    yield storage
```

### Test Files

```python
# tests/test_session_mongo.py

import pytest
from src.models import Session, SessionStatus

def test_create_session(mongo_storage):
    """Test creating a session."""
    session = mongo_storage.create(
        incident_name="test-incident",
        interviewee_name="Test User",
        interviewee_role="participant",
        user_id="test-user-123"
    )

    assert session.session_id is not None
    assert session.user_id == "test-user-123"
    assert session.incident_name == "test-incident"
    assert session.status == SessionStatus.ACTIVE

def test_save_and_load(mongo_storage):
    """Test saving and loading a session."""
    session = mongo_storage.create(
        incident_name="save-load-test",
        interviewee_name="Test",
        interviewee_role="participant",
        user_id="user-1"
    )

    # Save
    mongo_storage.save(session)

    # Load
    loaded = mongo_storage.load(session.session_id)

    assert loaded.session_id == session.session_id
    assert loaded.user_id == "user-1"

def test_multi_user_isolation(mongo_storage):
    """Test that users can only access their own sessions."""
    # User 1 creates session
    session_user1 = mongo_storage.create(
        incident_name="user1-session",
        interviewee_name="User1",
        interviewee_role="participant",
        user_id="user-1"
    )
    mongo_storage.save(session_user1)

    # User 2 creates session
    session_user2 = mongo_storage.create(
        incident_name="user2-session",
        interviewee_name="User2",
        interviewee_role="participant",
        user_id="user-2"
    )
    mongo_storage.save(session_user2)

    # User 1 can load their session
    loaded = mongo_storage.load(session_user1.session_id, user_id="user-1")
    assert loaded.session_id == session_user1.session_id

    # User 1 CANNOT load user 2's session
    with pytest.raises(PermissionError):
        mongo_storage.load(session_user2.session_id, user_id="user-1")

    # List sessions filters by user
    user1_sessions = mongo_storage.list_all(user_id="user-1")
    assert len(user1_sessions) == 1
    assert user1_sessions[0].user_id == "user-1"

def test_voice_mode_incremental_updates(mongo_storage):
    """Test incremental updates for voice mode."""
    session = mongo_storage.create(
        incident_name="voice-test",
        interviewee_name="Test",
        interviewee_role="participant",
        user_id="user-1",
        mode="voice"
    )
    mongo_storage.save(session)

    # Append message without loading entire session
    mongo_storage.append_message(
        session.session_id,
        {
            "role": "user",
            "content": "Test message",
            "timestamp": "2025-11-18T10:00:00Z"
        }
    )

    # Load and verify
    loaded = mongo_storage.load(session.session_id)
    assert len(loaded.messages) == 1
    assert loaded.messages[0]["content"] == "Test message"
```

---

## Makefile for Developer Experience

```makefile
# Makefile

.PHONY: help setup mongo-up mongo-down mongo-shell migrate seed test test-mongo reset-db

help:
	@echo "Drama Detective - Development Commands"
	@echo ""
	@echo "  make setup          Install Python dependencies"
	@echo "  make mongo-up       Start MongoDB (Docker Compose)"
	@echo "  make mongo-down     Stop MongoDB"
	@echo "  make mongo-shell    Open MongoDB shell"
	@echo "  make migrate        Run database migrations"
	@echo "  make seed           Seed test data (dev scenario)"
	@echo "  make seed-demo      Seed demo data"
	@echo "  make test           Run tests (mongomock)"
	@echo "  make test-mongo     Run tests (real MongoDB)"
	@echo "  make reset-db       ⚠️  Delete all sessions"

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r backend/requirements.txt

mongo-up:
	docker-compose up -d mongodb mongo-express
	@echo ""
	@echo "✅ MongoDB running at localhost:27017"
	@echo "✅ Mongo Express UI at http://localhost:8081"
	@echo "   Username: admin | Password: admin"

mongo-down:
	docker-compose down

mongo-shell:
	docker exec -it drama-detective-mongo mongosh drama_detective \
		-u drama_admin -p dev_password_change_me

migrate:
	@echo "🚀 Running database migrations..."
	cd backend && python scripts/run_migrations.py up

seed:
	@echo "🌱 Seeding development data..."
	cd backend && python scripts/seed_database.py --scenario dev

seed-demo:
	@echo "🌱 Seeding demo data..."
	cd backend && python scripts/seed_database.py --scenario demo --clean

test:
	@echo "🧪 Running tests (mongomock)..."
	cd backend && pytest tests/

test-mongo:
	@echo "🧪 Running tests (real MongoDB)..."
	cd backend && pytest tests/ --use-real-mongo

reset-db:
	@echo "⚠️  WARNING: This will delete ALL sessions!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	cd backend && python scripts/reset_database.py --confirm
```

---

## Environment Variables Reference

### Local Development (.env)

```bash
# .env (backend/)

# Storage backend
SESSION_STORAGE=mongo  # or "file" for old behavior

# MongoDB connection (Docker Compose)
MONGODB_URI=mongodb://drama_admin:dev_password_change_me@localhost:27017/drama_detective
MONGODB_DATABASE=drama_detective

# API
JWT_SECRET=your-secret-key-change-this
ACCESS_PASSWORD=your-password-here

# Hume (voice mode)
HUME_API_KEY=your-hume-api-key
HUME_CONFIG_ID=drama-detective-interviewer
```

### Railway Production

```bash
# Railway environment variables (set in dashboard)

SESSION_STORAGE=mongo
# MONGODB_URI is auto-set by Railway MongoDB plugin as MONGO_URL
MONGODB_DATABASE=drama_detective

JWT_SECRET=<generate-strong-secret>
ACCESS_PASSWORD=<production-password>

# Hume
HUME_API_KEY=<production-hume-key>
HUME_CONFIG_ID=drama-detective-interviewer

# Railway detection
RAILWAY_ENVIRONMENT=production
```

---

## Implementation Checklist

### Phase 1: Local MongoDB Setup
- [ ] Create `docker-compose.yml`
- [ ] Create `mongo-init.js` initialization script
- [ ] Create `.env` file with MongoDB connection string
- [ ] Test: `make mongo-up` starts MongoDB successfully

### Phase 2: Storage Layer
- [ ] Create `backend/src/storage/base.py` (abstract interface)
- [ ] Create `backend/src/storage/mongo_storage.py` (MongoDB implementation)
- [ ] Move existing logic to `backend/src/storage/file_storage.py`
- [ ] Update `backend/src/session.py` (SessionManager facade)
- [ ] Create `backend/src/config.py` (environment detection)
- [ ] Test: SessionManager works with both file and mongo

### Phase 3: Multi-User Support
- [ ] Add `user_id` field to Session model
- [ ] Update SessionManager to accept user context
- [ ] Update API routes to extract user_id from JWT
- [ ] Test: Multi-user isolation works

### Phase 4: Migration & Seeding
- [ ] Create `scripts/migrate_file_to_mongo.py`
- [ ] Create `scripts/seed_database.py` with scenarios
- [ ] Create `scripts/run_migrations.py`
- [ ] Create `migrations/001_initial_schema.py`
- [ ] Test: Migration script works on sample data

### Phase 5: Testing
- [ ] Create `tests/conftest.py` with MongoDB fixtures
- [ ] Create `tests/test_session_mongo.py`
- [ ] Create `tests/test_migration.py`
- [ ] Create `tests/test_multi_user.py`
- [ ] Test: All tests pass with both mongomock and real MongoDB

### Phase 6: Developer Tooling
- [ ] Create Makefile with common commands
- [ ] Update README with MongoDB setup instructions
- [ ] Test: New developer can run `make setup && make mongo-up && make migrate`

### Phase 7: Railway Deployment
- [ ] Add MongoDB plugin to Railway project
- [ ] Configure environment variables
- [ ] Create `railway.toml` config
- [ ] Deploy backend to Railway
- [ ] Test: Sessions persist in Railway MongoDB

---

## Success Criteria

- [ ] Local dev: MongoDB runs via Docker Compose
- [ ] Sessions save/load correctly to MongoDB
- [ ] Multi-user: Users only see their own sessions
- [ ] Migration: File-based sessions migrate to MongoDB
- [ ] Tests: 90%+ coverage on storage layer
- [ ] Railway: Production deployment uses Railway MongoDB plugin
- [ ] Developer experience: `make setup && make mongo-up` gets new dev running
- [ ] Voice mode ready: Incremental updates work for webhook efficiency

---

## Open Questions

1. **User Authentication**: Should we build full user registration/login, or continue with password-based access for now?
2. **Session Sharing**: Future feature - allow users to share sessions with others?
3. **Data Retention**: Should old sessions be auto-archived/deleted after X days?
4. **Backup Strategy**: Railway MongoDB backups sufficient, or need separate backup solution?

---

This design provides a complete MongoDB migration path with multi-user support, optimized for your local → Railway deployment workflow.
