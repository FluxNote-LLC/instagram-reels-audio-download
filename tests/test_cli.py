import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from instagram_reels_audio.cli import build_command, main, normalize_url, parser


class CLITests(unittest.TestCase):
    def test_normalize(self):
        for value in ('https://www.instagram.com/reel/ABC-12_/?igsh=secret',
                      'instagram.com/reels/ABC-12_', 'http://m.instagram.com/reel/ABC-12_/'):
            self.assertEqual(normalize_url(value), 'https://www.instagram.com/reel/ABC-12_/')

    def test_reject_other_targets(self):
        for value in ('https://evil.com/reel/abc/', 'https://instagram.com.evil.com/reel/abc/',
                      'https://user@instagram.com/reel/abc/', 'https://instagram.com:443/reel/abc/',
                      'https://instagram.com/p/abc/', 'https://instagram.com/reel/a/b',
                      'file:///etc/passwd', '--exec=oops', 'https://[broken'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_url(value)

    def test_command(self):
        args = parser().parse_args(['--format', 'wav', '--cookies-from-browser', 'firefox', '-o', 'my audio'])
        command = build_command(args, 'https://www.instagram.com/reel/abc/')
        self.assertIn('--ignore-config', command)
        self.assertIn('--no-overwrites', command)
        self.assertEqual(command[command.index('--audio-format') + 1], 'wav')
        self.assertEqual(command[command.index('--cookies-from-browser') + 1], 'firefox')
        self.assertEqual(command[-2], '--')

    @patch('instagram_reels_audio.cli.importlib.util.find_spec', return_value=object())
    @patch('instagram_reels_audio.cli.shutil.which', return_value='/bin/tool')
    @patch('instagram_reels_audio.cli.subprocess.run')
    def test_batch_continues_and_deduplicates(self, run, *_):
        run.side_effect = [subprocess.CompletedProcess([], 1), subprocess.CompletedProcess([], 0)]
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory) / 'reels.txt'
            batch.write_text('# comment\n\nhttps://instagram.com/reel/abc/\nhttps://instagram.com/reel/abc/?igsh=1\nhttps://instagram.com/reel/def/\n')
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['-b', str(batch), '-o', directory]), 1)
        self.assertEqual(run.call_count, 2)

    @patch('instagram_reels_audio.cli.subprocess.run')
    def test_invalid_batch_downloads_nothing(self, run):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
            main(['https://instagram.com/reel/abc/', 'https://evil.com/reel/def/'])
        self.assertEqual(exc.exception.code, 2)
        run.assert_not_called()

    @patch('instagram_reels_audio.cli.importlib.util.find_spec', return_value=object())
    @patch('instagram_reels_audio.cli.shutil.which', return_value=None)
    def test_missing_ffmpeg(self, *_):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['https://instagram.com/reel/abc/']), 1)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_real_audio_extraction(self):
        from yt_dlp import YoutubeDL
        from yt_dlp.postprocessor.ffmpeg import FFmpegExtractAudioPP
        with tempfile.TemporaryDirectory() as directory:
            for codec in ('mp3', 'm4a', 'wav'):
                with self.subTest(codec=codec):
                    source = Path(directory) / (codec + '.mp4')
                    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                                    'color=c=black:s=32x32:d=0.3', '-f', 'lavfi', '-i',
                                    'sine=frequency=440:duration=0.3', '-c:v', 'mpeg4',
                                    '-c:a', 'aac', '-shortest', str(source)], check=True)
                    with YoutubeDL({'quiet': True}) as ydl:
                        processor = FFmpegExtractAudioPP(ydl, preferredcodec=codec, preferredquality='192')
                        _, info = processor.run({'filepath': str(source), 'ext': 'mp4', 'vcodec': 'mpeg4', 'acodec': 'aac'})
                    target = Path(info['filepath'])
                    self.assertEqual(target.suffix, '.' + codec)
                    self.assertGreater(target.stat().st_size, 100)
                    result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(target)], capture_output=True, text=True, check=True)
                    streams = json.loads(result.stdout)['streams']
                    self.assertEqual([s['codec_type'] for s in streams], ['audio'])


if __name__ == '__main__':
    unittest.main()
