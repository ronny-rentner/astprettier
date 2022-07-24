import ast
import functools
import types
import sys

def _is_ast_tuple(node):
    """ Returns True if node is a tuple of ast.AST class objects """
    return isinstance(node, (ast.AST,))

def _is_expr_tuple(node):
    """ Returns True if node is a tuple of ast.expr_context class objects """
    return isinstance(node, (ast.expr_context,))

def _is_sub_node(node):
    return _is_ast_tuple(node) and not _is_expr_tuple(node)

def _is_leaf(node: ast.AST):
    for name, value in _fields(node):
        if _is_sub_node(value):
            return False
        elif isinstance(value, (list, tuple)):
            for val in value:
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
        # TODO: Probably not needed, better do it ourselves in another recursion?
        return _leaf(node, show_offsets=show_offsets, ns_prefix=ns_prefix)

    _pformat = functools.partial(pformat, indent=indent, show_offsets=show_offsets, ns_prefix=ns_prefix)

    out = [f'{ns_prefix}{type(node).__name__}(']

    for name, value in _fields(node, show_offsets):
        if isinstance(value, list):
            l = len(value)
            if l == 0:
                representation = repr([])
            elif l == 1 and _is_ast_tuple(value[0]) and _is_leaf(value[0]):
                representation = f'[{_pformat(value[0], indent_level + 1)}]'
            else:
                _indent = indent * (indent_level + 2)
                elements = (f'{_indent}{_pformat(element, indent_level + 2)}' for element in value)
                inner = ',\n'.join(elements)
                representation = f'[\n{inner},\n{indent * (indent_level + 1)}]'

        elif _is_ast_tuple(value):
            representation = _pformat(value, indent_level + 1)

        else:
            # static strings or ints
            representation = repr(value)

        out.append(f'{indent * (indent_level + 1)}{name}={representation},')
    out.append(f'{indent * indent_level})')

    return '\n'.join(out)

def pprint(node, indent_level=0, indent='    ', show_offsets=True, ns_prefix='', colorize=False):
    """
    Pretty print an Python AST node

    The `node` parameter can be either an `ast.AST` object or a string with Python code.
    """

    out = pformat(node, indent_level, indent, show_offsets, ns_prefix)

    if colorize:
        try:
            import pygments, pygments.lexers, pygments.formatters
            # We use the NumPyLexer because it allows to define a custom list of extra keywords
            # to highlight and we want to highlight all methods of the ast module
            lexer = pygments.lexers.NumPyLexer()
            keys =  list(vars(ast).keys()) + list('body')
            lexer.EXTRA_KEYWORDS = { key for key in vars(ast).keys() if not key.startswith('_') }
            out = pygments.highlight(out, lexer, pygments.formatters.TerminalTrueColorFormatter())
        except ImportError as e:
            print(e)
            pass

    sys.stdout.write(out)
    sys.stdout.write('\n')

def main(*args):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='?', type=argparse.FileType('r'), default=(None if not sys.stdin.isatty() else sys.stdin))
    parser.add_argument(      '--show-offsets',    dest='show_offsets', action='store_const', const=True)
    parser.add_argument('-n', '--no-show-offsets', dest='show_offsets', action='store_const', const=False)
    parser.add_argument('-i', '--indent',          dest='indent',       action='store')
    parser.add_argument('-l', '--level',           dest='indent_level', type=int)
    parser.add_argument('-p', '--ns-prefix',       dest='ns_prefix',    action='store')
    parser.add_argument('-c', '--colorize',        dest='colorize',     action='store_const', const=True)
    parser.add_argument(      '--no-colorize',     dest='colorize',     action='store_const', const=False)
    args = parser.parse_args(*args)

    if not args.filename:
        parser.print_usage()
        print('Error: missing filename')
        raise SystemExit(1)

    contents = str(args.filename.read())
    tree = ast.parse(contents, filename=args.filename.name)

    del args.filename

    # Filter all arguments with value `None` becaues they have not actually been set when calling
    # astprettier from command line
    actually_set_arguments = { k: v for (k, v) in vars(args).items() if v is not None }
    pprint(tree, **actually_set_arguments)

if __name__ == '__main__':
    main()
