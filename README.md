# Instagram Reels Audio

A small, open-source command-line tool to save an Instagram Reel's audio locally. Paste a Reel link, get an MP3. No API keys, hosted service, or paid API required.

- MP3, M4A, and WAV output
- Multiple URLs or a batch file, processed sequentially
- Optional cookies from your browser or a Netscape cookies file
- Tracking parameters removed and duplicate URLs skipped within each run
- Predictable filenames (`SHORTCODE.mp3`) and no overwriting existing audio
- MIT licensed

## Install

Requires **Python 3.10+** and **FFmpeg**, including `ffprobe`, on your PATH.

Install FFmpeg using your operating system's package manager, for example `brew install ffmpeg` on macOS or `sudo apt install ffmpeg` on Ubuntu. Windows users can get a build from [FFmpeg's download page](https://ffmpeg.org/download.html) and add its `bin` folder to PATH.

From this repository:

```sh
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
reel-audio --help
```

## Download

```sh
reel-audio 'https://www.instagram.com/reel/SHORTCODE/'
reel-audio 'https://www.instagram.com/reel/SHORTCODE/' --format m4a --output ./audio
reel-audio 'https://www.instagram.com/reel/SHORTCODE/' --format mp3 --quality 320
reel-audio 'https://www.instagram.com/reel/SHORTCODE/' --format wav
```

Replace `SHORTCODE` with a real Reel ID. Audio is saved in `downloads/` by default; the final path is printed after extraction. `python -m instagram_reels_audio` also works.

For batches, pass multiple quoted URLs, or create `reels.txt` with one URL per line:

```sh
reel-audio --batch-file reels.txt --output ./audio
```

Blank lines and lines starting with `#` are ignored. All URLs are validated before downloading. One failed download does not stop the remaining URLs. Exit status is `0` on success, `1` if a download/setup fails, `2` for invalid arguments, or `130` when cancelled.

## When Instagram requires login

Log into Instagram in your browser, then explicitly opt into reading that session:

```sh
reel-audio 'https://www.instagram.com/reel/SHORTCODE/' --cookies-from-browser firefox
# Or use an existing Netscape-format cookie file:
reel-audio 'https://www.instagram.com/reel/SHORTCODE/' --cookies ./cookies.txt
```

Cookies are credentials: keep them local and never attach them to an issue or commit them. This tool does not ask for your password or send cookies to a separate download service. yt-dlp uses the selected session to request media. Browser cookie access may require closing the browser or unlocking its credential store.

## Limitations and troubleshooting

This extracts the Reel's complete mixed soundtrack, including speech and effects. It does not isolate music or retrieve a separate original song. Converting to WAV or a higher bitrate cannot improve the source quality. Videos may be downloaded temporarily during extraction.

Only direct `/reel/ID/` and `/reels/ID/` links are accepted. Profiles, stories, `/share/` links, and audio collection pages are not supported. Open a shared link in Instagram and copy the direct Reel URL first.

Instagram can require login, rate-limit requests, or change its endpoints. Cookies do not guarantee access; unavailable content remains unavailable. Update the extractor first if downloads stop working:

```sh
python -m pip install --upgrade yt-dlp
```

If the stable release still fails, try `python -m pip install --upgrade --pre yt-dlp` and consult [yt-dlp's documentation](https://github.com/yt-dlp/yt-dlp#readme). For missing FFmpeg errors, check both `ffmpeg -version` and `ffprobe -version`. Existing audio files are preserved; use a different output directory to download a new bitrate of the same Reel.

Download content you own or have permission to use. This project is not affiliated with Instagram or Meta.

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
```

Tests cover URL validation, command construction, batch failures, and real FFmpeg audio extraction from a generated local video. They do not make requests to Instagram or need credentials. CI runs on Linux and Windows with Python 3.10 and 3.12. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE). Extraction is powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/); those projects have their own licenses.
