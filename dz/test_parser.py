import json
import subprocess
import sys
from pathlib import Path

import pytest


def run_parser(input_data: str, output_file: Path) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S603
        [sys.executable, "main.py", f"--output={output_file}"],
        check=False,
        input=input_data,
        capture_output=True,
        text=True,
        shell=False,
    )


def run_and_check(input_data: str, tmp_path: Path, expected_data: dict) -> None:
    output_file = tmp_path / "output.json"
    process = run_parser(input_data, output_file)
    assert process.returncode == 0
    with output_file.open() as f:
        data = json.load(f)
    assert data == expected_data


def run_and_check_error(input_data: str, tmp_path: Path, expected_error: str) -> None:
    output_file = tmp_path / "error_output.json"
    process = run_parser(input_data, output_file)
    assert process.returncode != 0
    assert expected_error in process.stderr
    assert not output_file.exists()


def test_simple_dictionary(tmp_path: Path) -> None:
    input_data = """
    begin
        NAME := q(John);
        AGE := 25;
    end
    """
    expected_data = {"NAME": "John", "AGE": 25}
    run_and_check(input_data, tmp_path, expected_data)


def test_nested_dictionary(tmp_path: Path) -> None:
    input_data = """
    begin
        USER := begin
            NAME := q(Alice);
            ID := 1;
            XP := 2;
            SETTINGS := begin
                IQ := 70;
                ONLINE := begin
                    ONLINE := q(false);
                    SHOW := q(true);
                end;
            end;
        end;
        ENABLED := q(true);
    end
    """
    expected_data = {
        "USER": {
            "NAME": "Alice",
            "ID": 1,
            "XP": 2,
            "SETTINGS": {
                "IQ": 70,
                "ONLINE": {
                    "ONLINE": "false",
                    "SHOW": "true",
                },
            },
        },
        "ENABLED": "true",
    }
    run_and_check(input_data, tmp_path, expected_data)


def test_constants(tmp_path: Path) -> None:
    input_data = """
    PORT is 8080
    HOST is q(localhost)
    begin
        HOSTNAME := HOST;
        PORTNUMBER := PORT;
    end
    """
    expected_data = {"HOSTNAME": "localhost", "PORTNUMBER": 8080}
    run_and_check(input_data, tmp_path, expected_data)


def test_constant_expressions(tmp_path: Path) -> None:
    input_data = """
    BASE_PORT is 8000
    OFFSET is 80
    begin
        API_PORT := |BASE_PORT + OFFSET|;
        ADMIN_PORT := |BASE_PORT - 10|;
        MULT_PORT := |OFFSET * 2|;
    end
    """
    expected_data = {"API_PORT": 8080, "ADMIN_PORT": 7990, "MULT_PORT": 160}
    run_and_check(input_data, tmp_path, expected_data)


def test_ord_function(tmp_path: Path) -> None:
    input_data = """
    CHAR is q(A)
    begin
        ASCII_VALUE := |ord(CHAR)|;
    end
    """
    expected_data = {"ASCII_VALUE": 65}
    run_and_check(input_data, tmp_path, expected_data)


def test_string_concatenation(tmp_path: Path) -> None:
    input_data = """
    STR1 is q(hello)
    STR2 is q( world)
    begin
        GREETING := |STR1 + STR2|;
    end
    """
    expected_data = {"GREETING": "hello world"}
    run_and_check(input_data, tmp_path, expected_data)


def test_string_multiplication(tmp_path: Path) -> None:
    input_data = """
    begin
        REPEATED := |q(a) * 5|;
    end
    """
    expected_data = {"REPEATED": "aaaaa"}
    run_and_check(input_data, tmp_path, expected_data)


@pytest.mark.parametrize(
    "input_data, expected_data",
    [
        (
            """
            begin
                A := begin
                    B := begin
                        C := begin
                            D := 1;
                        end;
                    end;
                end;
            end
            """,
            {"A": {"B": {"C": {"D": 1}}}},
        ),
        (
            """
            A is 1
            A is 2
            begin
                B := A;
            end
            """,
            {"B": 2},
        ),
        (
            """
            A is 10
            B is 2
            begin
                C := |(A + B) * 2 - 4|;
            end
            """,
            {"C": 20},
        ),
        ("begin end", {}),
        ("", {}),
        (
            """
            CHAR is q(()
            begin
                A := |ord(CHAR)|;
            end
            """,
            {"A": 40},
        ),
    ],
)
def test_advanced_features(
    input_data: str,
    expected_data: dict,
    tmp_path: Path,
) -> None:
    run_and_check(input_data, tmp_path, expected_data)


@pytest.mark.parametrize(
    "input_data, expected_error",
    [
        ("begin NAME := q(test) end", "Syntax error: Expected SEMICOLON but got END"),
        (
            "begin\n    RESULT := |q(a) + 1|;\nend",
            "Syntax error: Unsupported operand types for +",
        ),
        ("begin @ end", "Syntax error: Unexpected character: @"),
        ("begin NAME := q(value);", "Syntax error: Expected END but got EOF"),
        (
            "NAME := q(value); end",
            "Syntax error: Unexpected token at end of input: ('ID', 'NAME')",
        ),
        ("begin NAME := q(value) end", "Syntax error: Expected SEMICOLON but got END"),
        ("begin NAME q(value); end", "Syntax error: Expected ASSIGN but got STRING"),
        ("begin name := q(value); end", "Syntax error: Unexpected character: n"),
        ("begin NAME := q(hello; end", "Syntax error: Unexpected character: q"),
        ("begin NAME := |1+2; end", "Syntax error: Expected PIPE but got NUMBER"),
        ("begin NAME := UNKNOWN; end", "Syntax error: Undefined constant: UNKNOWN"),
        (
            "begin NAME := |ord()|; end",
            "Syntax error: ord() argument must be a string literal or a constant.",
        ),
        (
            "begin NAME := |ord(q(AB))|; end",
            "Syntax error: ord() expects a single character string",
        ),
        (
            "begin NAME := |1 ++ 2|; end",
            "Syntax error: Unexpected token in expression factor",
        ),
        ("begin A := 1; # comment end", "Syntax error: Unexpected character: #"),
        ("begin A := 1; // comment end", "Syntax error: Unexpected character: /"),
        (
            "begin A := q(a()|;b); end",
            "Syntax error: Unexpected character: b",
        ),
        (
            "begin A := q(a\\)); end",
            "Syntax error: Expected SEMICOLON but got RPAREN",
        ),
    ],
)
def test_invalid_syntax(input_data: str, expected_error: str, tmp_path: Path) -> None:
    run_and_check_error(input_data, tmp_path, expected_error)
