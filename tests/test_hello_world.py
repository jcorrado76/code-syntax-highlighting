from code_syntax_highlighting.hello_world import hello_world


def test_hello_world() -> None:
    assert hello_world() == "hello world"
