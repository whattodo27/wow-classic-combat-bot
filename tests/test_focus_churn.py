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

    def keyDown(self, key):  # noqa: N802
        self.down.append(key)

    def keyUp(self, key):  # noqa: N802
        self.up.append(key)

    @property
    def PAUSE(self):
        return 0.1

    @PAUSE.setter
    def PAUSE(self, value):
        pass

    @property
    def FAILSAFE(self):
        return True

    @FAILSAFE.setter
    def FAILSAFE(self, value):
        pass


class FocusChurnTests(unittest.TestCase):
    def make(self):
        self.focus = []
        self.keyboard = FakeKeyboard()
        return ActionExecutor(
            live_input=True,
            live_targeting=True,
            target_key="tab",
            keyboard=self.keyboard,
            focus_callback=lambda: self.focus.append(1),
        )

    def test_focus_is_not_called_for_every_key(self):
        executor = self.make()

        for _ in range(6):
            executor.execute(Action.press("1", "opening_attack"))

        self.assertEqual(len(self.focus), 1)
        self.assertEqual(len(self.keyboard.pressed), 6)

    def test_focus_is_called_once_for_a_sweep(self):
        executor = self.make()

        executor.execute(Action.hold(("w", "d"), "sweep", hold_seconds=0.0))
        executor.execute(Action.hold(("w", "d"), "sweep", hold_seconds=0.0))

        self.assertEqual(len(self.focus), 1)

    def test_focus_can_be_forced_after_a_manual_focus_loss(self):
        executor = self.make()
        executor.execute(Action.press("tab", "no_target"))
        executor.focus_now()

        self.assertEqual(len(self.focus), 2)

    def test_keys_still_send_without_refocusing(self):
        executor = self.make()
        executor.execute(Action.press("2", "attack"))

        self.assertEqual(self.keyboard.pressed, ["2"])


if __name__ == "__main__":
    unittest.main()
