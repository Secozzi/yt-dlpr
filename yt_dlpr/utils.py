import os
from collections.abc import Iterable
import appdirs
import yt_dlp
from pathlib import Path
from math import log


class dotdict(dict):
    __getattr__ = dict.get


def shorten_protocol_name(proto, simplify=False):
    short_protocol_names = {
        'm3u8_native': 'm3u8_n',
        'rtmp_ffmpeg': 'rtmp_f',
        'http_dash_segments': 'dash',
        'http_dash_segments_generator': 'dash_g',
        'niconico_dmc': 'dmc',
        'websocket_frag': 'WSfrag',
    }
    if simplify:
        short_protocol_names.update({
            'https': 'http',
            'ftps': 'ftp',
            'm3u8_native': 'm3u8',
            'http_dash_segments_generator': 'dash',
            'rtmp_ffmpeg': 'rtmp',
            'm3u8_frag_urls': 'm3u8',
            'dash_frag_urls': 'dash',
        })
    return short_protocol_names.get(proto, proto)


def float_or_none(v, scale=1, invscale=1, default=None):
    if v is None:
        return default
    try:
        return float(v) * invscale / scale
    except (ValueError, TypeError):
        return default


def variadic(x, allowed_types=(str, bytes, dict)):
    return x if isinstance(x, Iterable) and not isinstance(x, allowed_types) else (x,)


def format_field(obj, field=None, template='%s', ignore=(None, ''), default='', func=None):
    val = yt_dlp.traverse_obj(obj, *variadic(field))
    if val in ignore:
        return default
    return template % (func(val) if func else val)


def join_nonempty(*values, delim='-', from_dict=None):
    if from_dict is not None:
        values = map(from_dict.get, values)
    return delim.join(map(str, filter(None, values)))


def get_config():
    config_dir = os.environ.get(
        "YT_DLPR_CONFIG_HOME", appdirs.user_config_dir("yt_dlpr", "yt_dlpr")
    )

    Path(config_dir).mkdir(parents=True, exist_ok=True)

    return os.path.join(config_dir, "config.py")


def format_decimal_suffix(num, fmt='%d%s', *, factor=1000):
    """ Formats numbers with decimal sufixes like K, M, etc """
    num, factor = float_or_none(num), float(factor)
    if num is None or num < 0:
        return None
    POSSIBLE_SUFFIXES = 'kMGTPEZY'
    exponent = 0 if num == 0 else min(int(log(num, factor)), len(POSSIBLE_SUFFIXES))
    suffix = ['', *POSSIBLE_SUFFIXES][exponent]
    if factor == 1024:
        suffix = {'k': 'Ki', '': ''}.get(suffix, f'{suffix}i')
    converted = num / (factor ** exponent)
    return fmt % (converted, suffix)


def format_bytes(bytes):
    return format_decimal_suffix(bytes, '%.2f%sB', factor=1024) or 'N/A'
