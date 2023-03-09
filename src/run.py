from typing import Callable, Literal, Tuple, Union


Pair = Union[Tuple[str, str], Literal[False]]
PairCallable = Callable[[str], Pair]


def shift(source: str) -> Pair:
    return bool(source) and (source[0], source[1:])


def nothing(source: str) -> Tuple[None, str]:
    return (None, "bar")


def sieve(predicate: Callable[[str], bool]) -> Callable[[PairCallable], PairCallable]:
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

    return sieve(f)


def member_of(values: str) -> Callable[[PairCallable], PairCallable]:
    def f(source: str) -> bool:
        return source in values

    return sieve(f)


def test_run() -> None:
    assert shift("bar") == ("b", "ar")
    assert shift("ar") == ("a", "r")
    assert shift("r") == ("r", "")
    assert shift("") is False

    assert nothing("bar") == (None, "bar")

    digit = sieve(str.isdigit)(shift)
    assert digit("456") == ("4", "56")
    assert sieve(str.isalpha)(shift)("456") is False

    assert literal(".")(shift)(".456") == (".", "456")
    assert literal(".")(shift)("45.6") is False

    assert member_of("02468")(digit)("456") == ("4", "56")
    assert member_of("02468")(digit)("345") is False


if __name__ == "__main__":
    test_run()
