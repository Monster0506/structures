def check(node, in_loop=False, in_function=False):
    if type(node) in (list, tuple):
        for item in node:
            check(item, in_loop, in_function)
        return
    if type(node) is not dict:
        return
    tag = node["tag"]
    if tag in ("break", "continue") and not in_loop:
        raise ValueError(f"'{tag}' used outside a loop")
    if tag == "return" and not in_function:
        raise ValueError("'return' used outside a function")
    if tag == "function":
        names = node["parameters"]
        for position, name in enumerate(names):
            if name in names[:position]:
                raise ValueError(f"Duplicate parameter name: {name}")
        check(node["body"], False, True)
        return
    if tag == "while":
        check(node["condition"], in_loop, in_function)
        check(node["body"], True, in_function)
        return
    for value in node.values():
        check(value, in_loop, in_function)
