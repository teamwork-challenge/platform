import random
import unittest
from typing import Any, List
from router import (
    convert_to_decimal,
    generate_mixed_types,
    get_answer,
    gen_int,
    gen_base5,
    gen_bigint,
    gen_complex,
    gen_matrix,
    gen_fib_num,
    gen_roman_num
)


class TestNumericalOperations(unittest.TestCase):
    # --------------------------
    # Conversion Tests
    # --------------------------

    def test_roman_conversion(self):
        test_cases = [
            ("I", 1), ("V", 5), ("X", 10), ("L", 50), ("C", 100),
            ("D", 500), ("M", 1000), ("IV", 4), ("IX", 9),
            ("XL", 40), ("XC", 90), ("CD", 400), ("CM", 900),
            ("III", 3), ("XXVIII", 28), ("XCIX", 99),
            ("CDXLIV", 444), ("MCMXC", 1990), ("MMMCMXCIX", 3999)
        ]
        for roman, expected in test_cases:
            with self.subTest(roman=roman):
                self.assertEqual(convert_to_decimal(roman, 7), expected)

    def test_fib_conversion(self):
        test_cases = [
            ("0F", 0), ("1F", 1), ("10F", 2), ("100F", 3), ("101F", 4),
            ("1000F", 5), ("1001F", 6), ("1010F", 7), ("10000F", 8),
            ("100000F", 13), ("1000000F", 21), ("101010F", 20)
        ]
        for fib, expected in test_cases:
            with self.subTest(fib=fib):
                self.assertEqual(convert_to_decimal(fib, 6), expected)

    def test_base5_conversion(self):
        test_cases = [
            ("0_5", 0), ("1_5", 1), ("10_5", 5), ("21_5", 11),
            ("100_5", 25), ("1234_5", 194), ("43210_5", 2930)
        ]
        for base5, expected in test_cases:
            with self.subTest(base5=base5):
                self.assertEqual(convert_to_decimal(base5, 2), expected)

    # --------------------------
    # Generator Tests
    # --------------------------

    def test_generators(self):
        # Test integer generator
        for _ in range(100):
            num = gen_int()
            self.assertIsInstance(num, int)
            self.assertTrue(1 <= num <= 100)

        # Test base5 generator
        for _ in range(100):
            num = gen_base5()
            self.assertTrue(num.endswith('_5'))
            digits = num[:-2]
            self.assertTrue(all(c in '01234' for c in digits))

        # Test bigint generator
        for _ in range(100):
            num = gen_bigint()
            self.assertIsInstance(num, int)
            self.assertTrue(-10 ** 30 <= num <= 10 ** 30)

        # Test complex generator
        for _ in range(100):
            num = gen_complex()
            self.assertIsInstance(num, complex)
            self.assertTrue(1 <= num.real <= 50)
            self.assertTrue(1 <= num.imag <= 50)

        # Test matrix generator
        for _ in range(100):
            size = random.randint(2, 5)
            matrix = gen_matrix(size)
            self.assertEqual(len(matrix), size)
            for row in matrix:
                self.assertEqual(len(row), size)
                self.assertTrue(all(0 <= x <= 10 for x in row))

        # Test Fibonacci number generator
        for _ in range(100):
            fib_num = gen_fib_num()
            self.assertTrue(fib_num.endswith('F'))
            digits = fib_num[:-1]
            self.assertTrue(all(c in '01' for c in digits))
            # Verify it's a valid Fibonacci number
            decimal_val = convert_to_decimal(fib_num, 6)
            self.assertTrue(1 <= decimal_val <= 10000)

        # Test Roman numeral generator
        for _ in range(100):
            roman = gen_roman_num()
            decimal_val = convert_to_decimal(roman, 7)
            self.assertTrue(1 <= decimal_val <= 4999)

    # --------------------------
    # Operation Tests
    # --------------------------

    def test_matrix_operations(self):
        # Test same size matrices
        matrix1 = [[1, 2], [3, 4]]
        matrix2 = [[5, 6], [7, 8]]
        result = get_answer(matrix1, matrix2, 5, 5)
        self.assertEqual(result, "[[6, 8], [10, 12]]")

    def test_complex_operations(self):
        # Test complex + complex
        c1 = complex(1, 2)
        c2 = complex(3, 4)
        result = get_answer(c1, c2, 4, 4)
        self.assertEqual(result, "(4+6j)")

        # Test complex + int
        result = get_answer(c1, 5, 4, 1)
        self.assertEqual(result, "(6+2j)")


    def test_mixed_type_operations(self):
        # Test base5 + int
        result = get_answer("12_5", 3, 2, 1)
        self.assertEqual(result, "10")  # 7 + 3

        # Test Fibonacci + Roman
        result = get_answer("100F", "V", 6, 7)
        self.assertEqual(result, "8")  # 3 + 5

        # Test bigint + complex
        result = get_answer(10 ** 20, complex(1, 1), 3, 4)
        self.assertEqual(result, "(1e+20+1j)")

    # --------------------------
    # Edge Case Tests
    # --------------------------

    def test_zero_values(self):
        # Test zeros in all formats
        self.assertEqual(get_answer(0, 0, 1, 1), "0")
        self.assertEqual(get_answer("0_5", "0_5", 2, 2), "0")
        self.assertEqual(get_answer(0j, 0j, 4, 4), "0j")
        self.assertEqual(get_answer("0F", "0F", 6, 6), "0")
        self.assertEqual(get_answer("", "", 7, 7), "0")  # Empty Roman
        self.assertEqual(get_answer([[0, 0], [0, 0]], [[0, 0], [0, 0]], 5, 5), "[[0, 0], [0, 0]]")

    def test_extreme_values(self):
        # Test with maximum values
        max_int = 10 ** 30
        min_int = -10 ** 30
        self.assertEqual(get_answer(max_int, min_int, 3, 3), "0")

        # Test with large complex numbers
        big_complex = complex(1e20, 1e20)
        self.assertEqual(get_answer(big_complex, big_complex, 4, 4), "(2e+20+2e+20j)")

        # Test with large Fibonacci numbers
        fib_num = "101010101010101010101010101010F"  # Large Fibonacci number
        self.assertTrue(convert_to_decimal(fib_num, 6) > 1000000)


if __name__ == "__main__":
    unittest.main(verbosity=2)