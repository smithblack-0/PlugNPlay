"""
Unit tests for the prompts system.

This includes tests for the prompt mechanism itself, alongside tests for
the loading system.
"""
import textwrap
import unittest
from unittest.mock import patch, mock_open
from src import prompts

PRINT_ERROR_MESSAGES = True
PRINT_PROMPT_MESSAGES = True

class TestPrompt(unittest.TestCase):
    """
    Test feature to test the Prompt class.
    """

    def setUp(self) -> None:
        # Setup the test prompt, with formatting features.
        test_prompt = """
        This is a test prompt.

        {dependency_one}

        {dependency_one}

        {dependency_two}
        """
        test_prompt = textwrap.dedent(test_prompt)

        # Define matching dependencies
        dependencies = {"dependency_one": "foo", "dependency_two": "bar"}

        # Define expected outcome
        expected_prompt = """
        This is a test prompt.

        foo

        foo

        bar
        """
        expected_prompt = textwrap.dedent(expected_prompt)

        # Store
        self.test_template = test_prompt
        self.dependencies = dependencies
        self.expected_prompt = expected_prompt

    def test_init(self):
        """ Test that initialization is operating sanely """
        max_char_width = 3
        prompt = prompts.Prompt(self.test_template, 3)
        self.assertEqual(prompt.max_width, 3)
        self.assertEqual(prompt.template, self.test_template)
        self.assertEqual(prompt.dependencies, {"dependency_one", "dependency_two"})

    def test_format(self):
        """ Test the prompt formatting feature, including if it resolves dynamic requirements """
        prompt = prompts.Prompt(self.test_template, None)

        # Test we throw as expected when not satisfying dependencies
        with self.assertRaises(RuntimeError) as err:
            prompt.format({})
        if PRINT_ERROR_MESSAGES:
            print("---Error message during test_format of test prompt---")
            print(err)

        # Test we do not throw when dependencies are satisfied
        output = prompt.format(self.dependencies)
        if PRINT_PROMPT_MESSAGES:
            print("---Prompt message during test_format of test prompt---")
            print(output)

        # Test we are actually getting the expected result
        self.assertEqual(self.expected_prompt, output)

    def test_say(self):
        """
        Test the generator the prompter produces, and ensures we are following all
        the rules we need to.
        """
        prompt = prompts.Prompt(self.test_template, None)
        contents = list(prompt.say(self.dependencies))
        self.assertEqual(contents, [self.expected_prompt])

        # Test we slice the prompt into pieces when appropriate
        long_prompt = self.test_template * 30
        long_response = self.expected_prompt * 30
        max_length = 400

        prompt = prompts.Prompt(long_prompt, max_length)
        if PRINT_PROMPT_MESSAGES:
            print("---Beginning of prompt slice messages---")

        for section in prompt.say(self.dependencies):
            self.assertLessEqual(len(section), max_length)
            if PRINT_PROMPT_MESSAGES:
                print(section)

