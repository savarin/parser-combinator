from typing import Callable, List, Literal, Optional, Tuple, Union


PairList = Union[Tuple[Optional[List[str]], str], Literal[False]]
PairListCallable = Callable[[str], PairList]


def shift(source: str) -> PairList:
    return bool(source) and ([source[0]], source[1:])


def nothing(source: str) -> PairList:
    return (None, source)


def sift(
    predicate: Callable[[List[str]], bool]
) -> Callable[[PairListCallable], PairListCallable]:
    def f(parser: PairListCallable) -> PairListCallable:
        def g(source: str) -> PairList:
            def h(result: PairList) -> PairList:
                if result is False:
                    return result

                assert isinstance(result, tuple) and result[0] is not None
                return predicate(result[0]) and result

            return h(parser(source))

        return g

    return f


def literal(value: str) -> Callable[[PairListCallable], PairListCallable]:
    def f(source: List[str]) -> bool:
        return all([item == value for item in source])

    return sift(f)


def member_of(values: str) -> Callable[[PairListCallable], PairListCallable]:
    def f(source: List[str]) -> bool:
        return all([item in values for item in source])

    return sift(f)


def char(value: str) -> PairListCallable:
    return literal(value)(shift)


def fmap(
    func: Callable[[List[str]], List[str]]
) -> Callable[[PairListCallable], PairListCallable]:
    def f(parser: PairListCallable) -> PairListCallable:
        def g(source: str) -> PairList:
            def h(result: PairList) -> PairList:
                if result is False:
                    return result

                assert isinstance(result, tuple) and result[0] is not None
                return (func(result[0]), result[1])

            return h(parser(source))

        return g

    return f


def one_or_more(parser: PairListCallable) -> PairListCallable:
    def parse(source: str) -> PairList:
        result: List[str] = []

        while True:
            pair = parser(source)

            if not pair:
                break

            value, source = pair
            assert value is not None
            result += value or [""]

        return bool(result) and (result, source)

    return parse


def sequence(*parsers: PairListCallable) -> PairListCallable:
    def parse(source: str) -> PairList:
        result: List[str] = []

        for parser in parsers:
            pair = parser(source)

            if not pair:
                return False

            value, source = pair
            assert value is not None
            result += value or [""]

        return (result, source)

    return parse


def either(left: PairListCallable, right: PairListCallable) -> PairListCallable:
    def parse(source: str) -> PairList:
        return left(source) or right(source)

    return parse


def maybe(parser: PairListCallable) -> PairListCallable:
    return either(parser, nothing)


def zero_or_more(parser: PairListCallable) -> PairListCallable:
    return either(one_or_more(parser), sequence())


def choice(parser: PairListCallable, *parsers: PairListCallable) -> PairListCallable:
    return either(parser, choice(*parsers) if parsers else parser)


def test_run() -> None:
    assert shift("bar") == (["b"], "ar")
    assert shift("ar") == (["a"], "r")
    assert shift("r") == (["r"], "")
    assert shift("") is False

    assert nothing("bar") == (None, "bar")

    digit = sift(lambda x: all(map(str.isdigit, x)))(shift)
    letter = sift(lambda x: all(map(str.isalpha, x)))(shift)
    assert digit("456") == (["4"], "56")
    assert letter("456") is False

    dot = literal(".")(shift)
    even = member_of("02468")(digit)
    assert dot(".456") == (["."], "456")
    assert dot("45.6") is False
    assert even("456") == (["4"], "56")
    assert even("345") is False

    dot = char(".")
    assert dot(".456") == (["."], "456")

    ndigit = fmap(lambda x: list(map(int, x)))(digit)  # type: ignore
    tenx = fmap(lambda x: list(map(lambda y: 10 * y, x)))
    assert ndigit("456") == ([4], "56")
    assert tenx(ndigit)("456") == ([40], "56")
    assert tenx(digit)("456") == (["4444444444"], "56")

    digits = one_or_more(digit)
    assert digits("456") == (["4", "5", "6"], "")
    assert digits("1abc") == (["1"], "abc")
    assert digits("abc") == False

    digits = fmap(lambda x: ["".join(x)])(one_or_more(digit))
    assert digits("456") == (["456"], "")

    value = fmap(lambda x: list(map(int, x)))(digits)  # type: ignore
    assert value("456") == ([456], "")

    assert sequence(letter, digit, letter)("a4x") == (["a", "4", "x"], "")
    assert sequence(letter, digit, letter)("abc") is False
    assert sequence(letter, fmap(lambda x: ["".join(x)])(one_or_more(digit)))("x12345") == (  # type: ignore
        ["x", "12345"],
        "",
    )

    left = lambda p1, p2: fmap(lambda p: [p[0]])(sequence(p1, p2))
    right = lambda p1, p2: fmap(lambda p: [p[1]])(sequence(p1, p2))
    assert left(letter, digit)("a4") == (["a"], "")
    assert right(letter, digit)("a4") == (["4"], "")

    alnum = either(letter, digit)  # type: ignore
    assert alnum("4a") == (["4"], "a")
    assert alnum("a4") == (["a"], "4")
    assert alnum("$4") is False

    assert maybe(digit)("456") == (["4"], "56")
    assert maybe(digit)("abc") == (None, "abc")

    assert zero_or_more(digit)("456") == (["4", "5", "6"], "")
    assert zero_or_more(digit)("abc") == ([], "abc")

    # example: numbers
    dot = char(".")
    digit = sift(lambda x: all(map(str.isdigit, x)))(shift)
    digits = fmap(lambda x: ["".join(x)])(one_or_more(digit))
    decdigits = fmap(lambda x: ["".join(x)])(
        choice(
            sequence(digits, dot, digits), sequence(digits, dot), sequence(dot, digits)
        )
    )
    integer = fmap(lambda x: list(map(int, x)))(digits)  # type: ignore
    decimal = fmap(lambda x: list(map(float, x)))(decdigits)  # type: ignore
    number = choice(decimal, integer)
    assert number("1234") == ([1234], "")
    assert number("12.3") == ([12.3], "")
    assert number(".123") == ([0.123], "")
    assert number("123.") == ([123.0], "")
    assert number(".xyz") is False

    # example: key-value pairs
    letter = sift(lambda x: all(map(str.isalpha, x)))(shift)
    letters = fmap(lambda x: ["".join(x)])(one_or_more(letter))
    whitespace = sift(lambda x: all(map(str.isspace, x)))(shift)
    whitespaces = fmap(lambda x: ["".join(x)])(zero_or_more(whitespace))
    token = lambda parser: right(whitespaces, parser)
    equal = token(char("="))
    semicolon = token(char(";"))
    name = token(letters)
    value = token(number)
    key_value = sequence(left(name, equal), left(value, semicolon))
    assert key_value("xyz=123;") == (["xyz", 123], "")
    assert key_value("   pi = 3.14  ;") == (["pi", 3.14], "")

    # example: building dictionary
    key_values = fmap(lambda x: dict(zip(x[::2], x[1::2])))(zero_or_more(key_value))  # type: ignore
    assert key_values("x=2; y=3.4; z=.789;") == ({"x": 2, "y": 3.4, "z": 0.789}, "")
    assert key_values("") == ({}, "")

    # example: validating dictionary keys
    xy_dict = sift(lambda d: d.keys() == {"x", "y"})(key_values)  # type: ignore
    assert xy_dict("x=4;y=5;") == ({"x": 4, "y": 5}, "")
    assert xy_dict("y=5;x=4;") == ({"y": 5, "x": 4}, "")
    assert xy_dict("x=4;y=5;z=6;") is False


if __name__ == "__main__":
    test_run()
