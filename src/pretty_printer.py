from decimal import Decimal

COMPARISONS = ("==", "!=", "<", "<=", ">", ">=")
CALL_FORMS = {"length": "length", "head": "head", "tail": "tail", "copy": "copy",
              "type_query": "type", "string_conversion": "string",
              "number_conversion": "number", "boolean_conversion": "boolean"}
ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\t": "\\t", "\r": "\\r"}
INDENT = "    "


def quote(text):
    return '"' + "".join(ESCAPES.get(character, character) for character in text) + '"'


def number(value):
    text = repr(value)
    if type(value) is float and "e" in text:
        text = format(Decimal(text), "f")
        if "." not in text:
            text += ".0"
    return text


def block(node, depth):
    if not node["statements"]:
        return "{}"
    lines = [INDENT * (depth + 1) + statement(item, depth + 1) + ";" for item in node["statements"]]
    return "{\n" + "\n".join(lines) + "\n" + INDENT * depth + "}"


def statement(node, depth):
    tag = node["tag"]
    if tag == "print":
        return f"print({expression(node['expression'], 0, depth)})"
    if tag == "exit":
        if node["expression"] is None:
            return "exit()"
        return f"exit({expression(node['expression'], 0, depth)})"
    if tag == "assert":
        return f"assert {expression(node['expression'], 0, depth)}, {quote(node['explanation'])}"
    if tag == "set":
        return f"set {node['name']} = {expression(node['expression'], 0, depth)}"
    if tag == "return":
        if node["expression"] is None:
            return "return"
        return f"return {expression(node['expression'], 0, depth)}"
    if tag in ("break", "continue"):
        return tag
    if tag == "if":
        text = f"if ({expression(node['condition'], 0, depth)}) {block(node['then'], depth)}"
        if node["else"] is not None:
            text += f" else {block(node['else'], depth)}"
        return text
    if tag == "while":
        return f"while ({expression(node['condition'], 0, depth)}) {block(node['body'], depth)}"
    return expression(node, 0, depth)


def expression(node, minimum, depth):
    def sub(child, level):
        return expression(child, level, depth)

    tag = node["tag"]
    level = 9
    if tag == "assign":
        level = 0
        text = f"{sub(node['target'], 8)} = {sub(node['expression'], 0)}"
    elif tag in ("or", "and"):
        level = 1 if tag == "or" else 2
        text = f"{sub(node['left'], level)} {tag} {sub(node['right'], level + 1)}"
    elif tag == "not":
        level = 3
        text = f"not {sub(node['operand'], 3)}"
    elif tag in COMPARISONS:
        level = 4
        text = f"{sub(node['left'], 5)} {tag} {sub(node['right'], 5)}"
    elif tag in ("+", "-"):
        level = 5
        text = f"{sub(node['left'], 5)} {tag} {sub(node['right'], 6)}"
    elif tag in ("*", "/"):
        level = 6
        text = f"{sub(node['left'], 6)} {tag} {sub(node['right'], 7)}"
    elif tag == "unary-":
        level = 7
        text = f"-{sub(node['operand'], 7)}"
    elif tag == "complex":
        level = 8
        text = f"{sub(node['base'], 8)}[{sub(node['index'], 0)}]"
    elif tag == "call":
        level = 8
        text = f"{sub(node['callee'], 8)}({', '.join(sub(item, 0) for item in node['arguments'])})"
    elif tag == "boolean":
        text = "true" if node["value"] else "false"
    elif tag == "null":
        text = "null"
    elif tag == "number":
        text = number(node["value"])
    elif tag == "string":
        text = quote(node["value"])
    elif tag == "identifier":
        text = node["value"]
    elif tag == "list":
        text = "[" + ", ".join(sub(item, 0) for item in node["items"]) + "]"
    elif tag == "object":
        text = "{" + ", ".join(f"{sub(key, 0)}: {sub(value, 0)}" for key, value in node["fields"]) + "}"
    elif tag == "function":
        text = f"function({', '.join(node['parameters'])}) {block(node['body'], depth)}"
    elif tag == "input":
        text = "input()" if node["prompt"] is None else f"input({sub(node['prompt'], 0)})"
    elif tag == "slice":
        text = f"slice({sub(node['expression'], 0)}, {sub(node['start'], 0)}, {sub(node['end'], 0)})"
    elif tag in CALL_FORMS:
        text = f"{CALL_FORMS[tag]}({sub(node['expression'], 0)})"
    else:
        raise ValueError(f"Cannot print AST node: {tag}")
    return text if level >= minimum else f"({text})"


def format_source(ast):
    lines = [statement(item, 0) + ";" for item in ast["statements"]["statements"]]
    return "\n".join(lines) + "\n" if lines else ""