class TestLoadPromptFromDict(unittest.TestCase):
    """
    Load prompt from dict is one of the major functions.
    """
    def setUp(self):
        test_data = {}
        prompt = """
        This is a test prompt.

        It contains within it a static dependency, as follows

        {static}

        A dynamic dependency as follows

        {dynamic}

        And a static dependency that in turn has a dynamic dependency

        {static_with_dynamic}
        """
        prompt = textwrap.dedent(prompt)
        test_data["prompt"] = prompt

        static = "This is the static dependency"
        test_data["static"] = static

        static_with_dynamic = "This is a static entry with dynamic content: {dynamic_2}"
        test_data["static_with_dynamic"] = static_with_dynamic

        test_data["unused"] = "This is unused data. It should not be fetched at all"

        test_data["dynamic_keywords"] = ["dynamic", "dynamic_2"]

        expected_prompt = """
        This is a test prompt.

        It contains within it a static dependency, as follows

        This is the static dependency

        A dynamic dependency as follows

        {dynamic}

        And a static dependency that in turn has a dynamic dependency

        This is a static entry with dynamic content: {dynamic_2}
        """
        expected_prompt = textwrap.dedent(expected_prompt)
        expected_used = {"static", "static_with_dynamic"}

        self.test_data = test_data
        self.expected_prompt = expected_prompt
        self.expected_used = expected_used

    def print_exception(self, task: str, error: Exception):
        print(task)
        print(error)
        while error.__cause__ is not None:
            print("--- this was caused by ---")
            print(error.__cause__)
            error = error.__cause__

    def test_load_prompt(self):
        """ Test if assemble prompt works on the test data """
        prompt = prompts.load_prompt_from_dict(self.test_data)

        if PRINT_PROMPT_MESSAGES:
            print("---This prompt was assembled while testing assemble_prompt---")
            print(prompt.template)

        self.assertEqual(self.expected_prompt, prompt.template)

    def test_dynamic_throw_not_on_whitelist(self):
        """ Test if we throw when dynamic features are found that are not on the whitelist """
        bad_data = self.test_data.copy()
        bad_data.pop("dynamic_keywords")

        with self.assertRaises(prompts.ParseError) as err:
            prompts.load_prompt_from_dict(bad_data)
        if PRINT_ERROR_MESSAGES:
            task = "---error generated while testing throw from not on whitelist---"
            self.print_exception(task, err.exception)

    def test_throw_referring_to_dynamic_list(self):
        used = set()
        prompt = "This should be illegal: {dynamic_keywords}"
        resources = {"prompt": prompt, "dynamic_keywords": "foo"}

        with self.assertRaises(prompts.ParseError) as err:
            prompts.load_prompt_from_dict(resources)
        if PRINT_ERROR_MESSAGES:
            task = "---error generated while testing throw due to keyword collision---"
            self.print_exception(task, err.exception)

    def test_throw_wrong_dtype(self):
        """ If the dictionary is malformed with bad formatting resources, detect and throw """
        used = set()
        prompt = "This refers to a list of strings: {list_of_strings}"
        resources = {"prompt": prompt, "list_of_strings": ["item1", "item2"]}

        with self.assertRaises(prompts.ParseError) as err:
            prompts.parse_prompt(prompt, resources, used, {})

        if PRINT_ERROR_MESSAGES:
            task = "---error generated while testing wrong dtype in toml---"
            self.print_exception(task, err.exception)

    def test_detect_recurrent_resource(self):
        """ Test if the user is making a boneheaded recurrent mistake """
        resources = {
            "prompt": "This refers to {recurrent}",
            "recurrent": "This refers to {recurrent_2}",
            "recurrent_2": "This refers back to {recurrent}"
        }
        with self.assertRaises(prompts.ParseError) as err:
            prompts.load_prompt_from_dict(resources)
        if PRINT_ERROR_MESSAGES:
            task = "--- error message generated while testing recursion catch condition ---"
            self.print_exception(task, err.exception)

    def test_dynamic_pass(self):
        """ Test if the dynamic passing works """
        resources = {"prompt": "this is dynamic {dynamic}"}
        prompts.load_prompt_from_dict(resources, dynamic_keywords=["dynamic"])

    def test_max_width_pass(self):
        """ Test if the max width is being passed in sanely """
        resources = {"prompt": "this is just a test"}
        output = prompts.load_prompt_from_dict(resources, 3)
        self.assertEqual(output.max_width, 3)

class TestLoadPromptsFromFile(unittest.TestCase):
    """
    Test that we can successfully load in prompts from a file.
    """

    def setUp(self) -> None:
        mock_toml = """
        
        [Irrelevant]
        item = 3
        otheritem = 4
        
        [TestFeature.prompt]
        prompt = '''
        This is a prompt. We have one 
        static feature, {this}
        '''
        this = "Here is the static feature"
        
        [DynamicTestFeature.prompt]
        prompt = '''
        This is a dynamic test feature. The following
        must be dynamic: {dynamic}, {dynamic_2}
        '''
        dynamic_keywords = ["dynamic", "dynamic_2"]
        """
        mock_toml = textwrap.dedent(mock_toml)
        self.mock_toml = mock_toml

    def test_load(self):
        with patch("builtins.open", mock_open(read_data=self.mock_toml)) as mock_file:
            results = prompts.load_prompts_from_file("path")

        self.assertEqual(["TestFeature", "DynamicTestFeature"], list(results.keys()))

if __name__ == '__main__':
    unittest.main()
