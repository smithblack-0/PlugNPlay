import unittest
import warnings
from unittest.mock import patch
from src.text_extraction import PythonCallExtractor


# Assuming the implementation is in a module named `text_extractor`
# from text_extractor import PythonCallExtractor, TextIRStub, irnodes

class TestPythonCallExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = PythonCallExtractor()

    def test_qualified_names(self):
        text = 'blah blah blah supermodule.module.this_is_a_test("arg1", 3) blah end'
        function_name = "this_is_a_test"
        expected_text_template = 'blah blah blah {this_is_a_test_1} blah end'
        expected_results = {
            "this_is_a_test_1": {
                "name": "this_is_a_test",
                "args": ["arg1", 3],
                "kwargs": {}
            }
        }

        text_template, results = self.extractor.extract_function_invocations(text, function_name)
        self.assertEqual(expected_text_template, text_template)
        for result in results:
            reference = result.pop("reference")
            self.assertEqual(expected_results[reference], result)

    def test_function_with_positional_args(self):
        text = 'blah blah blah this_is_a_test(1, 2, 3) blah end'
        function_name = "this_is_a_test"
        expected_text_template = 'blah blah blah {this_is_a_test_1} blah end'
        expected_results = {
            "this_is_a_test_1": {
                "name": "this_is_a_test",
                "args": [1, 2, 3],
                "kwargs": {}
            }
        }

        text_template, results = self.extractor.extract_function_invocations(text, function_name)
        self.assertEqual(text_template, expected_text_template)
        for result in results:
            reference = result.pop("reference")
            self.assertEqual(expected_results[reference], result)

    def test_function_with_keyword_args(self):
        text = 'blah blah blah this_is_a_test(a=1, b=2, c=3) blah end'
        function_name = "this_is_a_test"
        expected_text_template = 'blah blah blah {this_is_a_test_1} blah end'
        expected_results = {
            "this_is_a_test_1": {
                "name": "this_is_a_test",
                "args": [],
                "kwargs": {"a": 1, "b": 2, "c": 3}
            }
        }

        text_template, results = self.extractor.extract_function_invocations(text, function_name)
        self.assertEqual(text_template, expected_text_template)
        for result in results:
            reference = result.pop("reference")
            self.assertEqual(expected_results[reference], result)

    def test_function_with_unknown_variables(self):
        text = 'blah blah blah this_is_a_test(var1, var2) blah end'
        function_name = "this_is_a_test"
        expected_text_template = 'blah blah blah {this_is_a_test_1} blah end'
        expected_results = {
            "this_is_a_test_1": {
                "name": "this_is_a_test",
                "args": ["<var:var1>", "<var:var2>"],
                "kwargs": {}
            }
        }

        text_template, results = self.extractor.extract_function_invocations(text, function_name)
        self.assertEqual(text_template, expected_text_template)
        for result in results:
            reference = result.pop("reference")
            self.assertEqual(expected_results[reference], result)

    @patch('warnings.warn')
    def test_warn_similar_names(self, mock_warn):
        text = 'blah blah blah this_is_a_tests(1, 2, 3) blah end'
        function_name = "this_is_a_test"
        self.extractor.extract_function_invocations(text, function_name, threshold=2)

        mock_warn.assert_called_with(
            "Warning: Function name 'this_is_a_tests' is within 1 edits of 'this_is_a_test'.",
            UserWarning
        )


if __name__ == '__main__':
    unittest.main()
