import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch


def csrf_token(client, path: str = "/") -> str:
    response = client.get(path)
    try:
        html = response.get_data(as_text=True)
    finally:
        response.close()
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    if not match:
        raise AssertionError("csrf token not found")
    return match.group(1)


class WebSecurityTest(unittest.TestCase):
    def test_post_without_csrf_token_is_rejected(self):
        import web_app

        client = web_app.app.test_client()
        response = client.post("/register", data={"username": "alice", "password": "secret1", "password2": "secret1"})
        self.assertEqual(response.status_code, 400)

    def test_login_rate_limit_blocks_repeated_failures(self):
        import web_app

        with tempfile.TemporaryDirectory() as tmp:
            users_file = Path(tmp) / "users.json"
            users_file.write_text(
                json.dumps({"alice": {"password_hash": web_app._hash_password("correct-password")}}),
                encoding="utf-8",
            )

            with patch.object(web_app, "USERS_FILE", users_file):
                web_app.LOGIN_FAILURES.clear()
                client = web_app.app.test_client()
                token = csrf_token(client, "/login")

                for _ in range(web_app.LOGIN_FAILURE_LIMIT):
                    response = client.post(
                        "/login",
                        data={"username": "alice", "password": "wrong-password", "csrf_token": token},
                    )
                    self.assertEqual(response.status_code, 200)

                response = client.post(
                    "/login",
                    data={"username": "alice", "password": "correct-password", "csrf_token": token},
                    follow_redirects=False,
                )

                self.assertEqual(response.status_code, 200)
                self.assertIn("登录失败次数过多", response.get_data(as_text=True))

    def test_export_files_are_written_under_current_user_only(self):
        import web_app

        with tempfile.TemporaryDirectory() as tmp:
            userspace = Path(tmp) / "userspace"
            with (
                patch.object(web_app, "USERSPACE_DIR", userspace),
                patch.object(web_app, "LEGACY_HOLDINGS_FILE", Path(tmp) / "missing_holdings.json"),
                patch.object(web_app, "LEGACY_HISTORY_FILE", Path(tmp) / "missing_history.json"),
            ):
                client = web_app.app.test_client()
                with client.session_transaction() as sess:
                    sess["username"] = "alice"

                web_app.HoldingsManager(
                    filepath=str(userspace / "alice" / "holdings.json"),
                    username="alice",
                ).add("002982", market="fund", quantity=10, avg_cost=1.0)

                response = client.get("/export/holdings.csv")
                try:
                    self.assertEqual(response.status_code, 200)
                finally:
                    response.close()

                self.assertTrue(list((userspace / "alice" / "exports").glob("holdings_alice_*.csv")))
                self.assertFalse((userspace / "bob" / "exports").exists())

    def test_invalid_numeric_form_values_are_rejected_without_saving(self):
        import web_app

        with tempfile.TemporaryDirectory() as tmp:
            userspace = Path(tmp) / "userspace"
            with (
                patch.object(web_app, "USERSPACE_DIR", userspace),
                patch.object(web_app, "LEGACY_HOLDINGS_FILE", Path(tmp) / "missing_holdings.json"),
                patch.object(web_app, "LEGACY_HISTORY_FILE", Path(tmp) / "missing_history.json"),
            ):
                client = web_app.app.test_client()
                token = csrf_token(client, "/")
                with client.session_transaction() as sess:
                    sess["username"] = "alice"
                    sess["csrf_token"] = token

                response = client.post(
                    "/",
                    data={
                        "mode": "holding_add",
                        "holding_symbol": "002982",
                        "holding_market": "fund",
                        "holding_qty": "-1",
                        "holding_cost": "nan",
                        "csrf_token": token,
                    },
                )

                self.assertEqual(response.status_code, 200)
                self.assertIn("数量必须在", response.get_data(as_text=True))
                holdings_file = userspace / "alice" / "holdings.json"
                data = json.loads(holdings_file.read_text(encoding="utf-8")) if holdings_file.exists() else {}
                self.assertFalse(data.get("alice"))

    def test_share_pages_strip_unsafe_link_targets(self):
        import web_app

        client = web_app.app.test_client()
        csrf = "csrf-share-test"
        with client.session_transaction() as sess:
            sess["username"] = "alice"
            sess["csrf_token"] = csrf

        config_response = client.post(
            "/api/ui/report_config",
            json={"page": "//evil.example/phish", "title": "safe"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(config_response.status_code, 200)
        self.assertEqual(config_response.get_json()["config"]["page"], "")

        share_response = client.post(
            "/api/ui/share_link",
            json={"page": "javascript:alert(1)", "title": "safe"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(share_response.status_code, 200)
        payload = share_response.get_json()
        self.assertEqual(payload["snapshot"]["page"], "")

        shared_path = urlsplit(payload["share_url"]).path
        public_response = client.get(shared_path)
        self.assertEqual(public_response.status_code, 200)
        html = public_response.get_data(as_text=True).lower()
        self.assertNotIn("javascript:", html)
        self.assertNotIn("evil.example", html)

    def test_report_followup_rejects_oversized_or_bad_ids(self):
        import web_app

        client = web_app.app.test_client()
        csrf = "csrf-followup-test"
        with client.session_transaction() as sess:
            sess["username"] = "alice"
            sess["csrf_token"] = csrf

        too_long = client.post(
            "/api/report_followup",
            data={"question": "x" * 501, "csrf_token": csrf},
        )
        self.assertEqual(too_long.status_code, 400)

        bad_id = client.post(
            "/api/report_followup",
            data={"question": "解释风险", "report_id": "../bob/report", "csrf_token": csrf},
        )
        self.assertEqual(bad_id.status_code, 400)


if __name__ == "__main__":
    unittest.main()
