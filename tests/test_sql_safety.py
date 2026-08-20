import unittest

from app.sql_safety import validate_sql


class SQLSafetyTests(unittest.TestCase):
    def test_select_star_is_rejected(self) -> None:
        result = validate_sql("SELECT * FROM orders")

        self.assertFalse(result.ok)

    def test_unknown_table_is_rejected(self) -> None:
        result = validate_sql("SELECT id FROM payroll")

        self.assertFalse(result.ok)

    def test_limit_is_added(self) -> None:
        result = validate_sql("SELECT order_id FROM orders")

        self.assertTrue(result.ok)
        self.assertIsNotNone(result.sql)
        self.assertIn("LIMIT", result.sql.upper())


if __name__ == "__main__":
    unittest.main()
