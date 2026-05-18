from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Dict, Optional
from collections import ChainMap
import sys
import argparse


@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int


class LangError(Exception):
    pass


class LexerError(LangError):
    def __init__(self, message: str, line: int = 0, column: int = 0) -> None:
        super().__init__(f"{message} (line {line}, col {column})")


class ParserError(LangError):
    def __init__(self, message: str, line: int = 0, column: int = 0) -> None:
        super().__init__(f"{message} (line {line}, col {column})")


class RuntimeLangError(LangError):
    pass


def format_error(err: Exception) -> str:
    # Mensaje legible para el usuario; preserva la traza interna si es inesperado.
    if isinstance(err, LangError):
        return str(err)
    return f"Error inesperado: {err}"


# AST basicos (faltan algunos)
# (Abstract Syntax Tree): representación en memoria del programa como nodos
# El AST es independiente del texto original y sirve como entrada para el intérprete-compilador
@dataclass
class Number:
    value: float


@dataclass
class String:
    value: str


@dataclass
class Bool:
    value: bool


@dataclass
class Var:
    name: str


@dataclass
class UnaryOp:
    op: str
    expr: Any


@dataclass
class BinOp:
    left: Any
    op: str
    right: Any

@dataclass
class Assign:
    name: str
    expr: Any


@dataclass
class PrintStmt:
    expr: Any


@dataclass
class Program:
    statements: List[Any]


@dataclass
class IfStmt:
    cond: Any
    then_branch: Program
    else_branch: Optional[Program]


@dataclass
class WhileStmt:
    cond: Any
    body: Program


@dataclass
class FuncDef:
    name: str
    params: List[str]
    body: Program


@dataclass
class ReturnStmt:
    expr: Optional[Any]


@dataclass
class Call:
    name: str
    args: List[Any]


@dataclass
class ListLiteral:
    items: List[Any]


@dataclass
class DictLiteral:
    items: List[Any]  # list of (key, value) pairs


@dataclass
class Index:
    target: Any
    index: Any


# Lexer
# Convierte el texto fuente en una lista de tokens. Ejemplo: a = 1 + 2 → tokens IDENT(a), '=', NUMBER(1), '+', NUMBER(2). 
# Detecta numeros, identificadores, cadenas, simbolos y posicion (linea/columna) para errores.


