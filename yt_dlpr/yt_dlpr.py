import os
import re
import sys
from pathlib import Path
from typing import Union

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.style import Style
from rich.table import Table

import yt_dlp
from yt_dlpr.utils import (
    dotdict, shorten_protocol_name, format_field,
    join_nonempty, get_config, format_bytes,
)

# Regexes
STARTS_WITH_BRACKET_RE = re.compile(r"^\[(\w+)\] ?(.*)", re.DOTALL)
STARTS_WITH_DELET_RE = re.compile(r"^delet", re.IGNORECASE)

# Extractor names
IE_NAMES = [i.IE_NAME for i in yt_dlp.list_extractors(None)]


config_file = get_config()


# Create config file if none exist
if not os.path.exists(config_file):
    default_file_path = Path(__file__).parent / "default_config.py"
    with open(config_file, "w+", encoding="utf-8") as cf:
        with open(default_file_path, "r+", encoding="utf-8") as df:
            cf.write(df.read())


# Read config file
with open(config_file, "r+", encoding="utf-8") as f:
    n = dotdict()
    code = compile(f.read(), config_file, "exec")
    exec(code, n, n)


RICH_CONSOLE = Console(
    highlighter=n.YtDLPHighlighter(),
    theme=n.YTDLP_THEME,
    log_time_format=n.RICH_LOG_TIME_FORMAT,
    log_path=False,
)


