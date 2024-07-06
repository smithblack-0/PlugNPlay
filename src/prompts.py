"""
Prompts, and the prompts modules are responsible for putting together and keeping organized
the large volume of textual prompts needed to get the relevant LLM's up and running.

---- Prompt definition structure ----

A prompt is ultimately defined in terms of formatting entries.

---- defining a prompt ----

Prompts are defined using the toml syntax under the '[NAME.prompt]' namespace,
with a class name. Parsing will begin at the "prompt" field, which must always
be defined, and proceeds to fill in any formatting entries with other fields
assigned to the class.

---- Dynamic prompts ----

It is useful sometimes to fill in keywords later on with dynamically generated content.
This so-called "dynamic formatting" is supported by the Prompt object.

However, detecting dynamic content by whether or not it was among the fields provided
on the TOML object risks making hard-to-debug errors that only show up when trying
to use the prompt object later on. Instead, dynamic format operates on a whitelist basis -
any format feature that is not explicitly defined as dynamic is assumed to be static, and
violations throw an error.

To support this, two mechanisms exist. You can pass in a list of dynamic keywords, or
you can define the keywords on the TOML file in the dynamic field. An example is shown below.

---- Recursive processing ----

Parsing and formatting is recursive. Anytime any feature loads another
feature, it is the case that the loaded entity will be parsed first, then
inserted into the original template.

"""

import string
import textwrap
import toml
from typing import Dict, Optional, Generator, List, Any


class ParseError(Exception):
    """
    Emitted when the prompt parser encounters an error.
    """

    def __init__(self, message):
        super().__init__(message)


DYNAMIC_KEYWORD = "dynamic_keywords"
PROMPT_KEYWORD = "prompt"


class Prompt:
    """
    A prompt is an entity which exists to format text into a useful
    prompt while making sure all dependencies are satisfied.

    Prompts are created from individual TOML classes beginning
    with a specified namespace. Such classes are expected to contain
    a field "prompt" that contains the actual prompt.

    This prompt may, in turn, contain formatting arguments. These arguments
    can be located elsewhere on the class, be global strings in the TOML
    file, or even might be passed in dynamically on usage of the prompt.

    ---- fields ----
    template: The template that will be populated on usage.
    dependencies: Dynamic dependencies that need to be resolved to say the prompt.
    max_width: The maximum width in characters any given prompt can get.

    ---- methods ----
    say: A generator which is provided dynamic dependencies and produces the prompt in sections depending
         on max size. If max size is none, yields the entire prompt in one go.
    __call__: Alias of say.
    """

    internal_message_issue = """
    It was found to be the case that the character length was shorter
    than some of the internal communication messages. Increase the length
    of the character limit.
    """

    def get_begin_prompt_message(self, num_sections: int):
        msg = f"""
        Beginning prompt feed. Sections may be fed in pieces depending
        on token limits. There are {num_sections} to feed. 

        Sections will be fed in as the section, then another segment telling what
        is feeding next, then the next section. This will continue until all
        sections are fed.

        Do not respond until all feeding has finished, and you have gotten the 
        respond request. Any responses before then will be ignored.
        """
        msg = textwrap.dedent(msg)
        if len(msg) > self.max_width:
            raise RuntimeError(self.internal_message_issue)
        return msg

    def get_prompt_section_message(self, section: int, total_sections: int) -> str:
        msg = f"""
        ---Next feeding section {section} out of {total_sections}---
        """
        msg = textwrap.dedent(msg)

        if len(msg) > self.max_width:
            raise RuntimeError(self.internal_message_issue)
        return msg

    def get_prompting_finished_message(self) -> str:
        msg = """
        All prompt sections have now been fed into the model. Please now provide a response.
        """
        msg = textwrap.dedent(msg)
        if len(msg) > self.max_width:
            raise RuntimeError(self.internal_message_issue)
        return msg

    def __init__(self, prompt: str, max_width: Optional[int] = None):
        formatter = string.Formatter()

        self.dependencies = set([item[1] for item in formatter.parse(prompt) if item[1] is not None])
        self.template = prompt
        self.max_width = max_width

    def format(self, dynamic_dependencies: Dict[str, str]) -> str:
        """
        Formats the prompt, yielding the result.

        :param dynamic_dependencies: A dictionary of dynamic dependencies.
        :return: The formatted prompt string.
        """
        dynamic_keys = set(dynamic_dependencies.keys())
        dependencies_check = list(self.dependencies.difference(dynamic_keys))
        if len(dependencies_check) > 0:
            raise RuntimeError(f"Dependency of prompt not satisfied: '{dependencies_check[0]}'")

        prompt = self.template.format(**dynamic_dependencies)
        return prompt

    def say(self, dependencies: Dict[str, str]) -> Generator[str, None, None]:
        """
        Provides a generator containing the prompt, sliced up
        into the appropriately sized sections.

        :param dependencies: A dictionary of dependencies.
        :return: A generator yielding the prompt sections.
        """
        prompt = self.format(dependencies)

        if self.max_width is None:
            yield prompt
        else:
            lines = textwrap.wrap(prompt, width=self.max_width,
                                  replace_whitespace=False,
                                  fix_sentence_endings=False,
                                  break_on_hyphens=False)
            num_sections = len(lines)

            if num_sections == 1:
                yield lines[0]
            else:
                yield self.get_begin_prompt_message(num_sections)
                for i, line in enumerate(lines):
                    yield self.get_prompt_section_message(i + 1, num_sections)
                    yield line
                yield self.get_prompting_finished_message()


