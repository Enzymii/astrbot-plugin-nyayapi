from pathlib import Path

from astrbot.core.utils.astrbot_path import get_astrbot_data_path


def get_plugin_data_path(plugin_name: str) -> Path:
    return Path(get_astrbot_data_path()) / "plugin_data" / plugin_name
