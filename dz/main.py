import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class Parser:
    def __init__(self, text: str) -> None:
        self._tokens = self._tokenize(text)
        self._pos = 0
        self._constants = {}

    def _tokenize(self, text: str) -> list[tuple[str, str]]:
        """
        Разбивает входной текст на список токенов.

        :param text: Входной текст.
        :return: Список токенов в формате (ТИП, ЗНАЧЕНИЕ).
        """
        token_specification = [
            ("NUMBER", r"[+-]?\d+"),  # Числа
            ("STRING", r"q\((.*?)\)"),  # Строки
            ("ID", r"[A-Z_][A-Z_0-9]*"),  # Имена констант
            ("ASSIGN", r":="),  # Оператор присваивания
            ("SEMICOLON", r";"),  # Точка с запятой
            ("BEGIN", r"begin"),  # Начало блока словаря
            ("END", r"end"),  # Конец блока словаря
            ("IS", r"is"),  # Оператор объявления константы
            ("PIPE", r"\|"),  # Разделитель выражений
            ("PLUS", r"\+"),
            ("MINUS", r"-"),
            ("TIMES", r"\*"),
            ("LPAREN", r"\("),
            ("RPAREN", r"\)"),
            ("ORD", r"ord"),
            ("SKIP", r"[\s\n\t]+"),  # Пропуск пробелов
            ("MISMATCH", r"."),  # Любой другой символ
        ]
        tok_regex = "|".join(
            f"(?P<{pair[0]}>{pair[1]})" for pair in token_specification
        )
        tokens = []
        for mo in re.finditer(tok_regex, text):
            kind = mo.lastgroup
            value = mo.group()
            if kind == "SKIP":
                continue
            if kind == "MISMATCH":
                raise SyntaxError(f"Unexpected character: {value}")
            tokens.append((kind, value))
        return tokens

    def _peek(self) -> tuple[str, str] | None:
        """Возвращает следующий токен, не сдвигая позицию."""
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _consume(self, expected_kind: str) -> tuple[str, str] | None:
        """Потребляет следующий токен, если он соответствует ожидаемому типу."""
        token = self._peek()
        if token and token[0] == expected_kind:
            self._pos += 1
            return token
        return None

    def _expect(self, expected_kind: str) -> tuple[str, str]:
        """
        Ожидает и потребляет токен определенного типа.
        Вызывает ошибку, если тип не совпадает.
        """
        token = self._consume(expected_kind)
        if token:
            return token
        current_token = self._peek()
        raise SyntaxError(
            f"Expected {expected_kind} but got "
            f"{current_token[0] if current_token else 'EOF'}",
        )

    def parse(self) -> dict:
        """
        Основной метод парсинга.
        Парсит объявления констант и один основной словарь.
        """
        # На верхнем уровне могут быть объявления констант или один словарь
        while (
            self._peek()
            and self._peek()[0] == "ID"
            and self._pos + 1 < len(self._tokens)
            and self._tokens[self._pos + 1][0] == "IS"
        ):
            self._parse_constant_declaration()

        if self._peek() and self._peek()[0] == "BEGIN":
            return self._parse_dictionary()

        # Если словаря нет, возвращаем пустой объект
        # Это может произойти, если ввод содержит только объявления констант
        if self._pos == len(self._tokens) or (
            self._peek() and self._peek()[0] != "BEGIN"
        ):
            # Проверяем наличие необработанных токенов для большей строгости
            if self._pos < len(self._tokens):
                raise SyntaxError(
                    f"Unexpected token at end of input: {self._peek()}",
                )
            return {}

        raise SyntaxError(
            "Expected 'begin' to start a dictionary or constant declarations.",
        )

    def _parse_constant_declaration(self) -> None:
        """Парсит объявление константы."""
        name_token = self._expect("ID")
        self._expect("IS")
        value = self._parse_value()
        self._constants[name_token[1]] = value

    def _parse_value(self) -> Any:
        """Парсинг значения (число, строка, словарь, константа или выражение)."""
        token = self._peek()
        if not token:
            raise SyntaxError("Unexpected EOF while parsing value")

        token_kind = token[0]

        if token_kind == "NUMBER":
            self._pos += 1
            return int(token[1])
        if token_kind == "STRING":
            self._pos += 1
            return token[1][2:-1]  # Удаляем 'q(' и ')'
        if token_kind == "BEGIN":
            return self._parse_dictionary()
        if token_kind == "ID":
            if token[1] in self._constants:
                self._pos += 1
                return self._constants[token[1]]
            raise SyntaxError(f"Undefined constant: {token[1]}")
        if token_kind == "PIPE":
            return self._parse_expression()

        raise SyntaxError(f"Unexpected token when parsing value: {token}")

    def _parse_dictionary(self) -> dict:
        """Парсит блок словаря."""
        self._expect("BEGIN")
        result = {}
        while self._peek() and self._peek()[0] != "END":
            name_token = self._expect("ID")
            self._expect("ASSIGN")
            value = self._parse_value()
            result[name_token[1]] = value
            self._expect("SEMICOLON")
        self._expect("END")
        return result

    def _parse_expression(self) -> Any:
        """Парсит константное выражение, заключенное в '|'."""
        self._expect("PIPE")
        value = self._parse_additive_expression()
        self._expect("PIPE")
        return value

    def _parse_additive_expression(self) -> Any:
        """Парсит выражения со сложением и вычитанием."""
        value = self._parse_multiplicative_expression()
        while self._peek() and self._peek()[0] in ("PLUS", "MINUS"):
            op = self._consume(self._peek()[0])
            term = self._parse_multiplicative_expression()

            is_str = isinstance(value, str) and isinstance(term, str)
            is_int = isinstance(value, int) and isinstance(term, int)

            if op[0] == "PLUS" and (is_str or is_int):
                value += term
            elif op[0] == "MINUS" and is_int:
                value -= term
            else:
                raise TypeError(f"Unsupported operand types for {op[1]}")
        return value

    def _parse_multiplicative_expression(self) -> Any:
        """Парсит выражения с умножением."""
        value = self._parse_factor()
        while self._peek() and self._peek()[0] == "TIMES":
            self._consume("TIMES")
            factor = self._parse_factor()

            is_int_int = isinstance(value, int) and isinstance(factor, int)
            is_str_int = isinstance(value, str) and isinstance(factor, int)
            is_int_str = isinstance(value, int) and isinstance(factor, str)

            if is_int_int or is_str_int:
                value *= factor
            elif is_int_str:
                value = factor * value
            else:
                raise TypeError("Unsupported operand types for *")
        return value

    def _parse_factor(self) -> Any:
        """Парсинг фактора выражения (число, строка, константа, ord(), подвыражение)."""
        if self._consume("LPAREN"):
            value = self._parse_additive_expression()
            self._expect("RPAREN")
            return value
        if self._peek()[0] == "STRING":
            return self._consume("STRING")[1][2:-1]
        if self._peek()[0] == "NUMBER":
            return int(self._consume("NUMBER")[1])
        if self._peek()[0] == "ID":
            name = self._consume("ID")[1]
            if name in self._constants:
                return self._constants[name]
            raise SyntaxError(f"Undefined constant in expression: {name}")
        if self._peek()[0] == "ORD":
            return self._parse_ord()
        raise SyntaxError(f"Unexpected token in expression factor: {self._peek()}")

    def _parse_ord(self) -> int:
        """Парсит вызов функции ord()."""
        self._expect("ORD")
        self._expect("LPAREN")

        token = self._peek()
        if token[0] == "STRING":
            value = self._consume("STRING")[1][2:-1]
        elif token[0] == "ID":
            const_name = self._consume("ID")[1]
            if const_name in self._constants:
                value = self._constants[const_name]
            else:
                raise SyntaxError(f"Undefined constant: {const_name}")
        else:
            raise SyntaxError(
                "ord() argument must be a string literal or a constant.",
            )

        if not isinstance(value, str) or len(value) != 1:
            raise SyntaxError("ord() expects a single character string")

        self._expect("RPAREN")
        return ord(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Парсер учебного конфигурационного языка в JSON",
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Путь для выходного JSON файла",
    )
    args = parser.parse_args()

    try:
        input_text = sys.stdin.read()
        parser = Parser(input_text)
        result = parser.parse()
        if args.output:
            with Path(args.output).open("w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
        else:
            print(json.dumps(result, indent=4, ensure_ascii=False))
    except (SyntaxError, TypeError) as e:
        sys.stderr.write(f"Syntax error: {e}\n")
        sys.exit(1)
    except OSError as e:
        sys.stderr.write(f"File operation error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
