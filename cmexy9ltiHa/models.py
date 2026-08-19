"""
Data models for ESP32 Flasher application.
"""
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class FileEntry:
    """Represents a single file to flash."""
    address: str  # hex format: 0x1000
    path: str     # file path

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return FileEntry(**data)


@dataclass
class FlashProfile:
    """User-defined profile for flashing configuration."""
    name: str
    description: str = ""
    files: List[FileEntry] = None
    baud_rate: int = 460800
    port: str = ""
    auto_detect: bool = True
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.files is None:
            self.files = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        data = asdict(self)
        data['files'] = [f.to_dict() for f in self.files]
        data['updated_at'] = datetime.now().isoformat()
        return data

    @staticmethod
    def from_dict(data):
        """Create FlashProfile from dict, converting files list."""
        data_copy = data.copy()  # Make a copy to avoid modifying original dict
        files_data = data_copy.pop('files', [])
        files = [FileEntry.from_dict(f) for f in files_data]
        return FlashProfile(**data_copy, files=files)


@dataclass
class FlashOperation:
    """Records a flash operation for history."""
    profile_name: str
    port: str
    baud_rate: int
    files_count: int
    success: bool
    timestamp: datetime = None
    duration_seconds: float = 0
    error_message: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self):
        data = asdict(self)
        # Convert datetime to ISO format string
        if isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data

    @staticmethod
    def from_dict(data):
        data_copy = data.copy()
        # Convert ISO format string back to datetime if needed
        if isinstance(data_copy.get('timestamp'), str):
            data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])
        return FlashOperation(**data_copy)
