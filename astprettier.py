import ast
import functools

def _is_ast_tuple(node):
    """ Return True if node is a tuple of ast.AST class objects """
    return isinstance(node, (ast.AST,))

def _is_expr_tuple(node):
    """ Return True if node is a tuple of ast.expr_context class objects """
    return isinstance(node, (ast.expr_context,))

def _is_sub_node(node):
    return _is_ast_tuple(node) and not _is_expr_tuple(node)

def _is_leaf(node: ast.AST):
    for field in node._fields:
        attr = getattr(node, field)
        if _is_sub_node(attr):
            return False
        elif isinstance(attr, (list, tuple)):
            for val in attr:
                if _is_sub_node(val):
                    return False

    return True

def _fields(node: ast.AST, show_offsets = True):
    if show_offsets:
        return node._attributes + node._fields
    else:
        return node._fields

def _leaf(node: ast.AST, show_offsets=True, ns_prefix=''):
    __leaf = functools.partial(_leaf, show_offsets=show_offsets, ns_prefix=ns_prefix)
    if _is_ast_tuple(node):
        inner = ', '.join(f'{field}={__leaf(getattr(node, field))}' for field in _fields(node, show_offsets=show_offsets))
        return f'{ns_prefix}{type(node).__name__}({inner})'
    elif isinstance(node, list):
        inner = ', '.join(_leaf(item) for item in node)
        return f'[{inner}]'

    return repr(node)

def format(node, indent_level=0, indent='    ', show_offsets=True, ns_prefix=''):
    """
    Pretty format an Python AST node

    The `node` parameter can be either an `ast.AST` object or a string with Python code.
    """
    if isinstance(node, str):
        node = ast.parse(node)
    if ns_prefix and ns_prefix[-1] != '.':
        ns_prefix += '.'
    if node is None or isinstance(node, str):
        return repr(node)
    elif _is_leaf(node):
        return _leaf(node, show_offsets=show_offsets, ns_prefix=ns_prefix)

    _pformat = functools.partial(pformat, indent=indent, show_offsets=show_offsets, ns_prefix=ns_prefix)

    out = [f'{ns_prefix}{type(node).__name__}(']

    for field in _fields(node, show_offsets=show_offsets):
        attr = getattr(node, field)
        if isinstance(attr, list):
            l = len(attr)
            if l == 0:
                representation = repr([])
            elif l == 1 and _is_ast_tuple(attr[0]) and _is_leaf(attr[0]):
                representation = f'[{_pformat(attr[0])}]'
            else:
                inner = ''.join(f'{indent * (indent_level + 2)}{_pformat(el, indent_level + 2)},\n' for el in attr)
                representation = f'[\n{inner}{indent * (indent_level + 1)}]'

        elif _is_ast_tuple(attr):
            representation = _pformat(attr, indent_level + 1)

        else:
            # static strings or ints
            representation = repr(attr)

        out.append(f'{indent * (indent_level + 1)}{field}={representation},')
    out.append(f'{indent * indent_level})')

    return '\n'.join(out)

def print(node, indent_level=0, indent='    ', show_offsets=True, ns_prefix=''):
    """
    Pretty print an Python AST node

    The `node` parameter can be either an `ast.AST` object or a string with Python code.
    """
    # Must be the first line in the function
    kwargs = locals()
    import sys
    sys.stdout.write(format(**kwargs))
    sys.stdout.write('\n')

pformat = format
pprint = print

def main(argv = None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('--no-show-offsets', dest='show_offsets', action='store_false')
    args = parser.parse_args(argv)

    with open(args.filename, 'rb') as f:
        contents = f.read()

    tree = ast.parse(contents, filename=args.filename)
    print(tree, show_offsets=args.show_offsets)
    return 0



if __name__ == '__main__':
    main()
