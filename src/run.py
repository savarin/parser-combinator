from typing import Callable, List, Literal, Tuple, Union


Pair = Union[Tuple[str, str], Literal[False]]
PairCallable = Callable[[str], Pair]

PairList = Union[Tuple[List[str], str], Literal[False]]
PairListCallable = Callable[[str], PairList]


def shift(source: str) -> Pair:
    return bool(source) and (source[0], source[1:])


def nothing(source: str) -> Tuple[None, str]:
    return (None, "bar")


def sift(predicate: Callable[[str], bool]) -> Callable[[PairCallable], PairCallable]:
    def f(parser: PairCallable) -> PairCallable:
        def g(source: str) -> Pair:
            def h(result: Pair) -> Pair:
                return result and predicate(result[0]) and result

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
                return result and (func(result[0]), result[1])

            return h(parser(source))

        return g

    return f


def one_or_more(parser: Callable[[str], Pair]) -> Callable[[str], PairList]:
    def parse(source: str) -> PairList:
        result: List[str] = []

        while True:
            pair = parser(source)

            if not pair:
                break

            value, source = pair
            result.append(value)

        return bool(result) and (result, source)

    return parse


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


if __name__ == "__main__":
    test_run()
