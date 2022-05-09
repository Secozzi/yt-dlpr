import os
import sys
from pathlib import Path

import appdirs
import yt_dlp
from yt_dlpr.yt_dlpr import actual_main


def get_config():
    config_dir = os.environ.get(
        "YT_DLPR_CONFIG_HOME", appdirs.user_config_dir("yt_dlpr", "yt_dlpr")
    )

    Path(config_dir).mkdir(parents=True, exist_ok=True)

    config_file = os.path.join(config_dir, "config.py")

    return config_file


def main():
    config_file = get_config()

    args = sys.argv
    if "--yt-dlpr-config-path" in args:
        print(config_file)
        return

    # Create config file if none exist
    if not os.path.exists(config_file):
        default_file_path = Path(__file__).parent / "default_config.py"
        with open(config_file, "w+", encoding="utf-8") as cf:
            with open(default_file_path, "r+", encoding="utf-8") as df:
                cf.write(df.read())

    # Read config file
    with open(config_file, "r+", encoding="utf-8") as f:
        namespace = {}
        code = compile(f.read(), config_file, "exec")
        exec(code, namespace, namespace)

    run_yt_dlpr(namespace)


def run_yt_dlpr(namespace):
    try:
        actual_main(namespace)
    except yt_dlp.DownloadError:
        sys.exit(1)
    except yt_dlp.SameFileError as e:
        sys.exit(f"ERROR: {e}")
    except KeyboardInterrupt:
        sys.exit("\nERROR: Interrupted by user")
    except BrokenPipeError as e:
        import os

        # https://docs.python.org/3/library/signal.html#note-on-sigpipe
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(f"\nERROR: {e}")
