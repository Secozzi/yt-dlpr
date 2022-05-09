"""
Default configuration for yt-dlpr
"""
from rich.highlighter import RegexHighlighter
from rich.style import Style
from rich.theme import Theme

# Format for time log
RICH_LOG_TIME_FORMAT: str = "%X"

# Color for time logged, r;g;b
LOG_TIME_COLOR: str = "66;94;125"


# RegexHighlighter
class YtDLPHighlighter(RegexHighlighter):
    base_style: str = "ytdlp."
    highlights: list = [
        r"Deleting original file (?P<delete_original>.*?) \(pass -k to keep\)",
        r"(?:.*?)Destination: (?P<filename>.*)",
    ]


# Theme for YtDLPHighlighter
ytdlp_theme = Theme(
    {
        "ytdlp.delete_original": "bold blue",
        "ytdlp.filename": "bold blue",
    }
)

# Styles for various logs
RICH_STYLES: dict = {
    "download": Style(color="green"), # Downloading
    "info": Style(color="cyan"), # General info
    "Merger": Style(color="magenta"), # Merger
    "WARNING": Style(color="bright_red", bold=True), # Warning
    "delete": Style(color="yellow"), # Deletion
    "ExtractAudio": Style(color="purple"), # Audio Extraction
    "youtube": Style(color="red3"), # Extractor name for YouTube
}

# Style for extractor names not found in `RICH_STYLES`
EXTRACTOR_STYLE: Style = Style(underline=True)

# Yt-dlpr tries to pad the info-name of the log with width
# of `MAX_LEVEL_WIDTH`
MAX_LEVEL_WIDTH: int = 11
