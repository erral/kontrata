# -*- coding: utf-8 -*-
from step_02_process_contracts import clean_float_value

import unittest


class TestProcessContracts(unittest.TestCase):
    def test_dot_as_decimal(self):
        value = "202.49"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 202.49)

    def test_dots_and_no_decimals(self):
        value = "1.555.092"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 1555092.0)

    def test_comma_as_decimal_dot_as_thousands(self):
        value = "6.824,37"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 6824.37)

    def test_integer_value(self):
        value = "306"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 306)

    def test_integer_no_thousand_separator(self):
        value = "3844443"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 3844443.0)

    def test_comma_as_decimal_one_decimal(self):
        value = "10.030,9"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 10030.9)

    def test_crazy_dot_as_decimal_and_thousands(self):
        value = "4.268.35"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 4268.35)


if __name__ == "__main__":
    unittest.main()
