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
            result += value

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
            result += value

        return (result, source)

    return parse


def either(left: PairListCallable, right: PairListCallable) -> PairListCallable:
    def parse(source: str) -> PairList:
        return left(source) or right(source)

    return parse


def maybe(parser: PairListCallable) -> PairListCallable:
    return either(parser, nothing)


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


if __name__ == "__main__":
    test_run()
