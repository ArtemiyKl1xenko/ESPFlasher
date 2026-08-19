"""
Integrations module - интеграции с внешними сервисами.
"""

from .github_api import GitHubAPI, GitHubRelease, GitHubAsset
from .platformio_bridge import PlatformIOBridge, PIOProject
from .ota_manager import OTAManager, OTAConfig

__all__ = [
    'GitHubAPI',
    'GitHubRelease',
    'GitHubAsset',
    'PlatformIOBridge',
    'PIOProject',
    'OTAManager',
    'OTAConfig'
]
