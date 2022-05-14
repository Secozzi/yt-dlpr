# yt-dlpr
Rich output of yt-dlp

## yt-dlpr options

``--examples`` - print out examples

``--yt-dlpr-config-path`` - print out path for config file

## Examples of yt-dlp vs yt-dlpr

Downloading video using yt-dlp:

[![asciicast](https://asciinema.org/a/493210.svg)](https://asciinema.org/a/493210)

Downlaoding video using yt-dlpr:

[![asciicast](https://asciinema.org/a/493207.svg)](https://asciinema.org/a/493207)

Extracting audio using yt-dlp:

[![asciicast](https://asciinema.org/a/493214.svg)](https://asciinema.org/a/493214)

Extracting audio using yt-dlpr:

[![asciicast](https://asciinema.org/a/493212.svg)](https://asciinema.org/a/493212)

## Changelog

### [1.2] - 2022-05-14

#### Added

- Added support for `--list-formats`, `--list-thumnails`, and `--list-subs`

### [1.1] - 2022-05-11

#### Added

- Added SPLIT_MULTINE option
- Added MESSAGE_STYLES dict, styling entire message

### Fixed

- Fixed styling for warning
- Tables no longer broken