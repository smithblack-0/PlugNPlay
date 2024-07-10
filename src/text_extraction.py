import ast
import re
import textwrap
import warnings

import Levenshtein

from src import irnodes
from src.module import TextIRStub


class TextExtractor:
    """
    A class that can be used to extract TextTreeStubs
    from raw text. This will include any processes needed
    to end up with a ir tree.

    ---- fields ----
    context: A context string implemented by subclasses, that displays what is being
    extracted. Inserted at the beginning of a TextIRSTub
    registry: A registry of all know text extractors.

    ---- methods ----
    implementation: Implemented by a subclass to perform the extraction
    extract: Method called to perform extraction

    """
    context: str
    registry = {}
    def __init_subclass__(cls, register: bool = None, **kwargs):
        if register:
            cls.registry[cls.__name__] =  cls
        super().__init_subclass__(**kwargs)
    def implementation(self, text: str, **kwargs)-> TextIRStub:
        """

        :param id: A unique id assigned to this block of text
        :param text: The text we are converting
        :param kwargs:
        :return:
        """
        raise NotImplementedError("Subclass needs to implement extract")
    def extract(self, text: str, **kwargs)-> TextIRStub:
        if not hasattr(self, "context"):
            raise AttributeError("Context attribute")
        context = textwrap.dedent(self.context)
        stub = self.implementation(text, **kwargs)
        new_template = context + stub.text_template
        return TextIRStub(stub.name, new_template, stub.ir_elements, text)


class PythonCallExtractor(TextExtractor, register=True):
    """
    Extracts python function calls from text and
    returns a TextIRStub
    """
    context = """
    ---- Conversion warning ---
    
    The following text has been automatically converted from
    its original format. This is intended to give you the opportunity
    to see examples being invoked using the mechanisms that you will
    actually have to use as an LLM model.
    
    However, it may sometimes cause weird behavior wherein python code 
    suddenly switches to something else like xml. Be aware such cases
    are showing you how to invoke the code through your local interface.
    
    The conversion is automatic and not perfect. If you suspect an issue,
    consider using a different or raw conversion to get a working manual.
    ---- End conversion warning ----
    """
    @staticmethod
    def find_matching_parenthesis(s, start_idx):
        """Find the index of the matching parenthesis."""
        paren_count = 1
        for i in range(start_idx + 1, len(s)):
            if s[i] == '(':
                paren_count += 1
            elif s[i] == ')':
                paren_count -= 1
            if paren_count == 0:
                return i
        return -1  # if no matching parenthesis is found

    @classmethod
    def process_arg(cls, arg):
        """Process a single argument, handling variables and tuples."""
        if isinstance(arg, ast.Name):
            return f"<var:{arg.id}>"
        elif isinstance(arg, ast.Tuple):
            return tuple(cls.process_arg(elt) for elt in arg.elts)
        else:
            return ast.literal_eval(arg)

    @classmethod
    def parse_arguments(cls, arg_str):
        """Parse arguments from the argument string."""
        try:
            parsed = ast.parse(f"f({arg_str})").body[0].value
            args = [cls.process_arg(arg) for arg in parsed.args]
            kwargs = {kw.arg: cls.process_arg(kw.value) for kw in parsed.keywords}
            return args, kwargs
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing arguments: {e}")
            return [], {}

    @staticmethod
    def warn_similar_names(matched_name, function_name, threshold=8):
        """Emit warnings if a matched function name is similar to the target function name."""
        if matched_name == function_name:
            return
        distance = Levenshtein.distance(matched_name, function_name)
        if distance <= threshold:
            warnings.warn(f"Warning: Function name '{matched_name}' is within {distance} edits of '{function_name}'.", UserWarning)

    @classmethod
    def extract_function_invocations(cls, text, function_name, threshold=8):
        """
        Extract specific function invocations from text, replacing them with references.

        Args:
            text (str): The input text containing function invocations.
            function_name (str): The function name to extract.
            threshold (int): The Levenshtein distance threshold for emitting warnings.

        Returns:
            dict: A dictionary with processed text and details of function invocations.
        """
        func_call_pattern = re.compile(r'((?:\w+\.)*(\w+))\s*\(')
        matches = list(func_call_pattern.finditer(text))
        results = []
        processed_text = text
        count = 1
        offset = 0

        for match in matches:
            full_name = match.group(1)
            func_name = match.group(2)
            cls.warn_similar_names(func_name, function_name, threshold)
            if func_name != function_name:
                continue

            start_idx = match.end() - 1
            end_idx = cls.find_matching_parenthesis(text, start_idx)

            if end_idx == -1:
                continue

            arg_str = text[start_idx + 1:end_idx]
            args, kwargs = cls.parse_arguments(arg_str)

            reference = f"{func_name}_{count}"
            count += 1

            results.append({
                "name": func_name,
                "reference": reference,
                "args": args,
                "kwargs": kwargs
            })

            # Replace the original function call with a placeholder
            original_call = text[match.start():end_idx + 1]
            placeholder = f"{{{reference}}}"
            processed_text = processed_text[:match.start() + offset] + placeholder + processed_text[end_idx + 1 + offset:]
            offset += len(placeholder) - len(original_call)

        return processed_text, results

    def extract(self, text: str, **kwargs) -> TextIRStub:
        text_template, results = self.extract_function_invocations(text, kwargs["function_name"])
        ir_dict = {}
        for result in results:
            reference = result.pop("reference")
            ir_dict[reference] = irnodes.pytree_to_schema(result)
        return TextIRStub(kwargs["function_name"], text_template, ir_dict, text)
