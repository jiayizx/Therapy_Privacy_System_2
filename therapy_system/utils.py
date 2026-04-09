from typing import Generator, Union

def _escape_generator(gen: Generator[str, None, None], rules) -> Generator[str, None, None]:
    for chunk in gen:
        yield rules(chunk)

def escape_special_characters(text: Union[str, Generator[str, None, None]]) -> Union[str, Generator[str, None, None]]:
    rules = lambda x: x.replace("$", r"\$").replace("*", r"\*")
    if isinstance(text, Generator):
        return _escape_generator(text, rules)
    else:
        return rules(text)

def unescape_special_characters(text: str) -> str:
    rules = lambda x: x.replace(r"\$", "$").replace(r"\*", "*")
    return rules(text)
    #     for chunk in text:
    #         yield rules(chunk)
    # else:
    #     return rules(text)