class Lexer:
    def __init__(self, source: str) -> None:
        # Guardamos el texto original y un cursor para avanzar caracter por caracter.
        self.source = source
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        # Recorremos el texto y lo convertimos en tokens que el parser pueda entender.
        tokens: List[Token] = []

        while self.index < len(self.source):
            ch = self.source[self.index]

            if ch in " \t\r":
                # Espacios y tabulaciones no cambian el significado del programa.
                self._advance()
                continue

            if ch == "\n":
                # Conservamos saltos de linea para dar mejores mensajes de error.
                tokens.append(Token("NEWLINE", "\n", self.line, self.column))
                self._advance(newline=True)
                continue

            if ch.isdigit():
                tokens.append(self._number())
                continue

            if ch == '"':
                tokens.append(self._string())
                continue

            if ch.isalpha() or ch == "_":
                tokens.append(self._identifier())
                continue

            # multi-char operators: ==, !=, <=, >=
            next_ch = self.source[self.index + 1] if self.index + 1 < len(self.source) else None
            if ch == "=" and next_ch == "=":
                tokens.append(Token("==", "==", self.line, self.column))
                self._advance()
                self._advance()
                continue
            if ch == "!" and next_ch == "=":
                tokens.append(Token("!=", "!=", self.line, self.column))
                self._advance()
                self._advance()
                continue
            if ch == "<" and next_ch == "=":
                tokens.append(Token("<=", "<=", self.line, self.column))
                self._advance()
                self._advance()
                continue
            if ch == ">" and next_ch == "=":
                tokens.append(Token(">=", ">=", self.line, self.column))
                self._advance()
                self._advance()
                continue

            if ch in "+-*/()=<>!{}[],:":
                # Los simbolos simples se convierten en un token de un solo caracter.
                tokens.append(Token(ch, ch, self.line, self.column))
                self._advance()
                continue

            if ch == ";":
                tokens.append(Token("SEMI", ";", self.line, self.column))
                self._advance()
                continue

            raise LexerError(f"Caracter inesperado {ch!r}.", self.line, self.column)

        tokens.append(Token("EOF", "", self.line, self.column))
        return tokens

    def _advance(self, newline: bool = False) -> None:
        # Mover el cursor actualizando linea y columna para ubicar errores.
        self.index += 1
        if newline:
            self.line += 1
            self.column = 1
        else:
            self.column += 1

    def _number(self) -> Token:
        # Leemos un numero entero o decimal hasta que aparezca un caracter invalido.
        start_line = self.line
        start_column = self.column
        start = self.index
        has_dot = False

        while self.index < len(self.source):
            ch = self.source[self.index]
            if ch == ".":
                if has_dot:
                    break
                has_dot = True
                self._advance()
            elif ch.isdigit():
                self._advance()
            else:
                break

        return Token("NUMBER", self.source[start:self.index], start_line, start_column)

    def _string(self) -> Token:
        # Lee una cadena entre comillas dobles, permite \" para comillas dentro.
        start_line = self.line
        start_column = self.column
        self._advance()  # abrir comilla
        start = self.index
        value_chars: List[str] = []
        while self.index < len(self.source):
            ch = self.source[self.index]
            if ch == "\\":
                # escape simple
                self._advance()
                if self.index < len(self.source):
                    esc = self.source[self.index]
                    if esc == '"':
                        value_chars.append('"')
                    elif esc == 'n':
                        value_chars.append('\n')
                    else:
                        value_chars.append(esc)
                    self._advance()
                    continue
                break
            if ch == '"':
                # cerrar
                self._advance()
                break
            value_chars.append(ch)
            self._advance()

        return Token("STRING", "".join(value_chars), start_line, start_column)

    def _identifier(self) -> Token:
        # Leemos nombres de variables o palabras reservadas como print.
        start_line = self.line
        start_column = self.column
        start = self.index

        while self.index < len(self.source):
            ch = self.source[self.index]
            if ch.isalnum() or ch == "_":
                self._advance()
            else:
                break

        value = self.source[start:self.index]
        kw = value.lower()
        # palabras reservadas (aceptamos ingles/español cuando tiene sentido)
        if kw == "print":
            return Token("PRINT", value, start_line, start_column)
        if kw == "if":
            return Token("IF", value, start_line, start_column)
        if kw == "else":
            return Token("ELSE", value, start_line, start_column)
        if kw == "while":
            return Token("WHILE", value, start_line, start_column)
        if kw == "def":
            return Token("DEF", value, start_line, start_column)
        if kw == "return":
            return Token("RETURN", value, start_line, start_column)
        if kw in {"true", "false", "verdadero", "falso"}:
            return Token("BOOL", kw, start_line, start_column)
        if kw in {"and", "or", "not", "y", "o", "no"}:
            mapping = {"and": "AND", "or": "OR", "not": "NOT", "y": "AND", "o": "OR", "no": "NOT"}
            return Token(mapping[kw], value, start_line, start_column)
        return Token("IDENT", value, start_line, start_column)

# Parser
# Consume los tokens y construye una estructura de datos jerarquica. Traduce la secuencia plana de tokens a nodos con significado: 
# p. ej. Assign(name='a', expr=BinOp(Number(1), '+', Number(2))). Tambien valida la gramatica y produce errores si la sintaxis es invalida.



