import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.holdings_manager import HoldingsManager


class HoldingsIsolationTest(unittest.TestCase):
    def test_holdings_are_separated_and_tagged_by_username(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "holdings.json"

            alice = HoldingsManager(filepath=str(path), username="alice")
            bob = HoldingsManager(filepath=str(path), username="bob")

            alice.add("002982", market="fund", quantity=100, avg_cost=0.86)
            bob.add("017811", market="fund", quantity=200, avg_cost=1.12)

            alice = HoldingsManager(filepath=str(path), username="alice")
            bob = HoldingsManager(filepath=str(path), username="bob")

            self.assertEqual([h.symbol for h in alice.list_all()], ["002982"])
            self.assertEqual([h.symbol for h in bob.list_all()], ["017811"])
            self.assertEqual(alice.list_all()[0].username, "alice")
            self.assertEqual(bob.list_all()[0].username, "bob")

            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw["alice"][0]["username"], "alice")
            self.assertEqual(raw["bob"][0]["username"], "bob")


class WebUserDataTest(unittest.TestCase):
    def test_history_and_alert_rows_include_current_username(self):
        import web_app

        with tempfile.TemporaryDirectory() as tmp:
            userspace = Path(tmp) / "userspace"
            with patch.object(web_app, "USERSPACE_DIR", userspace):
                web_app._write_history_item(
                    {"symbol": "002982", "market": "fund", "period": "1y", "use_ai": False},
                    username="alice",
                )
                web_app._write_alerts(
                    [{"id": "a1", "symbol": "002982", "market": "fund", "target_price": 0.8}],
                    username="alice",
                )

                history = json.loads((userspace / "alice" / "analysis_history.json").read_text(encoding="utf-8"))
                alerts = json.loads((userspace / "alice" / "alerts.json").read_text(encoding="utf-8"))

                self.assertEqual(history[0]["username"], "alice")
                self.assertEqual(alerts[0]["username"], "alice")

    def test_report_files_are_scoped_to_current_user(self):
        import web_app

        with tempfile.TemporaryDirectory() as tmp:
            reports_dir = Path(tmp) / "reports"
            reports_dir.mkdir()
            (reports_dir / "alice_002982_fund_1y_20260505_analysis.png").write_bytes(b"alice")
            (reports_dir / "bob_002982_fund_1y_20260505_analysis.png").write_bytes(b"bob")
            (reports_dir / "guest_002982_fund_1y_20260505_analysis.png").write_bytes(b"guest")

            with patch.object(web_app, "REPORTS_DIR", reports_dir):
                client = web_app.app.test_client()

                def status(path: str) -> int:
                    response = client.get(path)
                    try:
                        return response.status_code
                    finally:
                        response.close()

                self.assertEqual(status("/reports/guest_002982_fund_1y_20260505_analysis.png"), 200)
                self.assertEqual(status("/reports/alice_002982_fund_1y_20260505_analysis.png"), 404)

                with client.session_transaction() as sess:
                    sess["username"] = "alice"

                self.assertEqual(status("/reports/alice_002982_fund_1y_20260505_analysis.png"), 200)
                self.assertEqual(status("/reports/bob_002982_fund_1y_20260505_analysis.png"), 404)

    def test_register_rejects_usernames_that_do_not_map_safely(self):
        import web_app

        with tempfile.TemporaryDirectory() as tmp:
            users_file = Path(tmp) / "users.json"
            userspace = Path(tmp) / "userspace"

            with (
                patch.object(web_app, "USERS_FILE", users_file),
                patch.object(web_app, "USERSPACE_DIR", userspace),
            ):
                client = web_app.app.test_client()
                token = self._csrf_token(client, "/register")
                response = client.post(
                    "/register",
                    data={"username": "alice/../bob", "password": "secret1", "password2": "secret1", "csrf_token": token},
                )

                self.assertEqual(response.status_code, 200)
                self.assertFalse(users_file.exists())

    @staticmethod
    def _csrf_token(client, path: str = "/") -> str:
        import re

        response = client.get(path)
        try:
            html = response.get_data(as_text=True)
        finally:
            response.close()
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        if not match:
            raise AssertionError("csrf token not found")
        return match.group(1)


if __name__ == "__main__":
    unittest.main()
