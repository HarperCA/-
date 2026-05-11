import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ResearchReportRoutesTest(unittest.TestCase):
    def test_report_page_has_landing_workflow_controls(self):
        import web_app

        client = web_app.app.test_client()
        with client.session_transaction() as session:
            session["username"] = "route_test_user"
            session["csrf_token"] = "token"

        response = client.get("/research_report")
        try:
            html = response.get_data(as_text=True)
        finally:
            response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn("投资复盘与风险报告", html)
        self.assertIn("没有数据，先生成示例报告", html)
        self.assertIn("下载 CSV 数据模板", html)
        self.assertIn("本次报告要解决什么问题", html)

    def test_template_download_returns_csv(self):
        import web_app

        client = web_app.app.test_client()
        response = client.get("/research_report/template.csv")
        try:
            body = response.get_data(as_text=True)
        finally:
            response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn("date,nav,return", body)


if __name__ == "__main__":
    unittest.main()