class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        # El parser no mira texto crudo; solo consume tokens ya clasificados.
        self.tokens = tokens
        self.index = 0

    def parse(self) -> Program:
        # El programa es una lista de sentencias separadas por saltos de linea o ';'.
        statements: List[Any] = []

        self._skip_separators()
        while not self._check("EOF"):
            statements.append(self._statement())
            self._skip_separators()

        self._expect("EOF")
        return Program(statements)

    def _statement(self) -> Any:
        # Una sentencia puede ser print, una asignacion o una expresion simple.
        if self._match("IF"):
            # if (cond) { ... } [else { ... }]
            if self._match("("):
                cond = self._expression()
                self._expect(")")
            else:
                cond = self._expression()
            then_branch = self._parse_block()
            else_branch = None
            if self._match("ELSE"):
                else_branch = self._parse_block()
            return IfStmt(cond, then_branch, else_branch)

        if self._match("WHILE"):
            # while (cond) { ... }
            if self._match("("):
                cond = self._expression()
                self._expect(")")
            else:
                cond = self._expression()
            body = self._parse_block()
            return WhileStmt(cond, body)

        if self._match("PRINT"):
            expr = self._expression()
            return PrintStmt(expr)

        if self._match("DEF"):
            # def name(param1, param2) { ... }
            name_token = self._expect("IDENT")
            name = name_token.value
            self._expect("(")
            params: List[str] = []
            if not self._check(")"):
                p = self._expect("IDENT")
                params.append(p.value)
                while self._match(","):
                    p = self._expect("IDENT")
                    params.append(p.value)
            self._expect(")")
            body = self._parse_block()
            return FuncDef(name, params, body)

        if self._match("RETURN"):
            expr = self._expression()
            return ReturnStmt(expr)

        if self._check("IDENT") and self._peek(1).kind == "=":
            name = self._advance().value
            self._advance()  # =
            expr = self._expression()
            return Assign(name, expr)

        return self._expression()

    def _expression(self) -> Any:
        # Expresion: soporta aritmetica, comparaciones y operadores logicos basicos.
        node = self._term()

        # suma/resta
        while self._match("+", "-"):
            op = self._previous().kind
            right = self._term()
            node = BinOp(node, op, right)

        # comparadores (se aplican despues de la aritmetica)
        while self._match("==", "!=", "<", ">", "<=", ">="):
            op = self._previous().kind
            right = self._term()
            node = BinOp(node, op, right)

        # operadores logicos (and/or)
        while self._match("AND", "OR"):
            op = self._previous().kind
            right = self._term()
            node = BinOp(node, op, right)

        return node

    def _term(self) -> Any:
        # Multiplicacion y division tienen mas prioridad que + y -.
        node = self._factor()

        while self._match("*", "/"):
            op = self._previous().kind
            right = self._factor()
            node = BinOp(node, op, right)

        return node

    def _factor(self) -> Any:
        # Un factor puede ser numero, variable, parentesis o signo unario.
        if self._match("+"):
            return self._factor()

        if self._match("-"):
            return UnaryOp("-", self._factor())

        if self._match("NOT"):
            return UnaryOp("NOT", self._factor())

        if self._match("NUMBER"):
            return Number(float(self._previous().value))

        if self._match("STRING"):
            return String(self._previous().value)

        if self._match("BOOL"):
            val = self._previous().value
            v = val.lower() in {"true", "verdadero"}
            return Bool(v)

        # Lista literal: [a, b, c]
        if self._match("["):
            items: List[Any] = []
            if not self._check("]"):
                items.append(self._expression())
                while self._match(","):
                    items.append(self._expression())
            self._expect("]")
            return ListLiteral(items)

        # Dict literal: { "k": v, ... }
        if self._match("{"):
            pairs: List[Any] = []
            if not self._check("}"):
                # key can be STRING, IDENT, or NUMBER
                key = None
                if self._match("STRING"):
                    key = self._previous().value
                elif self._match("IDENT"):
                    key = self._previous().value
                elif self._match("NUMBER"):
                    key = self._previous().value
                else:
                    raise ParserError("Clave de diccionario debe ser string, identificador o número.", self._peek().line, self._peek().column)
                self._expect(":")
                val = self._expression()
                pairs.append((key, val))
                while self._match(","):
                    if self._match("STRING"):
                        key = self._previous().value
                    elif self._match("IDENT"):
                        key = self._previous().value
                    elif self._match("NUMBER"):
                        key = self._previous().value
                    else:
                        raise ParserError("Clave de diccionario debe ser string, identificador o número.", self._peek().line, self._peek().column)
                    self._expect(":")
                    val = self._expression()
                    pairs.append((key, val))
            self._expect("}")
            # Distinguimos bloque (usado en statement) de literal por el contexto: aqui devolvemos DictLiteral
            return DictLiteral(pairs)

        # Llamada a funcion si viene un IDENT seguido de '('
        if self._check("IDENT") and self._peek(1).kind == "(":
            name = self._advance().value
            self._advance()  # consume '('
            args: List[Any] = []
            if not self._check(")"):
                args.append(self._expression())
                while self._match(","):
                    args.append(self._expression())
            self._expect(")")
            return Call(name, args)

        if self._match("IDENT"):
            return Var(self._previous().value)

        if self._match("("):
            expr = self._expression()
            self._expect(")")
            return expr

        # Permitir acceso por indice despues de un primary: e.g. a[0]
        # (Handled by wrapping primary above and allowing post-index parse isn't trivial here,
        # so instead support index syntax by parsing primary then applying indices in a loop.)

        token = self._peek()
        raise ParserError(self._friendly_message(token), token.line, token.column)

    def _friendly_message(self, token: Token) -> str:
        # Traducimos errores tecnicos a mensajes mas directos para el usuario.
        if token.kind == "EOF":
            return "La expresion termino antes de tiempo. Quizas falta un numero, variable o parentesis de cierre."
        if token.kind == ")":
            return "Hay un parentesis de cierre sin apertura previa."
        if token.kind in {"+", "-", "*", "/", "="}:
            return f"No se esperaba el operador {token.value!r} aqui."
        return f"Token inesperado {token.value!r}."

    def _skip_separators(self) -> None:
        # Ignoramos separadores para permitir varias lineas o ';' al final.
        while self._match("NEWLINE", "SEMI"):
            pass

    def _parse_block(self) -> Program:
        # Parseamos un bloque entre llaves { ... } que contiene multiples sentencias.
        self._expect("{")
        stmts: List[Any] = []
        self._skip_separators()
        while not self._check("}"):
            stmts.append(self._statement())
            self._skip_separators()
        self._expect("}")
        return Program(stmts)

    def _match(self, *kinds: str) -> bool:
        for kind in kinds:
            if self._check(kind):
                self._advance()
                return True
        return False

    def _expect(self, kind: str) -> Token:
        if not self._check(kind):
            token = self._peek()
            raise ParserError(f"Se esperaba {kind} y llego {token.kind}.", token.line, token.column)
        return self._advance()

    def _check(self, kind: str) -> bool:
        return self._peek().kind == kind

    def _peek(self, offset: int = 0) -> Token:
        index = min(self.index + offset, len(self.tokens) - 1)
        return self.tokens[index]

    def _advance(self) -> Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def _previous(self) -> Token:
        return self.tokens[self.index - 1]


