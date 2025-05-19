import unittest
import os
import json
from unittest.mock import patch, mock_open
from Media_Player import MediaItem, MediaList, parse_time_string


class TestParseTimeString(unittest.TestCase):
    def test_seconds_only(self):
        self.assertEqual(parse_time_string("15"), 15)

    def test_minutes_and_seconds(self):
        self.assertEqual(parse_time_string("1:30"), 90)

    def test_hours_minutes_seconds(self):
        self.assertEqual(parse_time_string("1:15:01"), 4501)

    def test_invalid_string_raises(self):
        with self.assertRaises(ValueError):
            parse_time_string("abc")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_time_string("")

    def test_almost_empty_string(self):
        with self.assertRaises(ValueError):
            parse_time_string(" ")


class TestParseTimeStringNoColons(unittest.TestCase):
    def test_seconds_only(self):
        self.assertEqual(parse_time_string(" 15s"), 15)

    def test_minutes_and_seconds(self):
        self.assertEqual(parse_time_string("1m30s"), 90)

    def test_hours_minutes_seconds(self):
        self.assertEqual(parse_time_string("1h15m01s"), 4501)

    def test_seconds_spaces(self):
        self.assertEqual(parse_time_string(" 123s "), 123)

    def test_minutes_and_seconds_spaces(self):
        with self.assertRaises(ValueError):
            parse_time_string(" 5m  3s ")  # spaces in middle confuse things

    def test_hours_minutes_and_seconds_spaces(self):
        with self.assertRaises(ValueError):
            parse_time_string(" 1h 5m  3s ")  # spaces in middle confuse things

    def test_invalid_string_raises(self):
        with self.assertRaises(ValueError):
            parse_time_string("ms")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_time_string("")

    def test_almost_empty_string(self):
        with self.assertRaises(ValueError):
            parse_time_string(" ")


class TestMediaItem(unittest.TestCase):
    def test_detect_image_type(self):
        item = MediaItem("example.jpg", "An image")
        self.assertEqual(item.type, "image")

    def test_detect_video_type(self):
        item = MediaItem("video.mp4", "A video")
        self.assertEqual(item.type, "video")

    def test_unsupported_type(self):
        item = MediaItem("document.pdf", "A document")
        self.assertIsNone(item.type)


class TestMediaList(unittest.TestCase):
    @patch("os.path.exists", return_value=True)
    def test_load_valid_media(self, mock_exists):
        sample_json = json.dumps(
            [
                {"filepath": "image.jpg", "caption": "Image"},
                {"filepath": "video.mp4", "caption": "Video"},
            ]
        )
        with patch("builtins.open", mock_open(read_data=sample_json)):
            media_list = MediaList()
            warnings = media_list.load_from_json("fake.json")
            self.assertEqual(len(media_list.items), 2)
            self.assertEqual(warnings, [])

    @patch("os.path.exists", return_value=False)
    def test_load_missing_file(self, mock_exists):
        sample_json = json.dumps([{"filepath": "missing.jpg", "caption": "Missing"}])
        with patch("builtins.open", mock_open(read_data=sample_json)):
            media_list = MediaList()
            warnings = media_list.load_from_json("fake.json")
            self.assertEqual(len(media_list.items), 0)
            self.assertIn("File not found", warnings[0])

    @patch("os.path.exists", return_value=True)
    def test_load_unsupported_file(self, mock_exists):
        sample_json = json.dumps([{"filepath": "file.txt", "caption": "Text"}])
        with patch("builtins.open", mock_open(read_data=sample_json)):
            media_list = MediaList()
            warnings = media_list.load_from_json("fake.json")
            self.assertEqual(len(media_list.items), 0)
            self.assertIn("Unsupported file type", warnings[0])


if __name__ == "__main__":
    unittest.main()
