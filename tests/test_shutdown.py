import tempfile
import unittest
from pathlib import Path
from unittest import mock

from combat_bot import shutdown


class ReleaseAllKeysTests(unittest.TestCase):
    def test_releases_every_movement_key(self):
        fake = mock.MagicMock()
        with mock.patch.dict("sys.modules", {"pyautogui": fake}):
            shutdown.release_all_keys()

        released = [call.args[0] for call in fake.keyUp.call_args_list]
        self.assertEqual(released, ["w", "a", "s", "d"])

    def test_one_failing_key_does_not_stop_the_rest(self):
        fake = mock.MagicMock()
        fake.keyUp.side_effect = [Exception("boom"), None, None, None]
        with mock.patch.dict("sys.modules", {"pyautogui": fake}):
            shutdown.release_all_keys()

        self.assertEqual(fake.keyUp.call_count, 4)

    def test_missing_pyautogui_is_not_fatal(self):
        with mock.patch.dict("sys.modules", {"pyautogui": None}):
            shutdown.release_all_keys()


class InstallStopHandlersTests(unittest.TestCase):
    def register(self, **kwargs):
        import signal

        with mock.patch.object(signal, "signal") as fake:
            shutdown.install_stop_handlers(**kwargs)
        registered = {call.args[0]: call.args[1] for call in fake.call_args_list}
        return registered[signal.SIGINT]

    def test_registers_sigint_and_sigterm(self):
        import signal

        with mock.patch.object(signal, "signal") as fake:
            shutdown.install_stop_handlers()

        registered = {call.args[0] for call in fake.call_args_list}
        self.assertIn(signal.SIGINT, registered)
        self.assertIn(signal.SIGTERM, registered)

    def test_handler_releases_keys_and_raises(self):
        handler = self.register()

        with mock.patch.object(shutdown, "release_all_keys") as fake:
            with self.assertRaises(KeyboardInterrupt):
                handler(2, None)

        fake.assert_called_once()

    def test_handler_calls_the_stop_callback(self):
        calls = []
        handler = self.register(on_stop=lambda: calls.append(True))

        with mock.patch.object(shutdown, "release_all_keys"):
            with self.assertRaises(KeyboardInterrupt):
                handler(2, None)

        self.assertEqual(calls, [True])

    def test_registers_windows_console_handler(self):
        with mock.patch.object(shutdown, "_install_windows_console_handler") as fake:
            shutdown.install_stop_handlers()

        fake.assert_called_once()


class StopFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_no_stop_file_initially(self):
        self.assertFalse(shutdown.stop_requested(self.root))

    def test_request_stop_creates_the_file(self):
        path = shutdown.request_stop(self.root)

        self.assertTrue(path.exists())
        self.assertTrue(shutdown.stop_requested(self.root))

    def test_clear_stop_file_removes_it(self):
        shutdown.request_stop(self.root)

        shutdown.clear_stop_file(self.root)

        self.assertFalse(shutdown.stop_requested(self.root))

    def test_clearing_a_missing_file_is_fine(self):
        shutdown.clear_stop_file(self.root)

    def test_stop_file_lives_next_to_main(self):
        self.assertEqual(shutdown.stop_file_path().name, "bot.stop")
        self.assertTrue(
            str(shutdown.stop_file_path()).endswith("bot.stop"),
        )


class PanicKeyTests(unittest.TestCase):
    def test_reports_the_key_as_pressed(self):
        with mock.patch.object(shutdown, "_keyboard_state", return_value=lambda vk: 0x8001):
            self.assertTrue(shutdown.panic_key_pressed())

    def test_reports_the_key_as_released(self):
        with mock.patch.object(shutdown, "_keyboard_state", return_value=lambda vk: 0x0001):
            self.assertFalse(shutdown.panic_key_pressed())

    def test_broken_keyboard_api_is_not_fatal(self):
        def boom():
            raise OSError("no keyboard")

        with mock.patch.object(shutdown, "_keyboard_state", return_value=boom):
            self.assertFalse(shutdown.panic_key_pressed())


if __name__ == "__main__":
    unittest.main()
