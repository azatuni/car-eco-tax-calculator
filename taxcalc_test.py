import unittest
import datetime
from taxcalc import CarEcoTax


class CatEcoTaxTest(unittest.TestCase):

    def test_two_digit_production_year(self):
        testcase = CarEcoTax(20, 100).production_year
        expected = 2020
        self.assertEqual(testcase, expected, f"Production year for 2 digit should be {expected}")

    def test_one_digit_production_year(self):
        testcase = CarEcoTax(1, 100).production_year
        expected = 2001
        self.assertEqual(testcase, expected, f"Production year for 1 digit should be {expected}")

    def test_50_hours_power_3_year_car_tax(self):
        three_years_before = datetime.datetime.today().year - 3
        horse_powers = 50
        testcase = CarEcoTax(three_years_before, horse_powers).calculate()
        expected = 125
        self.assertEqual(testcase, expected, f"Eco tax for {three_years_before} "
                                             f"and {horse_powers} horsepower's should be {expected}")

    def test_100_hours_power_10_year_car_tax(self):
        ten_years_before = datetime.datetime.today().year - 10
        horse_powers = 100
        testcase = CarEcoTax(ten_years_before, horse_powers).calculate()
        expected = 1500
        self.assertEqual(testcase, expected, f"Eco tax for {ten_years_before} "
                                             f"and {horse_powers} horsepower's should be {expected}")

    def test_251_hours_power_6_year_car_tax(self):
        six_years_before = datetime.datetime.today().year - 6
        horse_powers = 251
        testcase = CarEcoTax(six_years_before, horse_powers).calculate()
        expected = 7028
        self.assertEqual(testcase, expected, f"Eco tax for {six_years_before} "
                                             f"and {horse_powers} horsepower's should be {expected}")

    def test_350_hours_power_2_year_car_tax(self):
        two_years_before = datetime.datetime.today().year - 2
        horse_powers = 350
        testcase = CarEcoTax(two_years_before, horse_powers).calculate()
        expected = 8750
        self.assertEqual(testcase, expected, f"Eco tax for {two_years_before} "
                                             f"and {horse_powers} horsepower's should be {expected}")



if __name__ == '__main__':
    unittest.main()
