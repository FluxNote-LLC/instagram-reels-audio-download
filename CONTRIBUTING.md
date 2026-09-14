# Contributing

Bug reports and pull requests are welcome. Include your OS, Python and yt-dlp versions, the command used, and a redacted error log. Do not include cookies, account credentials, or private media.

Install the project in a virtual environment and run `python -m unittest discover -s tests -v` before opening a pull request. Add regression coverage for behavior changes. Keep downloads sequential and authentication optional. For extractor failures, first check whether the latest yt-dlp release fixes the issue.
