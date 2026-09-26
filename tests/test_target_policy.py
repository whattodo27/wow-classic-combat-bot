import unittest

from combat_bot.models import TargetInfo, TargetPolicyConfig
from combat_bot.target_policy import TargetPolicy


class TargetPolicyTests(unittest.TestCase):
    def test_empty_whitelist_rejects_every_target(self):
        policy = TargetPolicy(TargetPolicyConfig())

        decision = policy.check(TargetInfo(name="Kobold Vermin"))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "target_not_in_allowlist")

    def test_exact_allowlisted_target_is_allowed(self):
        policy = TargetPolicy(
            TargetPolicyConfig(allowed_names=("Kobold Vermin",))
        )

        decision = policy.check(TargetInfo(name="Kobold Vermin"))

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "allowlisted")

    def test_player_elite_and_rare_targets_are_always_rejected(self):
        policy = TargetPolicy(
            TargetPolicyConfig(allowed_names=("Kobold Vermin",))
        )

        cases = [
            TargetInfo(name="Kobold Vermin", is_player=True),
            TargetInfo(name="Kobold Vermin", is_elite=True),
            TargetInfo(name="Kobold Vermin", is_rare=True),
        ]

        for target in cases:
            with self.subTest(target=target):
                self.assertFalse(policy.check(target).allowed)

    def test_unknown_name_is_rejected(self):
        policy = TargetPolicy(
            TargetPolicyConfig(allowed_names=("Kobold Vermin",))
        )

        decision = policy.check(TargetInfo(name=None))

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "target_name_unknown")

    def test_young_nightsaber_can_be_enabled_by_allowlist(self):
        policy = TargetPolicy(
            TargetPolicyConfig(allowed_names=("Young Nightsaber",))
        )

        decision = policy.check(
            TargetInfo(name="Young Nightsaber", exists=True)
        )

        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
