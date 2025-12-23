import os
import asyncio
import re
from typing import Tuple

import yt_dlp


TIKTOK_PATTERN = r"(https?://(?:www\.)?tiktok\.com/[^\s]+)"
YOUTUBE_PATTERN = r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[^\s]+)"
REELS_PATTERN = r"(https?://(?:www\.)?instagram\.com/(?:reel|reels)/[^\s]+)"


class VideoDownloader:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_ydl_opts(self, platform: str):
        return {
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "format": "mp4/bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "ignoreerrors": False,
            "postprocessors": [
                {
                    "key": "FFmpegVideoRemuxer",
                    "preferedformat": "mp4",
                }
            ],
        }

    def _download_sync(self, url: str, platform: str) -> Tuple[str, str]:
        try:
            with yt_dlp.YoutubeDL(self.get_ydl_opts(platform)) as ydl:
                info = ydl.extract_info(url, download=True)

                filename = ydl.prepare_filename(info)

                if not os.path.exists(filename):
                    base_name = os.path.splitext(filename)[0]
                    possible_mp4 = base_name + ".mp4"
                    if os.path.exists(possible_mp4):
                        filename = possible_mp4

                title = info.get("title", "Video")
                return filename, title
        except Exception as e:
            raise Exception(f"Ошибка скачивания: {str(e)}")

    async def download_video(self, url: str, platform: str) -> Tuple[str, str]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_sync, url, platform)

    @staticmethod
    def detect_platform(url: str) -> str | None:
        if re.search(TIKTOK_PATTERN, url):
            return "TikTok"
        if re.search(YOUTUBE_PATTERN, url):
            return "YouTube"
        if re.search(REELS_PATTERN, url):
            return "Reels"
        return None

    def cleanup(self, filepath: str):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            base = os.path.splitext(filepath)[0]
            for ext in [".mp4", ".webm", ".mkv", ".m4a", ".part", ".fmp4"]:
                temp_file = base + ext
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        except Exception:
            pass


downloader = VideoDownloader(
    output_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "video_files")
)





