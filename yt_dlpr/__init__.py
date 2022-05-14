import sys

import yt_dlp
from yt_dlpr.yt_dlpr import _main


def main():
    try:
        _main()
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
