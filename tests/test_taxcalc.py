import unittest
import datetime
import sys
sys.path.append('..')
from taxcalc import CarEcoTax
from taxcalc import CarEcoTaxProdYearError
from taxcalc import CarEcoTaxHorsePowerError


class CatEcoTaxTest(unittest.TestCase):

    def test_two_digit_production_year(self):
        testcase = CarEcoTax(20, 100).production_year
        expected = 2020
        error_message = f"Production year for 2 digit should be {expected}"
        self.assertEqual(testcase, expected, error_message)

    def test_one_digit_production_year(self):
        testcase = CarEcoTax(1, 100).production_year
        expected = 2001
        error_message = f"Production year for 1 digit should be {expected}"
        self.assertEqual(testcase, expected, error_message)

    def test_50_hours_power_3_year_car_tax(self):
        three_years_before = datetime.datetime.today().year - 3
        horse_powers = 50
        testcase = CarEcoTax(three_years_before, horse_powers).calculate()
        expected = 125
        error_message = f"Eco tax for {three_years_before} and " \
                        f"{horse_powers} horsepower's should be {expected}"
        self.assertEqual(testcase, expected, error_message)

    def test_100_hours_power_10_year_car_tax(self):
        ten_years_before = datetime.datetime.today().year - 10
        horse_powers = 100
        testcase = CarEcoTax(ten_years_before, horse_powers).calculate()
        expected = 1500
        error_message = f"Eco tax for {ten_years_before} and " \
                        f"{horse_powers} horsepower's should be {expected}"
        self.assertEqual(testcase, expected, error_message)

    def test_251_hours_power_6_year_car_tax(self):
        six_years_before = datetime.datetime.today().year - 6
        horse_powers = 251
        testcase = CarEcoTax(six_years_before, horse_powers).calculate()
        expected = 7028
        error_message = f"Eco tax for {six_years_before} and {horse_powers} " \
                        f"horsepower's should be {expected}"
        self.assertEqual(testcase, expected, error_message)

    def test_350_hours_power_2_year_car_tax(self):
        two_years_before = datetime.datetime.today().year - 2
        horse_powers = 350
        testcase = CarEcoTax(two_years_before, horse_powers).calculate()
        expected = 8750
        error_message = f"Eco tax for {two_years_before} " \
                        f"and {horse_powers} horsepower's should be {expected}"
        self.assertEqual(testcase, expected, error_message)

    def test_next_year_input_exception(self):
        one_year_after = datetime.datetime.today().year + 2
        horse_powers = 350
        error_message = f"Prod year is {one_year_after}"
        with self.assertRaises(CarEcoTaxProdYearError, msg=error_message):
            CarEcoTax(one_year_after, horse_powers).calculate()

    def test_three_letters_year_input_exception(self):
        one_year_after = 198
        horse_powers = 350
        error_message = "Prod year could not be 3 digits"
        with self.assertRaises(CarEcoTaxProdYearError, msg=error_message):
            CarEcoTax(one_year_after, horse_powers).calculate()

    def test_year_not_int_input(self):
        prod_year = "random_string"
        horse_powers = 350
        error_message = "Prod year should be integer"
        with self.assertRaises(CarEcoTaxProdYearError, msg=error_message):
            CarEcoTax(prod_year, horse_powers).calculate()

    def test_horse_power_not_int_input(self):
        prod_year = 1980
        horse_powers = "random_string"
        error_message = "Horse powers should be integer"
        with self.assertRaises(CarEcoTaxHorsePowerError, msg=error_message):
            CarEcoTax(prod_year, horse_powers).calculate()

    def test_horse_power_not_zero(self):
        prod_year = 1980
        horse_powers = 0
        error_message = "Horse powers should be greater then 0"
        with self.assertRaises(CarEcoTaxHorsePowerError, msg=error_message):
            CarEcoTax(prod_year, horse_powers).calculate()

    def test_horse_power_not_negative(self):
        prod_year = 1980
        horse_powers = -1
        error_message = "Horse powers should be greater then 0"
        with self.assertRaises(CarEcoTaxHorsePowerError, msg=error_message):
            CarEcoTax(prod_year, horse_powers).calculate()

    def test_year_not_zero(self):
        prod_year = 0
        horse_powers = 300
        error_message = "Prod year should be greater then 0"
        with self.assertRaises(CarEcoTaxProdYearError, msg=error_message):
            CarEcoTax(prod_year, horse_powers).calculate()

    def test_year_not_negative(self):
        prod_year = -1
        horse_powers = 300
        error_message = "Prod year should be greater then 0"
        with self.assertRaises(CarEcoTaxProdYearError, msg=error_message):
            CarEcoTax(prod_year, horse_powers).calculate()


if __name__ == '__main__':
    unittest.main()