# -----------------------------
# Interprete
# -----------------------------

class Interpreter:
    def __init__(self) -> None:
        # La tabla de simbolos guarda el valor actual de cada variable.
        self.env: Dict[str, float] = {}

    def run(self, program: Program) -> Optional[float]:
        # Ejecutamos todas las sentencias en orden y devolvemos el ultimo valor.
        last_value: Optional[float] = None

        for stmt in program.statements:
            last_value = self._eval(stmt)

        return last_value

    def _eval(self, node: Any) -> Optional[float]:
        # Cada tipo de nodo se interpreta de forma distinta.
        if isinstance(node, Number):
            return node.value

        if isinstance(node, String):
            return node.value

        if isinstance(node, Bool):
            return node.value

        if isinstance(node, IfStmt):
            cond = self._eval(node.cond)
            if cond:
                for s in node.then_branch.statements:
                    self._eval(s)
            elif node.else_branch is not None:
                for s in node.else_branch.statements:
                    self._eval(s)
            return None

        if isinstance(node, WhileStmt):
            # Ejecuta el body mientras la condicion sea verdadera.
            # Cuidado con bucles infinitos.
            while bool(self._eval(node.cond)):
                for s in node.body.statements:
                    self._eval(s)
            return None

        if isinstance(node, FuncDef):
            # Registramos la funcion en la tabla de funciones.
            if not hasattr(self, "functions"):
                self.functions: Dict[str, FuncDef] = {}
            self.functions[node.name] = node
            return None

        if isinstance(node, ReturnStmt):
            # El return salta fuera de la ejecucion normal con una excepcion controlada.
            val = None
            if node.expr is not None:
                val = self._eval(node.expr)
            raise ReturnException(val)

        if isinstance(node, Call):
            # Buscar la definicion de la funcion y ejecutar en un entorno local.
            if not hasattr(self, "functions") or node.name not in self.functions:
                raise RuntimeLangError(f"Funcion {node.name!r} no definida.")
            f = self.functions[node.name]
            # evaluar argumentos
            args = [self._eval(a) for a in node.args]
            # preparar entorno local que encadena con el global
            prev_env = self.env
            local = {p: v for p, v in zip(f.params, args)}
            self.env = ChainMap(local, prev_env)
            try:
                for s in f.body.statements:
                    self._eval(s)
            except ReturnException as r:
                return r.value
            finally:
                self.env = prev_env
            return None

        if isinstance(node, Var):
            # Si la variable no existe, frenamos con un mensaje entendible.
            if node.name not in self.env:
                raise RuntimeLangError(
                    f"La variable {node.name!r} no existe. Definela antes de usarla."
                )
            return self.env[node.name]

        if isinstance(node, UnaryOp):
            value = self._eval(node.expr)
            assert value is not None
            if node.op == "-":
                return -value
            return value

        if isinstance(node, BinOp):
            # Evaluamos primero los dos lados y luego aplicamos el operador.
            left = self._eval(node.left)
            right = self._eval(node.right)
            assert left is not None and right is not None

            if node.op == "+":
                return left + right
            if node.op == "-":
                return left - right
            if node.op == "*":
                return left * right
            if node.op == "/":
                # La division entre cero no es valida, asi que la bloqueamos.
                if right == 0:
                    raise RuntimeLangError("Division entre cero. Revisa el divisor.")
                return left / right

            # comparaciones
            if node.op == "==":
                return left == right
            if node.op == "!=":
                return left != right
            if node.op == "<":
                return left < right
            if node.op == ">":
                return left > right
            if node.op == "<=":
                return left <= right
            if node.op == ">=":
                return left >= right

            # logica booleana (AND/OR) - tratamos los operandos como booleanos
            if node.op == "AND":
                return bool(left) and bool(right)
            if node.op == "OR":
                return bool(left) or bool(right)

            raise RuntimeLangError(f"Operador desconocido {node.op!r}.")

        if isinstance(node, Assign):
            # Guardamos el resultado en la tabla de variables.
            value = self._eval(node.expr)
            assert value is not None
            self.env[node.name] = value
            return value

        if isinstance(node, PrintStmt):
            # print no solo calcula: tambien muestra el resultado por pantalla.
            value = self._eval(node.expr)
            print(value)
            return value

        if isinstance(node, ListLiteral):
            return [self._eval(i) for i in node.items]

        if isinstance(node, DictLiteral):
            d = {}
            for k, v in node.items:
                d[k] = self._eval(v)
            return d

        if isinstance(node, Index):
            target = self._eval(node.target)
            idx = self._eval(node.index)
            try:
                return target[int(idx)]
            except Exception as e:
                raise RuntimeLangError(f"Index error: {e}")

        raise RuntimeLangError("Nodo AST desconocido.")

