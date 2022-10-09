import datetime
import argparse


class CarEcoTax:
    tax_per_horse_power = {
        "from_0_to_50": {
            "for_three_years": 2.5,
            "per_additional_year": 0.5
        },
        "from_51_to_80": {
            "for_three_years": 5,
            "per_additional_year": 1
        },
        "from_81_to_100": {
            "for_three_years": 7.5,
            "per_additional_year": 1.5
        },
        "from_101_to_150": {
            "for_three_years": 10,
            "per_additional_year": 2
        },
        "from_151_to_200": {
            "for_three_years": 12.5,
            "per_additional_year": 2.5
        },
        "from_201_to_250": {
            "for_three_years": 15,
            "per_additional_year": 3
        },
        "from_251_to_300": {
            "for_three_years": 17.5,
            "per_additional_year": 3.5
        },
        "more_then_300": {
            "for_three_years": 25,
            "per_additional_year": 5
        }

    }

    def __init__(self, production_year, horse_powers, debug=False):
        # Allow use tow digit numbers if car is newer than 2000 year
        if len(str(production_year)) <= 2:
            self.production_year = production_year + 2000
        else:
            self.production_year = production_year
        current_year = datetime.datetime.today().year
        age = current_year - self.production_year
        # Calculate car tax age
        if age > 8:
            self.car_tax_age = 8
        elif age == 0:
            self.car_tax_age = 1
        # from 1 to 3 years tax calculation is the same
        elif age in range(1, 4):
            self.car_tax_age = 3
        else:
            self.car_tax_age = age
        self.horse_powers = horse_powers
        self.debug = debug
        if debug:
            print(f"Car tax age: {self.car_tax_age}")

    def __str__(self):
        return f"Car horsepowers are: {self.horse_powers}, tax age: {self.car_tax_age}"

    def __calc_parser(self, data):
        return self.horse_powers * (data["for_three_years"] +
                                    ((self.car_tax_age - 3) * (data["per_additional_year"])))

    def calculate(self):
        if self.horse_powers in range(0, 51):
            return self.__calc_parser(self.tax_per_horse_power["from_0_to_50"])
        elif self.horse_powers in range(51, 81):
            return self.__calc_parser(self.tax_per_horse_power["from_51_to_80"])
        elif self.horse_powers in range(81, 101):
            return self.__calc_parser(self.tax_per_horse_power["from_81_to_100"])
        elif self.horse_powers in range(101, 151):
            return self.__calc_parser(self.tax_per_horse_power["from_101_to_150"])
        elif self.horse_powers in range(151, 201):
            return self.__calc_parser(self.tax_per_horse_power["from_151_to_200"])
        elif self.horse_powers in range(200, 251):
            return self.__calc_parser(self.tax_per_horse_power["from_201_to_250"])
        elif self.horse_powers in range(250, 301):
            return self.__calc_parser(self.tax_per_horse_power["from_251_to_300"])
        elif self.horse_powers > 300:
            if self.debug:
                print(f"Car have a more then 301 horse powers: {self.horse_powers}")
            return self.__calc_parser(self.tax_per_horse_power["more_then_300"])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--horsepowers","-p",
                        type=int,
                        nargs=1,
                        help="Horse powers of machine")
    parser.add_argument("--prod-year", "-y",
                        type=int,
                        nargs=1,
                        help="Year of producton")
    parser.add_argument("--debug",
                        action='store_true',
                        dest='debug',
                        default=False,
                        help="turn on debug mode")
    args = parser.parse_args()
    car_age = args.prod_year[0]
    car_horse_powers = args.horsepowers[0]
    debug_mode = args.debug
    tax = CarEcoTax(car_age, car_horse_powers, debug_mode)
    print(tax.calculate())