class RichYoutubeDL(yt_dlp.YoutubeDL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rich_warning_previous: set = set()

    @staticmethod
    def rich_log(
        message: str,
        skip_eol: Union[bool, None],
        quiet: Union[bool, None],
        message_style: Union[Style, None] = None,
    ) -> None:
        if quiet:
            return
        if m := STARTS_WITH_BRACKET_RE.match(message):
            lvl, msg = m.group(1), m.group(2)

            # Attempt to pad
            if len(lvl) > (n.MAX_LEVEL_WIDTH - 2):
                overflow = 1
            else:
                overflow = n.MAX_LEVEL_WIDTH - len(lvl) - 2

            if lvl in n.RICH_STYLES:
                style = n.RICH_STYLES[lvl]
            elif lvl in IE_NAMES:
                style = n.EXTRACTOR_STYLE
            else:
                style = Style()

            # Log output
            message = (
                rf"\[[{style}]{lvl}[/]]"
                rf"{' ' * overflow}{escape(msg)}"
            )
        elif STARTS_WITH_DELET_RE.match(message):
            delete_style = n.RICH_STYLES["delete"]
            message = (
                rf"\[[{delete_style}]deleting[/]] "
                rf"{escape(message)}"  # Message
            )
        else:
            message = escape(message)

        RICH_CONSOLE.log(
            message, end="" if skip_eol else "\n", style=message_style
        )
        if n.SPLIT_MULTINE and (
            len(message + n.log_width_space) > RICH_CONSOLE.width
        ):
            RICH_CONSOLE.print("")

    def to_screen(
        self,
        message: str,
        skip_eol: Union[bool, None] = False,
        quiet: Union[bool, None] = None,
    ) -> None:
        self.rich_log(message, skip_eol=skip_eol, quiet=quiet)

    def to_stdout(
        self,
        message: str,
        skip_eol: Union[bool, None] = False,
        quiet: Union[bool, None] = None,
    ) -> None:
        self.rich_log(message, skip_eol=skip_eol, quiet=quiet)

    def report_warning(self, message: str, only_once: bool = False) -> None:
        if self.params.get("no_warnings"):
            return
        if only_once:
            if message in self.rich_warning_previous:
                return
            self.rich_warning_previous.add(message)
        warning_style = n.RICH_STYLES["WARNING"]
        RICH_CONSOLE.log(
            rf"\[[{warning_style}]WARNING[/]] "
            rf"{escape(message)}",
        )

    def deprecation_warning(self, message: str) -> None:
        self.rich_log(
            f"[DeprecationWarning] {message}",
            skip_eol=False,
            quiet=False,
        )

    def report_error(self, message: str, *args, **kwargs) -> None:
        self.rich_log(
            f"[ERROR] {message}",
            skip_eol=False,
            quiet=False,
            message_style=n.MESSAGE_STYLES["ERROR"],
        )

    def report_file_already_downloaded(self, file_name: str) -> None:
        try:
            self.rich_log(
                f'[download] "{file_name}" has already been downloaded',
                skip_eol=False,
                quiet=False,
            )
        except UnicodeEncodeError:
            self.rich_log(
                "[download] The file has already been downloaded",
                skip_eol=False,
                quiet=False,
            )

    def report_file_delete(self, file_name: str) -> None:
        try:
            self.rich_log(
                f'[delete] Deleting existing file "{file_name}"',
                skip_eol=False,
                quiet=False,
            )
        except UnicodeEncodeError:
            self.rich_log(
                "[delete] Deleting existing file",
                skip_eol=False,
                quiet=False,
            )

    def list_formats(self, info_dict: dict) -> None:
        if not info_dict.get("formats") and not info_dict.get("url"):
            self.rich_log(
                f"[info] {info_dict['id']} has no formats",
                skip_eol=False,
                quiet=False,
            )
            return

        table = Table(
            box=box.SIMPLE_HEAD,
            show_lines=False,
            pad_edge=False,
            show_edge=False,
            padding=(0, 0),
        )
        table.add_column("[yellow]ID[/]", style=Style(color="green"))
        table.add_column("[yellow]EXT[/]")
        table.add_column("[yellow]RESOLUTION[/]")
        table.add_column("[yellow]FPS[/]", justify="right")
        table.add_column("[blue]│[/]", style=Style(color="blue"))
        table.add_column("[yellow]FILESIZE[/]", justify="right")
        table.add_column("[yellow]TBR[/]", justify="right")
        table.add_column("[yellow]PROTO[/]")
        table.add_column("[blue]│[/]", style=Style(color="blue"))
        table.add_column("[yellow]VCODEC[/]")
        table.add_column("[yellow]VBR[/]", justify="right")
        table.add_column("[yellow]ACODEC[/]")
        table.add_column("[yellow]ABR[/]", justify="right")
        table.add_column("[yellow]ASR[/]", justify="right")
        table.add_column("[yellow]MORE INFO[/]")

        formats = info_dict.get("formats", [info_dict])
        for i, f in enumerate(formats):
            table.add_row(
                format_field(f, "format_id"),
                format_field(f, "ext"),
                format_field(
                    f, func=self.format_resolution, ignore=("audio only", "images")
                ),
                format_field(f, "fps"),
                "│",
                format_field(f, "filesize", func=format_bytes)
                + format_field(f, "filesize_approx", "~ %s", func=format_bytes),
                format_field(f, "tbr", "%dk"),
                shorten_protocol_name(f.get("protocol", "")),
                "│",
                format_field(f, "vcodec", default="unknown").replace(
                    "none",
                    "images" if f.get("acodec") == "none" else "[dim]audio only[/]",
                ),
                format_field(f, "vbr", "%dk"),
                format_field(f, "acodec", default="unknown").replace(
                    "none", "" if f.get("vcodec") == "none" else "[dim]video only[/]"
                ),
                format_field(f, "abr", "%dk"),
                format_field(f, "asr", "%dHz"),
                join_nonempty(
                    "[light red]UNSUPPORTED[/]"
                    if f.get("ext") in ("f4f", "f4m")
                    else None,
                    format_field(f, "language", "[%s]"),
                    join_nonempty(
                        format_field(f, "format_note"),
                        format_field(f, "container", ignore=(None, f.get("ext"))),
                        delim=", ",
                    ),
                    delim=" ",
                ),
                style=n.TABLE_ALTERNATE_STYLE if i % 2 == 1 else Style(),
            )
        self.rich_log(
            f"[info] Available formats for {info_dict['id']}:",
            skip_eol=False,
            quiet=False,
        )
        RICH_CONSOLE.log(table)

    def list_thumbnails(self, info_dict: dict) -> None:
        thumbnails = list(info_dict.get("thumbnails") or [])
        if not thumbnails:
            self.rich_log(
                f"[info] {info_dict['id']} has no thumbnails",
                skip_eol=False,
                quiet=False,
            )
            return

        table = Table(
            box=None,
            show_lines=False,
            pad_edge=False,
            show_edge=False,
            padding=(0, 1),
        )
        table.add_column("[yellow]ID[/]")
        table.add_column("[yellow]Width[/]")
        table.add_column("[yellow]Height[/]")
        table.add_column("[yellow]URL[/]")

        for i, t in enumerate(thumbnails):
            url = t["url"]
            table.add_row(
                str(t.get("id")),
                str(t.get("width", "unknown")),
                str(t.get("height", "unknown")),
                f"[link={url}]{url}[/]",
                style=n.TABLE_ALTERNATE_STYLE if i % 2 == 1 else Style(),
            )
        self.rich_log(
            f"[info] Available thumbnails for {info_dict['id']}:",
            skip_eol=False,
            quiet=False,
        )
        RICH_CONSOLE.log(table)

    def list_subtitles(
        self, video_id: str, subtitles: dict, name: str = "subtitles"
    ) -> None:
        def _row(lang: str, formats: list) -> list:
            exts, names = zip(
                *((f["ext"], f.get("name") or "unknown") for f in reversed(formats))
            )
            if len(set(names)) == 1:
                names = [] if names[0] == "unknown" else names[:1]
            return [lang, ", ".join(names), ", ".join(exts)]

        if not subtitles:
            self.rich_log(
                f"[info] {video_id} has no {name}",
                skip_eol=False,
                quiet=False,
            )
            return

        table = Table(
            box=None,
            show_lines=False,
            pad_edge=False,
            show_edge=False,
            padding=(0, 1),
        )
        table.add_column("[yellow]Language[/]")
        table.add_column("[yellow]Name[/]")
        table.add_column("[yellow]Formats[/]")
        for i, (lang, formats) in enumerate(subtitles.items()):
            table.add_row(
                *_row(lang, formats),
                style=n.TABLE_ALTERNATE_STYLE if i % 2 == 1 else Style(),
            )

        self.rich_log(
            f"[info] Available {name} for {video_id}:",
            skip_eol=False,
            quiet=False,
        )
        RICH_CONSOLE.log(table)
        
    def print_debug_header(self):
        class DebugHeaderPrinter:
            @staticmethod
            def debug(message):
                self.rich_log(f"[debug] {message[8:]}", skip_eol=False, quiet=False)

        _logger = self.params.get("logger")
        self.params["logger"] = DebugHeaderPrinter
        super(RichYoutubeDL, self).print_debug_header()
        self.params["logger"] = _logger

    def write_debug(self, message, only_once=False):
        if not self.params.get("verbose", False):
            return
        self.rich_log(f"[debug] {message}", skip_eol=False, quiet=False)


def _main() -> None:
    # Check for yt-dlpr options
    argv = sys.argv
    if "--yt-dlpr-config-path" in argv:
        yt_dlp.write_string(f"{config_file}\n", out=sys.stdout)
        sys.exit(0)

    if "--examples" in argv:
        RichYoutubeDL().rich_console.print(n.EXAMPLES)
        sys.exit(0)

    # yt-dlp._real_main()
    yt_dlp.setproctitle("yt-dlp")

    parser, opts, all_urls, ydl_opts = yt_dlp.parse_options()

    # Dump user agent
    if opts.dump_user_agent:
        ua = yt_dlp.traverse_obj(
            opts.headers,
            "User-Agent",
            casesense=False,
            default=yt_dlp.std_headers["User-Agent"],
        )
        yt_dlp.write_string(f"{ua}\n", out=sys.stdout)
        sys.exit(0)

    if yt_dlp.print_extractor_information(opts, all_urls):
        sys.exit(0)

    ydl_opts = {
        **ydl_opts,
        **n.RICH_YDL_OPTS,
    }

    with RichYoutubeDL(ydl_opts) as ydl:
        actual_use = all_urls or opts.load_info_filename

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

            ydl.warn_if_short_id(sys.argv[1:] if argv is None else argv)
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
                retcode = ydl.download(all_urls)
        except yt_dlp.DownloadCancelled:
            ydl.to_screen("Aborting remaining downloads")
            retcode = 101

    sys.exit(retcode)
