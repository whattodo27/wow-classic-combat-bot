import sys
import unittest
from unittest.mock import patch

from combat_bot.capture import find_window_by_title


class FakeWindow:
    def __init__(self, title, left, top, width, height, minimized=False):
        self.title = title
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.isMinimized = minimized


class FakePygetwindow:
    def __init__(self, exact=(), all_windows=()):
        self._exact = list(exact)
        self._all = list(all_windows)

    def getWindowsWithTitle(self, title):  # noqa: N802
        return [window for window in self._exact if title in window.title]

    def getAllWindows(self):  # noqa: N802
        return list(self._all)


HIDDEN = (-32000, -32000, 160, 28)


def use_pygw(fake):
    return patch.dict(sys.modules, {"pygetwindow": fake})


class FindWindowTests(unittest.TestCase):
    def test_normal_window_is_returned(self):
        window = FakeWindow("World of Warcraft", 100, 200, 1040, 807)

        with use_pygw(FakePygetwindow(exact=[window])):
            rect = find_window_by_title("World of Warcraft")

        self.assertIsNotNone(rect)
        self.assertEqual((rect.left, rect.top), (100, 200))
        self.assertEqual((rect.width, rect.height), (1040, 807))

    def test_minimized_window_is_not_returned(self):
        window = FakeWindow("World of Warcraft", *HIDDEN, minimized=True)

        with use_pygw(FakePygetwindow(exact=[window])):
            rect = find_window_by_title("World of Warcraft")

        self.assertIsNone(rect)

    def test_tiny_hidden_rectangle_is_rejected(self):
        window = FakeWindow("World of Warcraft", *HIDDEN)

        with use_pygw(FakePygetwindow(exact=[window])):
            rect = find_window_by_title("World of Warcraft")

        self.assertIsNone(rect)

    def test_minimized_window_falls_through_to_visible_match(self):
        hidden = FakeWindow("World of Warcraft", *HIDDEN, minimized=True)
        visible = FakeWindow("World of Warcraft (2)", 10, 20, 800, 600)

        with use_pygw(FakePygetwindow(exact=[hidden], all_windows=[hidden, visible])):
            rect = find_window_by_title("World of Warcraft")

        self.assertIsNotNone(rect)
        self.assertEqual((rect.left, rect.top), (10, 20))

    def test_blank_title_returns_none(self):
        self.assertIsNone(find_window_by_title("   "))

    def test_no_match_returns_none(self):
        with use_pygw(FakePygetwindow()):
            self.assertIsNone(find_window_by_title("World of Warcraft"))


if __name__ == "__main__":
    unittest.main()
