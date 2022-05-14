"""
Default configuration for yt-dlpr
"""
# Imports
from collections import defaultdict
from datetime import datetime

from rich.highlighter import RegexHighlighter
from rich.style import Style
from rich.theme import Theme

default = lambda: Style()

####################
# DON'T EDIT ABOVE #
####################

# Format for time log
RICH_LOG_TIME_FORMAT: str = "%X"

# Color for time logged, r;g;b
LOG_TIME_COLOR: str = "66;94;125"

# Is message occupies multiple lines, print a newline between
SPLIT_MULTINE: bool = False


# RegexHighlighter
class YtDLPHighlighter(RegexHighlighter):
    base_style: str = "ytdlp."
    highlights: list = [
        r"Deleting original file (?P<delete_original>.*?) \(pass -k to keep\)",
        r"(?:.*?)Destination: (?P<destination>.*)",
    ]


# Theme for YtDLPHighlighter
YTDLP_THEME = Theme(
    {
        "ytdlp.delete_original": "underline bold",
        "ytdlp.destination": "underline bold",
    }
)

# Styles for various logs
RICH_STYLES: defaultdict = defaultdict(default, **{
    "download": Style(color="green"),  # Downloading
    "info": Style(color="cyan"),  # General info
    "Merger": Style(color="magenta"),  # Merger
    "WARNING": Style(color="bright_red", bold=True),  # Warning
    "ERROR": Style(color="bright_red", italic=True),  # Error
    "delete": Style(color="yellow"),  # Deletion
    "ExtractAudio": Style(color="purple"),  # Audio Extraction
    "debug": Style(italic=True),  # Debug
    "generic": Style(),  # Generic
    "youtube": Style(color="red3"),  # Extractor name for YouTube
})

# Style for message on level
MESSAGE_STYLES: defaultdict = defaultdict(default, **{
    "ERROR": Style(bgcolor="black")
})

# Style for extractor names not found in `RICH_STYLES`
EXTRACTOR_STYLE: Style = Style(underline=True)

# yt-dlpr tries to pad the info-name of the log with width
# of `MAX_LEVEL_WIDTH`
MAX_LEVEL_WIDTH: int = 11

####################################################################################
#             CONSTANTS FOR PROGRESS TEMPLATE - EDITING NOT RECOMMENDED            #
_log_width_space = " " * (len(datetime.now().strftime(RICH_LOG_TIME_FORMAT)) + 1)  #
RESET = "\033[0m"  # Reset graphics mode                                           #
####################################################################################

GREEN_COLOR = "\033[32m"  # ANSI escape code for green
YELLOW_COLOR = "\033[33m"  # ANSI escape code for green
MAGENTA_COLOR = "\033[35m"  # ANSI escape code for green
FINISHED_SPEED = f"{GREEN_COLOR}FINISHED{RESET}"  # Green finished - for speed
FINISHED_ETA = f"{YELLOW_COLOR}[FINISHED]{RESET} -"  # Yellow finished - for eta

# String for progress bar - check https://github.com/yt-dlp/yt-dlp#output-template for more info
RICH_YDL_OPTS = {
    "progress_template": {
        "download":
            (
                f"{_log_width_space}[{GREEN_COLOR}download{RESET}] "  # Download - prepended by log width to align
                f"%(progress._percent_str)s{RESET} • "  # Percent
                f"{MAGENTA_COLOR}%(progress.downloaded_bytes)#.2DB{RESET}/"  # Bytes downloaded
                f"{MAGENTA_COLOR}%(progress._total_bytes_str)s{RESET} • "  # Total bytes
                f"%(progress._speed_str|{FINISHED_SPEED})s • "  # Speed
                f"{YELLOW_COLOR}ETA{RESET} %(progress._eta_str|{FINISHED_ETA})s "  # ETA
                f"%(progress._elapsed_str|)s"  # Time elapsed - when download is finished
            ),
        "download-title": "%(info.id)s-%(progress.eta)s",
    },
}

# Examples printed when using --examples
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
