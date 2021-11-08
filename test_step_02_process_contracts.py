# -*- coding: utf-8 -*-
from step_02_process_contracts import clean_float_value
from step_02_process_contracts import clean_float_value_old_xml
from step_02_process_contracts import clean_date_value

import unittest


class TestCleanFloatValue(unittest.TestCase):
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

    def test_crazy_comma_as_decimal_and_thousands(self):
        value = "4,321,45"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 4321.45)

    def test_million_with_decimals(self):
        value = "1.216.511,05"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 1216511.05)

    def test_with_one_decimal_number(self):
        value = "2.076,4"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 2076.4)

    def test_integer_no_thousands(self):
        value = "275"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 275.0)

    def test_integer_thousands_separator(self):
        value = "1.025"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 1025.0)

    def test_ten_euros(self):
        value = "10"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 10.0)

    def test_one_euro(self):
        value = "1"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 1.0)

    def test_one__and_decimal_euro_comma(self):
        value = "1,60"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 1.6)

    def test_one__and_decimal_euro_dot(self):
        value = "1.60"
        new_value = clean_float_value(value)
        self.assertEqual(new_value, 1.6)


class TestCleanFloatValueOldXML(unittest.TestCase):
    def test_million_with_decimals(self):
        value = "1.216.511,05"
        new_value = clean_float_value_old_xml(value)
        self.assertEqual(new_value, 1216511.05)

    def test_with_one_decimal_number(self):
        value = "2.076,4"
        new_value = clean_float_value_old_xml(value)
        self.assertEqual(new_value, 2076.4)

    def test_integer_no_thousands(self):
        value = "275"
        new_value = clean_float_value_old_xml(value)
        self.assertEqual(new_value, 275.0)

    def test_integer_thousands_separator(self):
        value = "1.025"
        new_value = clean_float_value_old_xml(value)
        self.assertEqual(new_value, 1025.0)


class TestCleanDateValue(unittest.TestCase):
    def test_es_date_with_slash_separator(self):
        value = "01/01/2017"
        new_value = clean_date_value(value)
        self.assertEqual(new_value, "2017-01-01")

    def test_eu_date_with_slash_separator(self):
        value = "2021/01/01"
        new_value = clean_date_value(value)
        self.assertEqual(new_value, "2021-01-01")

    def test_invalid_eu_date(self):
        """ Year can not be less than 1000"""
        value = "0099/01/25"
        new_value = clean_date_value(value)
        self.assertIsNone(new_value)

    def test_invalid_es_date(self):
        """ Year can not be less than 1000"""
        value = "25/01/0099"
        new_value = clean_date_value(value)
        self.assertIsNone(new_value)

    def test_empty_date(self):
        value = ""
        new_value = clean_date_value(value)
        self.assertIsNone(new_value)

    def test_giberish_date_is_none(self):
        value = "giberish"
        new_value = clean_date_value(value)
        self.assertIsNone(new_value)

    def test_none_date_is_none(self):
        value = None
        new_value = clean_date_value(value)
        self.assertIsNone(new_value)

    def test_with_date_time(self):
        value = "2020/11/17 09:40:38"
        new_value = clean_date_value(value)
        self.assertEqual(new_value, "2020-11-17")


if __name__ == "__main__":
    unittest.main()
