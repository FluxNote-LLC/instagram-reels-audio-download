"""Validate Reel URLs and delegate extraction to yt-dlp and FFmpeg."""

import argparse
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

from . import __version__


def normalize_url(value: str) -> str:
    """Accept only direct Instagram Reel links; discard tracking parameters."""
    value = value.strip()
    if not value.startswith(("https://", "http://")):
        value = "https://" + value
    try:
        url = urlsplit(value)
        valid_host = url.hostname in {"instagram.com", "www.instagram.com", "m.instagram.com"}
        valid_authority = not (url.username or url.password or url.port)
    except ValueError as exc:
        raise ValueError("Invalid Reel URL") from exc
    match = re.fullmatch(r"/reels?/([A-Za-z0-9_-]+)/?", url.path)
    if not valid_host or not valid_authority or not match:
        raise ValueError("Use a direct Instagram Reel URL: https://www.instagram.com/reel/SHORTCODE/")
    return f"https://www.instagram.com/reel/{match.group(1)}/"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Download Instagram Reel audio locally with yt-dlp and FFmpeg.")
    result.add_argument("urls", nargs="*", help="one or more Instagram Reel URLs")
    result.add_argument("--version", action="version", version=__version__)
    result.add_argument("-b", "--batch-file", type=Path, help="UTF-8 text file, one Reel URL per line")
    result.add_argument("-o", "--output", type=Path, default=Path("downloads"), help="output directory (default: downloads)")
    result.add_argument("-f", "--format", choices=("mp3", "m4a", "wav"), default="mp3")
    result.add_argument("--quality", choices=("128", "192", "256", "320"), default="192", help="lossy audio bitrate in kbps (default: 192; ignored for WAV)")
    auth = result.add_mutually_exclusive_group()
    auth.add_argument("--cookies", type=Path, help="Netscape cookies file")
    auth.add_argument("--cookies-from-browser", choices=("chrome", "chromium", "edge", "firefox", "brave", "opera", "safari", "vivaldi"))
    return result


def build_command(args: argparse.Namespace, url: str) -> list[str]:
    command = [
        sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-playlist",
        "--no-overwrites", "--restrict-filenames", "--socket-timeout", "30",
        "--retries", "3", "--format", "bestaudio/best", "--extract-audio",
        "--audio-format", args.format, "--audio-quality", args.quality + "K",
        "--paths", str(args.output.expanduser().resolve()),
        "--output", "%(id)s.%(ext)s", "--print", "after_move:filepath",
        "--no-simulate",
    ]
    if args.cookies:
        command.extend(["--cookies", str(args.cookies.expanduser().resolve())])
    if args.cookies_from_browser:
        command.extend(["--cookies-from-browser", args.cookies_from_browser])
    return [*command, "--", url]


def main(argv=None) -> int:
    cli = parser()
    args = cli.parse_args(argv)
    values = list(args.urls)
    if args.batch_file:
        try:
            values.extend(line.strip() for line in args.batch_file.expanduser().read_text(encoding="utf-8-sig").splitlines()
                          if line.strip() and not line.lstrip().startswith("#"))
        except (OSError, UnicodeError) as exc:
            cli.error(f"Cannot read batch file: {exc}")
    if not values:
        cli.error("Provide a Reel URL or --batch-file.")
    try:
        urls = list(dict.fromkeys(normalize_url(value) for value in values))
    except ValueError as exc:
        cli.error(str(exc))
    if args.cookies and not args.cookies.expanduser().is_file():
        cli.error("Cookies file does not exist.")
    if importlib.util.find_spec("yt_dlp") is None:
        print("Missing yt-dlp. Install this project with: python -m pip install -e .", file=sys.stderr)
        return 1
    if any(shutil.which(binary) is None for binary in ("ffmpeg", "ffprobe")):
        print("Install FFmpeg (including ffprobe) and add it to PATH. See README.md.", file=sys.stderr)
        return 1
    try:
        args.output.expanduser().mkdir(parents=True, exist_ok=True)
        failures = 0
        for index, url in enumerate(urls, 1):
            print(f"[{index}/{len(urls)}] {url}", flush=True)
            if subprocess.run(build_command(args, url), check=False).returncode:
                failures += 1
                print("Download failed. Update yt-dlp; if Instagram requires login, use your browser cookies.", file=sys.stderr)
        print(f"Finished: {len(urls) - failures} succeeded, {failures} failed.")
        return 1 if failures else 0
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    except OSError as exc:
        print(f"Cannot download audio: {exc}", file=sys.stderr)
        return 1