def parse_prompt(parsing: str,
                 resources: Dict[str, str],
                 used: set,
                 dynamic: set) -> str:
    """
    Parses and replaces formatting entries using resources,
    leaving in place anything it cannot find. Provides feedback
    through set side effects.

    :param parsing: The string currently being parsed.
    :param resources: The location to find resources.
    :param used: Resources already used. Detects recursion.
    :param dynamic: Resources needed. Used for feedback.
    :return: An assembled prompt.
    """
    formatter = string.Formatter()
    output = []

    for text, format_entry, _, _ in formatter.parse(parsing):
        output.append(text)

        if format_entry == DYNAMIC_KEYWORD:
            raise ParseError(f"Used reserved term '{DYNAMIC_KEYWORD}' as a formatting feature.")

        if format_entry is not None:
            if format_entry in used:
                msg = f"""
                Recursion detected in prompt definition. Feature of name: '{format_entry}' 
                was called more than one time. This is not allowed. Track
                down why your format references are referring to each other.
                """
                msg = textwrap.dedent(msg)
                raise ParseError(msg)

            if format_entry in resources:
                used.add(format_entry)

                try:
                    feature = resources[format_entry]
                    if not isinstance(feature, str):
                        msg = f"""
                        Formatting resource of name '{format_entry}'
                        was expected to be a string. However, instead found
                        type of '{type(feature)}'
                        """
                        msg = textwrap.dedent(msg)
                        raise ParseError(msg)

                    feature = parse_prompt(feature, resources, used, dynamic)
                    output.append(feature)

                except Exception as err:
                    msg = f"Error occurred while parsing format feature of name '{format_entry}'"
                    raise ParseError(msg) from err

            elif format_entry in dynamic:
                output.append("{" + format_entry + "}")
            else:
                msg = f"""
                Format feature of name '{format_entry}' was not found in prompt
                resources or among dynamic keyword whitelist called '{DYNAMIC_KEYWORD}'.

                Double-check you spelled your formatting references correctly,
                or add keyword to dynamic keyword whitelist.
                """
                msg = textwrap.dedent(msg)
                raise ParseError(msg)

    output = "".join(output)
    return output


