from rich.highlighter import RegexHighlighter
from rich.console import Console
from rich.markup import escape
from rich.theme import Theme
from rich.style import Style
from rich.text import Text

import sys
import re

import yt_dlp

# Regexes
STARTS_WITH_BRACKET_RE = re.compile(r"^\[(\w+)\] ?(.*)", re.DOTALL)
STARTS_WITH_DELET_RE = re.compile(r"^delet", re.IGNORECASE)

# ANSI Codes stuff
RESET = "\033[0m"                         # Reset graphics mode
FINISHEDG = f"\033[32mFINISHED{RESET}"    # Green finished
FINISHEDY = f"\033[33m[FINISHED]{RESET}"  # Yellow finished

# Other constants
IE_NAMES = [i.IE_NAME for i in yt_dlp.list_extractors(None)]

def actual_main(namespace):
    # Load from namespace
    globals().update(namespace)

    # Rich Console
    c = Console(
        highlighter=YtDLPHighlighter(),
        theme=ytdlp_theme,
        log_time_format=RICH_LOG_TIME_FORMAT,
        log_path=False,
    )

    _log_width_space = " " * (len(c.get_datetime().strftime(RICH_LOG_TIME_FORMAT)) + 1)

    # ℹ️ See docstring of yt_dlp.YoutubeDL for a description of the options
    rich_ydl_opts = {
        "progress_template": {
            "download":
                (
                    f"{_log_width_space}[\033[32mdownload{RESET}] "  # Download
                    f"%(progress._percent_str)s{RESET} • "  # Percent
                    f"\033[35m%(progress.downloaded_bytes)#.2DB{RESET}/"  # Bytes downloaded
                    f"\033[35m%(progress._total_bytes_str)s{RESET} • "  # Total bytes
                    f"%(progress._speed_str|{FINISHEDG})s • "  # Speed
                    f"\033[33mETA{RESET} %(progress._eta_str|{FINISHEDY})s"  # ETA
                ),
            "download-title": "%(info.id)s-%(progress.eta)s",
        },
    }

    class RichYoutubeDL(yt_dlp.YoutubeDL):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.rich_console = c
            self.rich_warning_previous = set()

        def rich_log(self, input_message, skip_eol, quiet):
            if quiet:
                return
            if m := STARTS_WITH_BRACKET_RE.match(input_message):
                lvl, msg = m.group(1), m.group(2)

                # Try to pad
                if len(lvl) > (MAX_LEVEL_WIDTH - 2):
                    overflow = 1
                else:
                    overflow = MAX_LEVEL_WIDTH - len(lvl) - 2

                if lvl in RICH_STYLES:
                    style = RICH_STYLES[lvl]
                elif lvl in IE_NAMES:
                    style = Style(underline=True)
                else:
                    style = Style()

                # Log output
                self.rich_console.log(
                    Text("[")
                    + Text(lvl, style=style)
                    + Text("]")
                    + " " * overflow
                    + Text(msg),
                    end="" if skip_eol else "\n",
                )
            elif STARTS_WITH_DELET_RE.match(input_message):
                self.rich_console.log(
                    Text("[")
                    + Text("deleting", style=RICH_STYLES["delete"])
                    + Text("]")
                    + " "
                    + Text(input_message),
                    end="" if skip_eol else "\n",
                )
            else:
                self.rich_console.log(escape(input_message), end="" if skip_eol else "\n")

        def to_screen(self, message, skip_eol=False, quiet=None):
            self.rich_log(message, skip_eol, quiet)

        def to_stdout(self, message, skip_eol=False, quiet=False):
            self.rich_log(message, skip_eol, quiet)

        def report_warning(self, message, only_once=False):
            if self.params.get("logger") is not None:
                self.params["logger"].warning(message)
            else:
                if self.params.get("no_warnings"):
                    return
                if only_once:
                    if message in self.rich_warning_previous:
                        return
                    self.rich_warning_previous.add(message)
                self.rich_log(f"[WARNING] {message}", skip_eol=False, quiet=False)

    EXAMPLES = """\
    List all formats: [grey23 on grey78]yt -F https://www.youtube.com/watch?v=FQUrmnwCuqs[/]
    Download subtitles: [grey23 on grey78]yt --sub-lang en --write-sub https://www.youtube.com/watch?v=FQUrmnwCuqs[/]
    Desc, metadata, etc: [grey23 on grey78]--write-description --write-info-json --write-annotations --write-sub --write-thumbnail[/]
    Download audio only: [grey23 on grey78]yt -x --audio-format mp3 https://www.youtube.com/watch?v=FQUrmnwCuqs[/]
    Custom filename output: [grey23 on grey78]yt -o "Output Filename" https://www.youtube.com/watch?v=FQUrmnwCuqs[/]
    Download multiple videos: [grey23 on grey78]yt <url1> <url2>[/] or [grey23 on grey78]yt -a urls.txt[/]
    Download in certain quality: [grey23 on grey78]yt -f best https://www.youtube.com/watch?v=FQUrmnwCuqs[/]
    Available qualities:
        * best - Select the best quality format of the given file with video and audio.
        * worst - Select the worst quality format (both video and audio).
        * bestvideo - Select the best quality video-only format (e.g. DASH video). Please note that it may not be available.
        * worstvideo - Select the worst quality video-only format. May not be available.
        * bestaudio - Select the best quality audio only-format. May not be available.
        * worstaudio - Select the worst quality audio only-format. May not be available.
    """

    if "--examples" in sys.argv:
        c.print(EXAMPLES)
        sys.exit(0)

    yt_dlp.workaround_optparse_bug9161()

    yt_dlp.setproctitle('yt-dlp')

    # ℹ️ See the public functions in yt_dlp.YoutubeDL for for other available functions.
    # Eg: "ydl.download", "ydl.download_with_info_file"
    parser, opts, args, old_ydl_opts = yt_dlp.parse_options()

    ydl_opts = {**old_ydl_opts, **rich_ydl_opts}

    if opts.dump_user_agent:
        ua = yt_dlp.traverse_obj(
            opts.headers,
            "User-Agent",
            casesense=False,
            default=yt_dlp.std_headers["User-Agent"],
        )
        c.log(ua)

    with RichYoutubeDL(ydl_opts) as ydl:
        actual_use = args or opts.load_info_filename

        # Remove cache dir
        if opts.rm_cachedir:
            ydl.cache.remove()

        # Update version
        if opts.update_self:
            # If updater returns True, exit. Required for windows
            if yt_dlp.run_update(ydl):
                if actual_use:
                    sys.exit("ERROR: The program must exit for the update to complete")
                sys.exit()

        # Maybe do nothing
        if not actual_use:
            if opts.update_self or opts.rm_cachedir:
                sys.exit()

            ydl.warn_if_short_id(sys.argv[1:] if sys.argv is None else sys.argv)
            parser.error(
                "You must provide at least one URL.\n"
                "Type yt-dlp --help to see a list of all options."
            )

        try:
            if opts.load_info_filename is not None:
                retcode = ydl.download_with_info_file(
                    yt_dlp.expand_path(opts.load_info_filename)
                )
            else:
                retcode = ydl.download(args)
        except yt_dlp.DownloadCancelled:
            ydl.to_screen("Aborting remaining downloads")
            retcode = 101

    sys.exit(retcode)
