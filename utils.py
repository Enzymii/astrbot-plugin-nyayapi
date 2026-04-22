import json
from collections.abc import Mapping
from pathlib import Path

from astrbot.core.utils.astrbot_path import get_astrbot_data_path

fallback = "mochun"
_EMOJI_QCID_MAP: dict[str, int] | None = None


def get_plugin_data_path(plugin_name: str) -> Path:
    return Path(get_astrbot_data_path()) / "plugin_data" / plugin_name


def get_emoji_qcid_map() -> dict[str, int]:
    """读取并缓存本地 emojiId -> qcid 映射。"""
    global _EMOJI_QCID_MAP
    if _EMOJI_QCID_MAP is not None:
        return _EMOJI_QCID_MAP

    index_path = Path(__file__).with_name("config").joinpath("qq_emoji_index.json")
    try:
        with index_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        _EMOJI_QCID_MAP = {}
        return _EMOJI_QCID_MAP

    mapping: dict[str, int] = {}
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            emoji_id = item.get("emojiId")
            qcid = item.get("qcid")
            if isinstance(emoji_id, str) and isinstance(qcid, int):
                mapping[emoji_id] = qcid

    _EMOJI_QCID_MAP = mapping
    return _EMOJI_QCID_MAP


class _SafeFormatDict(dict[str, object]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _get_texts_dir() -> Path:
    return Path(__file__).resolve().parent / "texts"


def _normalize_style_name(style_name: str) -> str:
    normalized = style_name.strip()
    return normalized or fallback


def _load_style_templates(style_name: str) -> dict[str, object]:
    style_name = _normalize_style_name(style_name)
    texts_dir = _get_texts_dir()
    style_file = texts_dir / f"{style_name}.json"
    if not style_file.exists():
        style_file = texts_dir / f"{fallback}.json"
    loaded: dict[str, object] = {}
    if style_file.exists():
        raw_data = json.loads(style_file.read_text(encoding="utf-8"))
        if isinstance(raw_data, dict):
            loaded = raw_data
    return loaded


def get_text_template(style_name: str, key_path: str, default: str = "") -> str:
    current: object = _load_style_templates(style_name)
    for key in key_path.split("."):
        if not isinstance(current, Mapping) or key not in current:
            return default
        current = current[key]
    if isinstance(current, str):
        return current
    return default


def render_text_template(
    style_name: str,
    key_path: str,
    context: dict[str, object],
    default_template: str,
) -> str:
    template = get_text_template(style_name, key_path, default_template)
    return template.format_map(_SafeFormatDict(context))
