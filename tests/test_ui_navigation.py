import unittest
from uuid import uuid4


class UINavConsistencyTest(unittest.TestCase):
    def test_dashboard_navigation_labels_match_targets(self):
        import web_app

        client = web_app.app.test_client()
        response = client.get("/")
        try:
            html = response.get_data(as_text=True)
        finally:
            response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn('href="/analysis"', html)
        self.assertIn(">分析台</a>", html)
        self.assertIn('href="/history"', html)
        self.assertIn(">经济历史</a>", html)
        self.assertIn('href="/alerts"', html)
        self.assertIn(">价格预警</a>", html)
        self.assertNotIn(">因子研究</a>", html)
        self.assertNotIn(">风险监控</a>", html)
        self.assertNotIn('href="#"', html)

    def test_workspace_rail_labels_match_destinations(self):
        import web_app

        client = web_app.app.test_client()
        response = client.get("/analysis")
        try:
            html = response.get_data(as_text=True)
        finally:
            response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn('href="/analysis"', html)
        self.assertIn(">分析台</a>", html)
        self.assertIn('href="/alerts"', html)
        self.assertIn(">价格预警</a>", html)
        self.assertIn('href="/analysis_history"', html)
        self.assertIn(">历史复盘</a>", html)
        self.assertNotIn(">预警</a>", html)
        self.assertNotIn(">历史</a>", html)

    def test_analysis_button_opens_analysis_workspace(self):
        import web_app

        client = web_app.app.test_client()
        response = client.get("/analysis")
        try:
            html = response.get_data(as_text=True)
        finally:
            response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn("自然语言 Agent", html)
        self.assertIn("结构化分析", html)
        self.assertIn("开始分析", html)

    def test_backtest_range_controls_submit_real_fields(self):
        import web_app

        client = web_app.app.test_client()
        response = client.get("/analysis")
        try:
            html = response.get_data(as_text=True)
        finally:
            response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="start_date" name="start_date" type="date"', html)
        self.assertIn('id="end_date" name="end_date" type="date"', html)
        self.assertIn('data-period="1y" data-years="1"', html)
        self.assertIn('data-period="3y" data-years="3"', html)
        self.assertIn('data-period="5y" data-years="5"', html)
        self.assertIn("startDateInput.value", html)
        self.assertIn("endDateInput.value", html)

    def test_module_buttons_open_matching_sections(self):
        import web_app

        client = web_app.app.test_client()
        checks = [
            ("/portfolio", "持仓管理"),
            ("/alerts", "价格预警"),
            ("/automation", "自动化"),
            ("/analysis_history", "历史记录"),
            ("/history", "ECONOMIC HISTORY"),
            ("/backtest_compare", "策略对比"),
        ]
        for path, expected in checks:
            with self.subTest(path=path):
                response = client.get(path)
                try:
                    html = response.get_data(as_text=True)
                finally:
                    response.close()
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected, html)

    def test_report_action_buttons_use_backend_apis(self):
        import web_app

        client = web_app.app.test_client()
        response = client.get("/analysis")
        try:
            html = response.get_data(as_text=True)
        finally:
            response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn("/api/ui/report_config", html)
        self.assertIn("/api/ui/share_link", html)
        self.assertIn("/api/ui/reader_version", html)
        self.assertIn("/api/ui/explain", html)
        self.assertIn("explainModal", html)
        self.assertIn("data-explain", html)
        self.assertIn('X-CSRF-Token', html)

    def test_ui_backend_actions_persist_and_share(self):
        import web_app

        client = web_app.app.test_client()
        username = f"ui_{uuid4().hex[:8]}"
        csrf = uuid4().hex
        with client.session_transaction() as session:
            session["username"] = username
            session["csrf_token"] = csrf

        save_response = client.post(
            "/api/ui/report_config",
            json={"title": "测试报告", "toggles": {"自动刷新数据": True}},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(save_response.status_code, 200)
        self.assertTrue(save_response.get_json()["ok"])

        reader_response = client.post(
            "/api/ui/reader_version",
            json={"version": "老板速读版"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(reader_response.status_code, 200)
        self.assertEqual(reader_response.get_json()["version"], "老板速读版")

        newbie_response = client.post(
            "/api/ui/reader_version",
            json={"version": "小白版本"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(newbie_response.status_code, 200)
        self.assertEqual(newbie_response.get_json()["version"], "小白版本")

        share_response = client.post(
            "/api/ui/share_link",
            json={"title": "测试报告"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(share_response.status_code, 200)
        share_url = share_response.get_json()["share_url"]
        self.assertIn("/share/", share_url)
        shared_path = "/" + share_url.split("/share/", 1)[1].join(["share/", ""])
        shared_response = client.get(shared_path)
        self.assertEqual(shared_response.status_code, 200)
        self.assertIn("测试报告", shared_response.get_data(as_text=True))

    def test_dashboard_returns_api_feeds_tabs(self):
        import web_app

        client = web_app.app.test_client()
        response = client.get("/api/ui/dashboard_returns?range=近一月")
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["range"], "近一月")
        self.assertIn("portfolio_path", data)

    def test_explain_metric_api(self):
        import web_app

        client = web_app.app.test_client()
        response = client.get("/api/ui/explain?name=夏普比率")
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["name"], "夏普比率")
        self.assertIn("单位风险", data["explanation"])


if __name__ == "__main__":
    unittest.main()
