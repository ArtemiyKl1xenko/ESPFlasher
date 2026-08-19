"""
Configuration and profile manager for ESP32 Flasher.
"""
import json
import os
from typing import List, Optional
from pathlib import Path
from models import FlashProfile, FlashOperation


class ConfigManager:
    """Manages profiles, history, and application configuration."""

    def __init__(self, config_dir: str = None):
        """Initialize config manager with a directory for storing configs."""
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser("~"), ".esp32_flasher")

        self.config_dir = Path(config_dir)
        self.profiles_dir = self.config_dir / "profiles"
        self.history_file = self.config_dir / "history.json"
        self.last_config_file = self.config_dir / "last_config.json"

        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create necessary directories if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    # ============ PROFILE MANAGEMENT ============

    def get_all_profiles(self) -> List[FlashProfile]:
        """Load all profiles from disk."""
        profiles = []
        if not self.profiles_dir.exists():
            return profiles

        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profiles.append(FlashProfile.from_dict(data))
            except Exception as e:
                print(f"Error loading profile {profile_file}: {e}")

        return sorted(profiles, key=lambda p: p.name)

    def get_profile(self, name: str) -> Optional[FlashProfile]:
        """Load a specific profile by name."""
        profile_file = self.profiles_dir / f"{name}.json"

        if not profile_file.exists():
            return None

        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return FlashProfile.from_dict(data)
        except Exception as e:
            print(f"Error loading profile {name}: {e}")
            return None

    def save_profile(self, profile: FlashProfile) -> bool:
        """Save a profile to disk."""
        try:
            profile_file = self.profiles_dir / f"{profile.name}.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving profile {profile.name}: {e}")
            return False

    def delete_profile(self, name: str) -> bool:
        """Delete a profile by name."""
        try:
            profile_file = self.profiles_dir / f"{name}.json"
            if profile_file.exists():
                profile_file.unlink()
            return True
        except Exception as e:
            print(f"Error deleting profile {name}: {e}")
            return False

    def profile_exists(self, name: str) -> bool:
        """Check if a profile exists."""
        return (self.profiles_dir / f"{name}.json").exists()

    # ============ HISTORY MANAGEMENT ============

    def add_operation_to_history(self, operation: FlashOperation) -> bool:
        """Add a flash operation to history."""
        try:
            history = self._load_history()
            history.append(operation.to_dict())

            # Keep only last 100 operations
            if len(history) > 100:
                history = history[-100:]

            self._save_history(history)
            return True
        except Exception as e:
            print(f"Error adding operation to history: {e}")
            return False

    def get_history(self, limit: int = 50) -> List[FlashOperation]:
        """Get recent operations from history."""
        try:
            history = self._load_history()
            # Return most recent first
            recent = history[-limit:] if limit > 0 else history
            return [FlashOperation.from_dict(op) for op in reversed(recent)]
        except Exception:
            return []

    def _load_history(self) -> list:
        """Load history from disk."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_history(self, history: list):
        """Save history to disk."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def clear_history(self) -> bool:
        """Clear all history."""
        try:
            self._save_history([])
            return True
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False

    # ============ LAST CONFIGURATION ============

    def save_last_config(self, config: dict) -> bool:
        """Save last used configuration."""
        try:
            with open(self.last_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving last config: {e}")
            return False

    def load_last_config(self) -> dict:
        """Load last used configuration."""
        if not self.last_config_file.exists():
            return {}

        try:
            with open(self.last_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    # ============ IMPORT/EXPORT ============

    def export_profile(self, profile_name: str, export_path: str) -> bool:
        """Export a profile to a file."""
        try:
            profile = self.get_profile(profile_name)
            if not profile:
                return False

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting profile: {e}")
            return False

    def import_profile(self, import_path: str) -> Optional[FlashProfile]:
        """Import a profile from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                profile = FlashProfile.from_dict(data)

                # Check if profile name already exists
                counter = 1
                original_name = profile.name
                while self.profile_exists(profile.name):
                    profile.name = f"{original_name}_{counter}"
                    counter += 1

                self.save_profile(profile)
                return profile
        except Exception as e:
            print(f"Error importing profile: {e}")
            return None
