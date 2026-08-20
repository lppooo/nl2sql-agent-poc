import unittest

from app.agent import NL2SQLAgent
from app.bootstrap import build_sample_database


class AgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        build_sample_database()

    def test_gmv_by_channel_query_runs(self) -> None:
        response = NL2SQLAgent().run("上个月各渠道GMV是多少？", include_trace=False)

        self.assertTrue(response.safety_passed)
        self.assertIsNotNone(response.sql)
        self.assertIn("JOIN channels", response.sql)
        self.assertGreater(len(response.rows), 0)

    def test_dangerous_sql_is_blocked(self) -> None:
        response = NL2SQLAgent().run("drop table orders;", include_trace=False)

        self.assertFalse(response.safety_passed)
        self.assertIsNone(response.sql)
        self.assertEqual(response.rows, [])


if __name__ == "__main__":
    unittest.main()
