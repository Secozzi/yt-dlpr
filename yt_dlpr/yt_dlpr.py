import os
import re
import sys
from pathlib import Path
from typing import Callable, Union

import appdirs
from rich.console import Console
from rich.markup import escape
from rich.style import Style

import yt_dlp

# Regexes
STARTS_WITH_BRACKET_RE = re.compile(r"^\[(\w+)\] ?(.*)", re.DOTALL)
STARTS_WITH_DELET_RE = re.compile(r"^delet", re.IGNORECASE)

# Extractor names
IE_NAMES = [i.IE_NAME for i in yt_dlp.list_extractors(None)]


class dotdict(dict):
    __getattr__ = dict.get


def get_config():
    config_dir = os.environ.get(
        "YT_DLPR_CONFIG_HOME", appdirs.user_config_dir("yt_dlpr", "yt_dlpr")
    )

    Path(config_dir).mkdir(parents=True, exist_ok=True)

    return os.path.join(config_dir, "config.py")


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


class RichYoutubeDL(yt_dlp.YoutubeDL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rich_console: Console = Console(
            highlighter=n.YtDLPHighlighter(),
            theme=n.YTDLP_THEME,
            log_time_format=n.RICH_LOG_TIME_FORMAT,
            log_path=False,
        )
        self.rich_warning_previous: set = set()

    def rich_log(
        self,
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

        self.rich_console.log(
            message, end="" if skip_eol else "\n", style=message_style
        )
        if n.SPLIT_MULTINE and (
            len(message + n._log_width_space) > self.rich_console.width
        ):
            self.rich_console.print("")

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
        self.rich_console.log(
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
                f"[download] The file has already been downloaded",
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
                f"[delete] Deleting existing file",
                skip_eol=False,
                quiet=False,
            )

    def __old_to_screen(
        self,
        message: str,
        skip_eol: Union[bool, None] = False,
        quiet: Union[bool, None] = None,
    ):
        """Print message to screen if not in quiet mode"""
        if self.params.get("logger"):
            self.params["logger"].debug(message)
            return
        if (
            self.params.get("quiet") if quiet is None else quiet
        ) and not self.params.get("verbose"):
            return
        self._write_string(
            "%s%s" % (self._bidi_workaround(message), ("" if skip_eol else "\n")),
            self._out_files["screen"],
        )

    def __old_to_stdout(
        self,
        message: str,
        skip_eol: Union[bool, None] = False,
        quiet: Union[bool, None] = None,
    ):
        """Print message to stdout"""
        if quiet is not None:
            self.deprecation_warning(
                '"YoutubeDL.to_stdout" no longer accepts the argument quiet. Use "YoutubeDL.to_screen" instead'
            )
        self._write_string(
            "%s%s" % (self._bidi_workaround(message), ("" if skip_eol else "\n")),
            self._out_files["print"],
        )

    def list_formats(self, info_dict: dict) -> None:
        self.__list_table(
            info_dict["id"], "formats", self.render_formats_table, info_dict
        )

    def list_thumbnails(self, info_dict: dict) -> None:
        self.__list_table(
            info_dict["id"], "thumbnails", self.render_thumbnails_table, info_dict
        )

    def list_subtitles(
        self, video_id: str, subtitles: dict, name: str = "subtitles"
    ) -> None:
        self.__list_table(
            video_id, name, self.render_subtitles_table, video_id, subtitles
        )

    def __list_table(self, video_id: str, name: str, func: Callable, *args) -> None:
        table = func(*args)
        if not table:
            self.rich_log(
                f"[info] {video_id} has no {name}", skip_eol=False, quiet=False
            )
            return

        self.rich_log(
            f"[info] Available {name} for {video_id}:", skip_eol=False, quiet=False
        )
        self.__old_to_stdout(table)


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
