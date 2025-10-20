import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from drama_detective.models import Session, SessionStatus

class SessionManager:
    def __init__(self, data_dir: Optional[Path] = None):
        # set data_dir 
        # create directory if it doesnt exist
        if data_dir is None:
            self.data_dir = Path.home() / ".drama_detective" / ".sessions"
        else:
            self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        pass
    def create_session(self, incident_name: str) -> Session:
        # TODO: Create Session with:
        #   - Random UUID for session_id
        #   - Current timestamp for created_at
        #   - ACTIVE status
        session = Session(
            session_id = str(uuid.uuid4()),
            incident_name=incident_name,
            created_at=datetime.now().isoformat()
        )
        return session

    def save_session(self, session: Session) -> None:
        # TODO: Save session to JSON file
        # Filename: {session_id}.json
        # Use session.model_dump() to serialize
        filename = self.data_dir / f"{session.session_id}.json"
        with open(filename, 'w') as f:
            json.dump(session.model_dump(), f, indent=2)
        return session

    def load_session(self, session_id: str) -> Session:
        # TODO: Load session from JSON file
        # Raise FileNotFoundError if not found
        # Use Session(**data) to deserialize
        filename = self.data_dir / f"{session_id}.json"
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            return Session(**data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Session {session_id} not found")

    def list_sessions(self) -> list[Session]:
        # TODO: Find all *.json files in data_dir
        # Load each one (skip corrupted files)
        # Return sorted by created_at (newest first)
        sessions = []
        
        for json_file in self.data_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                session = Session(**data)
                sessions.append(session)
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions