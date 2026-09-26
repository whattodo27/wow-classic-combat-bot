import unittest

from combat_bot.executor import ActionExecutor
from combat_bot.models import Action


class FakeKeyboard:
    def __init__(self):
        self.pressed = []
        self.down = []
        self.up = []

    def press(self, key, presses=1, interval=0.05):
        self.pressed.append(key)

    def keyDown(self, key):  # noqa: N802 - mirrors pyautogui API
        self.down.append(key)

    def keyUp(self, key):  # noqa: N802 - mirrors pyautogui API
        self.up.append(key)

    @property
    def PAUSE(self):
        return getattr(self, "_pause", 0.1)

    @PAUSE.setter
    def PAUSE(self, value):
        self._pause = value

    @property
    def FAILSAFE(self):
        return getattr(self, "_failsafe", False)

    @FAILSAFE.setter
    def FAILSAFE(self, value):
        self._failsafe = value


class ExecutorTargetingTests(unittest.TestCase):
    def test_live_targeting_presses_tab_but_keeps_attacks_in_dry_run(self):
        keyboard = FakeKeyboard()
        focus = []
        executor = ActionExecutor(
            live_input=False,
            live_targeting=True,
            target_key="tab",
            keyboard=keyboard,
            focus_callback=lambda: focus.append("focused"),
        )

        target_result = executor.execute(Action.press("tab", "no_target"))
        attack_result = executor.execute(Action.press("1", "opening_attack"))

        self.assertIn("LIVE TARGET", target_result)
        self.assertIn("DRY-RUN", attack_result)
        self.assertEqual(focus, ["focused"])
        self.assertEqual(keyboard.pressed, ["tab"])

    def test_full_dry_run_never_touches_keyboard(self):
        keyboard = FakeKeyboard()
        focus = []
        executor = ActionExecutor(
            live_input=False,
            live_targeting=False,
            target_key="tab",
            keyboard=keyboard,
            focus_callback=lambda: focus.append("focused"),
        )

        result = executor.execute(Action.press("tab", "no_target"))

        self.assertIn("DRY-RUN", result)
        self.assertEqual(focus, [])
        self.assertEqual(keyboard.pressed, [])

    def test_live_targeting_holds_sweep_keys(self):
        keyboard = FakeKeyboard()
        executor = ActionExecutor(
            live_input=False,
            live_targeting=True,
            target_key="tab",
            keyboard=keyboard,
        )

        result = executor.execute(
            Action.hold(("w", "d"), "sweep_spawn_area", hold_seconds=0.5)
        )

        self.assertIn("LIVE SWEEP", result)
        self.assertEqual(keyboard.down, ["w", "d"])
        self.assertEqual(keyboard.up, ["d", "w"])

    def test_sweep_is_dry_run_without_live_targeting(self):
        keyboard = FakeKeyboard()
        executor = ActionExecutor(
            live_input=False,
            live_targeting=False,
            target_key="tab",
            keyboard=keyboard,
        )

        result = executor.execute(
            Action.hold(("w", "d"), "sweep_spawn_area", hold_seconds=0.5)
        )

        self.assertIn("DRY-RUN", result)
        self.assertEqual(keyboard.down, [])
        self.assertEqual(keyboard.up, [])

    def test_hold_releases_keys_when_a_key_down_fails(self):
        class FailingKeyboard(FakeKeyboard):
            def keyDown(self, key):  # noqa: N802
                if key == "d":
                    raise RuntimeError("game rejected key")
                super().keyDown(key)

        keyboard = FailingKeyboard()
        executor = ActionExecutor(
            live_input=False,
            live_targeting=True,
            target_key="tab",
            keyboard=keyboard,
        )

        with self.assertRaises(RuntimeError):
            executor.execute(
                Action.hold(("w", "d"), "sweep_spawn_area", hold_seconds=0.5)
            )

        self.assertEqual(keyboard.up, ["w"])

    def test_live_input_sends_attack_keys(self):
        keyboard = FakeKeyboard()
        executor = ActionExecutor(
            live_input=True,
            target_key="tab",
            keyboard=keyboard,
        )

        result = executor.execute(Action.press("1", "opening_attack"))

        self.assertIn("LIVE", result)
        self.assertEqual(keyboard.pressed, ["1"])


if __name__ == "__main__":
    unittest.main()