class ReturnException(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


# -----------------------------
# Compilador simple
# -----------------------------

class Compiler:
    def compile(self, program: Program) -> List[str]:
        # En vez de ejecutar, generamos instrucciones de un bytecode simple.
        instructions: List[str] = []

        for stmt in program.statements:
            self._emit(stmt, instructions)

        return instructions

    def _emit(self, node: Any, instructions: List[str]) -> None:
        # Recorremos el AST y lo traducimos instruccion por instruccion.
        if isinstance(node, Number):
            instructions.append(f"PUSH {node.value}")
            return

        if isinstance(node, Var):
            instructions.append(f"LOAD {node.name}")
            return

        if isinstance(node, UnaryOp):
            self._emit(node.expr, instructions)
            instructions.append("NEG")
            return

        if isinstance(node, BinOp):
            # Primero generamos codigo para los operandos, luego para la operacion.
            self._emit(node.left, instructions)
            self._emit(node.right, instructions)
            op_map = {
                "+": "ADD",
                "-": "SUB",
                "*": "MUL",
                "/": "DIV",
            }
            instructions.append(op_map[node.op])
            return

        if isinstance(node, Assign):
            # Guardamos el valor y luego lo dejamos listo en la pila si hace falta.
            self._emit(node.expr, instructions)
            instructions.append(f"STORE {node.name}")
            return

        if isinstance(node, PrintStmt):
            self._emit(node.expr, instructions)
            instructions.append("PRINT")
            return

        raise RuntimeLangError("No se pudo compilar el nodo.")


# -----------------------------
# Utilidades
# -----------------------------

def process_source(source: str, mode: str = "interpret", anti_frustration: bool = True) -> Any:
    # Esta funcion conecta todo: lexer -> parser -> interprete o compilador.
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()

        if mode == "compile":
            return Compiler().compile(program)

        return Interpreter().run(program)

    except LangError as error:
        # Si el modo anti-frustracion esta activo, convertimos el error en un mensaje claro.
        if anti_frustration:
            raise SystemExit(format_error(error)) from error
        raise


def repl() -> None:
    # La REPL permite probar el lenguaje sin crear archivos.
    interpreter = Interpreter()
    print("Mini interprete/compilador. Escribe 'exit' para salir.")
    print("Comandos: print, asignacion con =, expresiones aritmeticas.")

    while True:
        try:
            source = input(">>> ").strip()
        except EOFError:
            break

        if source.lower() in {"exit", "quit"}:
            break

        if not source:
            continue

        try:
            if source.startswith("compile "):
                # Si el usuario escribe 'compile ...', mostramos instrucciones en vez de ejecutar.
                program_text = source[len("compile "):]
                tokens = Lexer(program_text).tokenize()
                program = Parser(tokens).parse()
                instructions = Compiler().compile(program)
                print("\n".join(instructions))
            else:
                # En modo normal usamos el interprete con estado persistente.
                tokens = Lexer(source).tokenize()
                program = Parser(tokens).parse()
                result = interpreter.run(program)
                if result is not None:
                    print(result)
        except LangError as error:
            # En la consola mostramos el error sin detener la REPL.
            print(format_error(error))


def main() -> None:
    # Definimos la interfaz de linea de comandos del programa.
    parser = argparse.ArgumentParser(
        description="Mini interprete/compilador con modo anti-frustracion."
    )
    parser.add_argument("source", nargs="?", help="Codigo a ejecutar")
    parser.add_argument(
        "--mode",
        choices=("interpret", "compile"),
        default="interpret",
        help="Modo de ejecucion",
    )
    parser.add_argument(
        "--no-af",
        action="store_true",
        help="Desactiva mensajes anti-frustracion",
    )
    parser.add_argument(
        "--repl",
        action="store_true",
        help="Abre una consola interactiva",
    )

    args = parser.parse_args()

    if args.repl or args.source is None:
        # Sin argumento de entrada abrimos la consola interactiva.
        repl()
        return

    # Ejecutamos el texto recibido desde la terminal.
    result = process_source(
        args.source,
        mode=args.mode,
        anti_frustration=not args.no_af,
    )

    if args.mode == "compile":
        # En compilacion imprimimos cada instruccion en una linea.
        print("\n".join(result))
    else:
        # En interpretacion solo mostramos el ultimo resultado si existe.
        if result is not None:
            print(result)


if __name__ == "__main__":
    main()
    