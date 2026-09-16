import unittest

from pim.model.errors import (
    ParseError,
    PimError,
    PIRNotFoundError,
    StorageError,
    ValidationError,
)


class ErrorHierarchyTests(unittest.TestCase):
    def test_validation_error_is_a_pim_error(self):
        self.assertTrue(issubclass(ValidationError, PimError))

    def test_pir_not_found_error_is_a_pim_error(self):
        self.assertTrue(issubclass(PIRNotFoundError, PimError))

    def test_parse_error_is_a_pim_error(self):
        self.assertTrue(issubclass(ParseError, PimError))

    def test_storage_error_is_a_pim_error(self):
        self.assertTrue(issubclass(StorageError, PimError))


if __name__ == "__main__":
    unittest.main()
