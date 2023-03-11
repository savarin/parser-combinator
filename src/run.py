from typing import Callable, List, Literal, Optional, Tuple, Union


Pair = Union[Tuple[Optional[str], str], Literal[False]]
PairCallable = Callable[[str], Pair]

PairList = Union[Tuple[List[str], str], Literal[False]]
PairListCallable = Callable[[str], PairList]


def shift(source: str) -> Pair:
    return bool(source) and (source[0], source[1:])


def nothing(source: str) -> Pair:
    return (None, source)


def sift(predicate: Callable[[str], bool]) -> Callable[[PairCallable], PairCallable]:
    def f(parser: PairCallable) -> PairCallable:
        def g(source: str) -> Pair:
            def h(result: Pair) -> Pair:
                if result is False:
                    return result

                assert isinstance(result, tuple) and result[0] is not None
                return predicate(result[0]) and result

            return h(parser(source))

        return g

    return f


def literal(value: str) -> Callable[[PairCallable], PairCallable]:
    def f(source: str) -> bool:
        return source == value

    return sift(f)


def member_of(values: str) -> Callable[[PairCallable], PairCallable]:
    def f(source: str) -> bool:
        return source in values

    return sift(f)


def char(value: str) -> PairCallable:
    return literal(value)(shift)


def fmap(func: Callable[[str], str]) -> Callable[[PairCallable], PairCallable]:
    def f(parser: PairCallable) -> PairCallable:
        def g(source: str) -> Pair:
            def h(result: Pair) -> Pair:
                if result is False:
                    return result

                assert isinstance(result, tuple) and result[0] is not None
                return (func(result[0]), result[1])

            return h(parser(source))

        return g

    return f


def one_or_more(parser: PairCallable) -> PairListCallable:
    def parse(source: str) -> PairList:
        result: List[str] = []

        while True:
            pair = parser(source)

            if not pair:
                break

            value, source = pair
            assert value is not None
            result.append(value)

        return bool(result) and (result, source)

    return parse


def sequence(*parsers: PairCallable) -> PairListCallable:
    def parse(source: str) -> PairList:
        result: List[str] = []

        for parser in parsers:
            pair = parser(source)

            if not pair:
                return False

            value, source = pair
            assert value is not None
            result.append(value)

        return (result, source)

    return parse


def either(left: PairCallable, right: PairCallable) -> PairCallable:
    def parse(source: str) -> Pair:
        return left(source) or right(source)

    return parse


def maybe(parser: PairCallable) -> PairCallable:
    return either(parser, nothing)


def test_run() -> None:
    assert shift("bar") == ("b", "ar")
    assert shift("ar") == ("a", "r")
    assert shift("r") == ("r", "")
    assert shift("") is False

    assert nothing("bar") == (None, "bar")

    digit = sift(str.isdigit)(shift)
    letter = sift(str.isalpha)(shift)
    assert digit("456") == ("4", "56")
    assert letter("456") is False

    dot = literal(".")(shift)
    even = member_of("02468")(digit)
    assert dot(".456") == (".", "456")
    assert dot("45.6") is False
    assert even("456") == ("4", "56")
    assert even("345") is False

    dot = char(".")
    assert dot(".456") == (".", "456")

    ndigit = fmap(int)(digit)  # type: ignore
    tenx = fmap(lambda x: 10 * x)
    assert ndigit("456") == (4, "56")
    assert tenx(ndigit)("456") == (40, "56")
    assert tenx(digit)("456") == ("4444444444", "56")

    digits = one_or_more(digit)
    assert digits("456") == (["4", "5", "6"], "")
    assert digits("1abc") == (["1"], "abc")
    assert digits("abc") == False

    digits = fmap("".join)(one_or_more(digit))  # type: ignore
    assert digits("456") == ("456", "")

    value = fmap(int)(digits)  # type: ignore
    assert value("456") == (456, "")

    assert sequence(letter, digit, letter)("a4x") == (["a", "4", "x"], "")
    assert sequence(letter, digit, letter)("abc") is False
    assert sequence(letter, fmap("".join)(one_or_more(digit)))("x12345") == (  # type: ignore
        ["x", "12345"],
        "",
    )

    left = lambda p1, p2: fmap(lambda p: p[0])(sequence(p1, p2))  # type: ignore
    right = lambda p1, p2: fmap(lambda p: p[1])(sequence(p1, p2))  # type: ignore
    assert left(letter, digit)("a4") == ("a", "")
    assert right(letter, digit)("a4") == ("4", "")

    alnum = either(letter, digit)  # type: ignore
    assert alnum("4a") == ("4", "a")
    assert alnum("a4") == ("a", "4")
    assert alnum("$4") is False

    assert maybe(digit)("456") == ("4", "56")
    assert maybe(digit)("abc") == (None, "abc")


if __name__ == "__main__":
    test_run()
