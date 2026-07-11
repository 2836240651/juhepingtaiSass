import unittest

from app.browser.session_state import build_session_payload, session_ready


class SessionStateTests(unittest.TestCase):
    def test_session_ready_when_mall_id_present(self):
        self.assertTrue(session_ready({"mall_id": "mall-1", "requires_auth": False}))

    def test_session_ready_false_on_auth_without_malls(self):
        self.assertFalse(session_ready({"requires_auth": True, "logged_in": False, "mall_count": 0}))

    def test_build_payload_marks_profile_busy(self):
        payload = build_session_payload(
            5,
            {"requires_auth": True, "logged_in": False, "mall_count": 0},
            profile_busy=True,
        )
        self.assertTrue(payload["profile_busy"])
        self.assertFalse(payload["ready"])


if __name__ == "__main__":
    unittest.main()