def load_prompt_from_dict(prompt_dict: Dict[str, str],
                          max_size: Optional[int] = None,
                          dynamic_keywords: Optional[List[str]] = None,
                          debug: bool = False) -> Prompt:
    """
    Loads a prompt from a prompt dictionary by means of parsing then assembling the
    resulting prompt. Will begin parsing from the 'prompt' feature, and stitch together
    dynamic keyword information.

    :param prompt_dict: A prompt dictionary to parse. Must contain a 'prompt' feature and may
                        contain various static formatting arguments. Also may contain a list
                        of dynamic keyword whitelists in 'dynamic_keywords'.
    :param max_size: Indicates the maximum number of characters per section when using the
                     prompt to feed into a model.
    :param dynamic_keywords: Dynamic keyword whitelist can be fed in here. We can also discover
                             whitelist elements from the 'dynamic_keywords' dictionary whitelist.
    :param debug: Whether to print debugging information.
    :return: A Prompt class.
    """
    if PROMPT_KEYWORD not in prompt_dict:
        msg = f"""
        Prompt definition was found to lack the '{PROMPT_KEYWORD}' feature
        defining the prompt root. It must be added.
        """
        msg = textwrap.dedent(msg)
        raise ParseError(msg)
    if not isinstance(prompt_dict[PROMPT_KEYWORD], str):
        msg = f"""
        Prompt dict was found to have a '{PROMPT_KEYWORD}' entry that
        was not a string. This is not allowed.
        """
        msg = textwrap.dedent(msg)
        raise ParseError(msg)

    prompt_root = prompt_dict[PROMPT_KEYWORD]

    keywords = set()
    if dynamic_keywords is not None:
        keywords.update(set(dynamic_keywords))
    if DYNAMIC_KEYWORD in prompt_dict:
        keywords.update(set(prompt_dict[DYNAMIC_KEYWORD]))

    used = set()
    output = parse_prompt(prompt_root, prompt_dict, used, keywords)

    if debug:
        print("Debugging feedback")
        print("Used features: %s" % used)
        print("Dynamic features: %s" % keywords)

    return Prompt(output, max_size)


def load_prompts_from_file(file,
                           max_size: Optional[int] = None,
                           dynamic_keywords: Optional[List[str]] = None,
                           debug: bool = False) -> Dict[str, Prompt]:
    """
    Load all prompts that can be detected from a TOML file.

    Prompts are defined in the TOML file as any class defined under the
    '[NAME.prompt]' namespace. Classes defined under this namespace are expected to have
    a string feature called 'prompt' attached to them. The return is a dictionary of
    "Prompt" objects assembled out of the TOML object.

    ---- Dynamic prompts ----

    It is useful sometimes to fill in keywords later on with dynamically generated content.
    This so-called "dynamic formatting" is supported by the Prompt object.

    However, detecting dynamic content by whether or not it was among the fields provided
    on the TOML object risks making hard-to-debug errors that only show up when trying
    to use the prompt object later on. Instead, dynamic format operates on a whitelist basis -
    any format feature that is not explicitly defined as dynamic is assumed to be static, and
    violations throw an error.

    To support this, two mechanisms exist. You can pass in a list of dynamic keywords, or
    you can define the keywords on the TOML file in the dynamic field. An example is shown below.

    ---- Recursive processing ----

    Parsing and formatting is recursive. Anytime any feature loads another
    feature, it is the case that the loaded entity will be parsed first, then
    inserted into the original template.

    ---- Example ----

    This is an example piece of TOML that illustrates all these capacities:

    ```
    [Test.prompt]
    dynamic_keywords = ["dynamic"]
    prompt = '''
    This is a very simple example. Here is some static content

    {static}

    Here is some dynamic content

    {dynamic}

    Here is some content that will load other content:

    {static_indirection}

    '''
    static = 'This static content will be substituted'
    static_indirection = '''

    The following content is indirected:

    {indirect}

    '''
    indirect = "This was retrieved recursively"
    ```

    --- params---

    :param file: The toml file to load prompts from.
    :param max_size: The maximum number of characters before we need to slice up a prompt
                     into pieces.
    :param debug: Prints debug information.
    :return: A dictionary of discovered prompts.
    """
    with open(file, 'r') as f:
        config_contents = toml.load(f)
        prompts = {}
        for k, v in config_contents.items():
            if isinstance(v, dict) and PROMPT_KEYWORD in v:
                prompts[k] = v[PROMPT_KEYWORD]

    output = {}
    for name, prompt_dict in prompts.items():
        output[name] = load_prompt_from_dict(prompt_dict, max_size, dynamic_keywords, debug)

    return output
