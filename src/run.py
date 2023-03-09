from typing import Tuple, Union


def shift(source: str) -> Union[Tuple[str, str], bool]:
    return bool(source) and (source[0], source[1:])


def nothing(source: str) -> Tuple[None, str]:
    return (None, "bar")


def test_run() -> None:
    assert shift("bar") == ("b", "ar")
    assert shift("ar") == ("a", "r")
    assert shift("r") == ("r", "")
    assert shift("") is False

    assert nothing("bar") == (None, "bar")


if __name__ == "__main__":
    test_run()
