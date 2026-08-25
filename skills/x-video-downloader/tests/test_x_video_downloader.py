import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "x_video_downloader.py"
SPEC = importlib.util.spec_from_file_location("x_video_downloader", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ParsePostUrlTests(unittest.TestCase):
    def test_accepts_x_and_twitter_status_urls(self):
        self.assertEqual(
            MODULE.parse_post_url("https://x.com/NousResearch/status/2089429432612147572"),
            ("NousResearch", "2089429432612147572"),
        )
        self.assertEqual(
            MODULE.parse_post_url("https://twitter.com/example/status/12345?s=20"),
            ("example", "12345"),
        )

    def test_rejects_non_status_url(self):
        with self.assertRaisesRegex(ValueError, "X post URL"):
            MODULE.parse_post_url("https://x.com/NousResearch")


class ExtractVideoTests(unittest.TestCase):
    def test_selects_highest_resolution_for_each_video(self):
        html = """
        https://video.twimg.com/amplify_video/111/vid/avc1/640x360/low.mp4?tag=1&amp;x=2
        https://video.twimg.com/amplify_video/111/vid/avc1/1920x1080/high.mp4?tag=1&amp;x=2
        https://video.twimg.com/ext_tw_video/222/pu/vid/avc1/1280x720/second.mp4?tag=1
        """

        videos = MODULE.extract_best_video_urls(html)

        self.assertEqual(len(videos), 2)
        self.assertEqual(videos[0].width, 1920)
        self.assertEqual(videos[0].height, 1080)
        self.assertIn("&x=2", videos[0].url)
        self.assertEqual(videos[1].media_id, "222")


class DestinationTests(unittest.TestCase):
    def test_builds_safe_destination_and_numbers_multiple_videos(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            first = MODULE.build_destination(
                output_dir, "Nous/Research", "123", 3842, 2160, 1, 2
            )
            second = MODULE.build_destination(
                output_dir, "Nous/Research", "123", 1280, 720, 2, 2
            )

        self.assertEqual(first.name, "Nous_Research_123_3842x2160_1.mp4")
        self.assertEqual(second.name, "Nous_Research_123_1280x720_2.mp4")


if __name__ == "__main__":
    unittest.main()
