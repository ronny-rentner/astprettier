import ast, functools, types, sys

def _is_ast_tuple(node):
    """ Return True if node is a tuple of ast.AST class objects """
    return isinstance(node, (ast.AST,))

def _is_expr_tuple(node):
    """ Return True if node is a tuple of ast.expr_context class objects """
    return isinstance(node, (ast.expr_context,))

def _is_sub_node(node):
    return _is_ast_tuple(node) and not _is_expr_tuple(node)

def _is_leaf(node: ast.AST):
    for field, attr in _fields(node):
        if _is_sub_node(attr):
            return False
        elif isinstance(attr, (list, tuple)):
            for val in attr:
                if _is_sub_node(val):
                    return False

    return True

def _field_names(node: ast.AST, show_offsets = True):
    """ Returns a list of field names """
    if show_offsets:
        return node._attributes + node._fields
    else:
        return node._fields

def _fields(node: ast.AST, show_offsets = True):
    """ Returns a list of tuples with field names and fields in node """
    return ((field, getattr(node, field)) for field in _field_names(node, show_offsets))

def _leaf(node: ast.AST, show_offsets=True, ns_prefix=''):

    __leaf = functools.partial(_leaf, show_offsets=show_offsets, ns_prefix=ns_prefix)

    if _is_ast_tuple(node):
        fields = (f'{name}={__leaf(value)}' for name, value in _fields(node, show_offsets))
        inner = ', '.join(fields)
        return f'{ns_prefix}{type(node).__name__}({inner})'

    elif isinstance(node, list):
        inner = ', '.join(__leaf(item) for item in node)
        return f'[{inner}]'

    return repr(node)

def pformat(node, indent_level=0, indent='    ', show_offsets=True, ns_prefix=''):
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

    for field, attr in _fields(node, show_offsets):
        if isinstance(attr, list):
            l = len(attr)
            if l == 0:
                representation = repr([])
            elif l == 1 and _is_ast_tuple(attr[0]) and _is_leaf(attr[0]):
                representation = f'[{_pformat(attr[0])}]'
            else:
                _indent = indent * (indent_level + 2)
                elements = (f'{_indent}{_pformat(element, indent_level + 2)}' for element in attr)
                inner = ',\n'.join(elements)
                representation = f'[\n{inner},\n{indent * (indent_level + 1)}]'

        elif _is_ast_tuple(attr):
            representation = _pformat(attr, indent_level + 1)

        else:
            # static strings or ints
            representation = repr(attr)

        out.append(f'{indent * (indent_level + 1)}{field}={representation},')
    out.append(f'{indent * indent_level})')

    return '\n'.join(out)

def pprint(node, indent_level=0, indent='    ', show_offsets=True, ns_prefix=''):
    """
    Pretty print an Python AST node

    The `node` parameter can be either an `ast.AST` object or a string with Python code.
    """
    # Must be the first line in the function
    kwargs = locals()
    import sys
    sys.stdout.write(pformat(**kwargs))
    sys.stdout.write('\n')

def main(*args):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument(      '--show-offsets',    dest='show_offsets', action='store_const', const=True)
    parser.add_argument('-n', '--no-show-offsets', dest='show_offsets', action='store_const', const=False)
    parser.add_argument('-i', '--indent',          dest='indent',       action='store')
    parser.add_argument('-l', '--level',           dest='indent_level', type=int)
    parser.add_argument('-p', '--ns-prefix',       dest='ns_prefix',    action='store')
    args = parser.parse_args(*args)

    try:
        with open(args.filename, 'rb') as f:
            contents = f.read()
    except Exception as e:
        print(e)
        raise SystemExit(1)

    tree = ast.parse(contents, filename=args.filename)
    del args.filename
    # Filter all arguments with value `None` becaues they have not actually been set when calling
    # astprettier from command line
    actually_set_arguments = { k: v for (k, v) in vars(args).items() if v is not None }
    pprint(tree, **actually_set_arguments)

if __name__ == '__main__':
    main()
else:
    # Make astprettier() directly callable after doing `import astprettier`
    class CallableModule(types.ModuleType):
        def __call__(self, *args, **kwargs):
            return pprint(*args, **kwargs)

    sys.modules[__name__].__class__ = CallableModule
    sys.modules[__name__].print = pprint
