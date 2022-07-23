import ast
import sys
import pytest
import ultraimport

astprettier = ultraimport('__dir__/../astprettier.py')

def get_module_body(s):
    return ast.parse(s).body[0]

def get_expr_value(s):
    return get_module_body(s).value

@pytest.mark.parametrize('s', ('x', '"y"', '5', '[]'))
def test_is_leaf_true(s):
    assert astprettier._is_leaf(get_expr_value(s)) is True


def test_is_leaf_has_attr_with_list_of_primitives():
    assert astprettier._is_leaf(get_module_body('global x, y')) is True

@pytest.mark.parametrize('s', ('a.b', '[4]', 'x()'))
def test_is_leaf_false(s):
    assert astprettier._is_leaf(get_expr_value(s)) is False

def test_pformat_py35_regression():
    expected = (
        'Dict(\n'
        '    keys=[\n'
        "        Name(id='a', ctx=Load()),\n"
        '        None,\n'
        '    ],\n'
        '    values=[\n'
        "        Name(id='b', ctx=Load()),\n"
        "        Name(id='k', ctx=Load()),\n"
        '    ],\n'
        ')'
    )
    s = '{a: b, **k}'
    assert astprettier.pformat(get_expr_value(s), show_offsets=False) == expected


def test_pformat_node():
    ret = astprettier.pformat(get_expr_value('x'), show_offsets=False)
    assert ret == "Name(id='x', ctx=Load())"


def test_pformat_nested_with_offsets():
    expected = (
        'Assign(\n'
        '    lineno=1,\n'
        '    col_offset=0,\n'
        '    end_lineno=1,\n'
        '    end_col_offset=5,\n'
        "    targets=[Name(lineno=1, col_offset=0, end_lineno=1, end_col_offset=1, id='x', ctx=Store())],\n"
        '    value=Constant(lineno=1, col_offset=4, end_lineno=1, end_col_offset=5, value=5, kind=None),\n'
        '    type_comment=None,\n'
        ')'
    )
    ret = astprettier.pformat(get_module_body('x = 5'))
    assert ret == expected


def test_pformat_nested_attr_empty_list():
    ret = astprettier.pformat(get_module_body('if x: pass'), show_offsets=False)
    assert ret == (
        'If(\n'
        "    test=Name(id='x', ctx=Load()),\n"
        '    body=[Pass()],\n'
        '    orelse=[],\n'
        ')'
    )


def test_pformat_mixed_sub_nodes_and_primitives():
    node = get_module_body('from y import x')
    ret = astprettier.pformat(node, show_offsets=False)
    assert ret == (
        'ImportFrom(\n'
        "    module='y',\n"
        "    names=[alias(name='x', asname=None)],\n"
        '    level=0,\n'
        ')'
    )


def test_pformat_nested_multiple_elements():
    ret = astprettier.pformat(get_expr_value('[a, b, c]'), show_offsets=False)
    assert ret == (
        'List(\n'
        '    elts=[\n'
        "        Name(id='a', ctx=Load()),\n"
        "        Name(id='b', ctx=Load()),\n"
        "        Name(id='c', ctx=Load()),\n"
        '    ],\n'
        '    ctx=Load(),\n'
        ')'
    )


def test_pformat_custom_indent():
    node = get_expr_value('[a, b, c]')
    ret = astprettier.pformat(node, indent='\t', show_offsets=False)
    assert ret == (
        'List(\n'
        '\telts=[\n'
        "\t\tName(id='a', ctx=Load()),\n"
        "\t\tName(id='b', ctx=Load()),\n"
        "\t\tName(id='c', ctx=Load()),\n"
        '\t],\n'
        '\tctx=Load(),\n'
        ')'
    )

def test_pformat_nested_node_without_line_information():
    expected_39 = (
        'Subscript(\n'
        '    lineno=1,\n'
        '    col_offset=0,\n'
        '    end_lineno=1,\n'
        '    end_col_offset=4,\n'
        "    value=Name(lineno=1, col_offset=0, end_lineno=1, end_col_offset=1, id='a', ctx=Load()),\n"
        '    slice=Constant(lineno=1, col_offset=2, end_lineno=1, end_col_offset=3, value=0, kind=None),\n'
        '    ctx=Load(),\n'
        ')'
    )
    expected_38 = (
        'Subscript(\n'
        '    lineno=1,\n'
        '    col_offset=0,\n'
        '    end_lineno=1,\n'
        '    end_col_offset=4,\n'
        "    value=Name(lineno=1, col_offset=0, end_lineno=1, end_col_offset=1, id='a', ctx=Load()),\n"
        '    slice=Index(\n'
        '        value=Constant(lineno=1, col_offset=2, end_lineno=1, end_col_offset=3, value=0, kind=None),\n'
        '    ),\n'
        '    ctx=Load(),\n'
        ')'
    )
    expected = expected_39 if sys.version_info >= (3, 9) else expected_38
    ret = astprettier.pformat(get_expr_value('a[0]'))
    assert ret == expected


def test_pformat_leaf_node_with_list():
    ret = astprettier.pformat(get_module_body('global x, y'), show_offsets=False)
    assert ret == "Global(names=['x', 'y'])"


def test_print(capsys):
    astprettier.print(get_expr_value('x'), show_offsets=False)
    out, _ = capsys.readouterr()
    assert out == "Name(id='x', ctx=Load())\n"


def test_main_with_offsets(capsys, tmpdir):
    expected = '''\
Module(
    body=[
        Assign(
            lineno=1,
            col_offset=0,
            end_lineno=1,
            end_col_offset=5,
            targets=[Name(lineno=1, col_offset=0, end_lineno=1, end_col_offset=1, id='x', ctx=Store())],
            value=Name(lineno=1, col_offset=4, end_lineno=1, end_col_offset=5, id='y', ctx=Load()),
            type_comment=None,
        ),
    ],
    type_ignores=[],
)
'''
    f = tmpdir.join('test.py')
    f.write('x = y\n')
    astprettier.main((f.strpath,))
    out, _ = capsys.readouterr()
    assert out == expected


def test_main_hide_offsets(capsys, tmpdir):
    expected = '''\
Module(
    body=[
        Assign(
            targets=[Name(id='x', ctx=Store())],
            value=Name(id='y', ctx=Load()),
            type_comment=None,
        ),
    ],
    type_ignores=[],
)
'''
    f = tmpdir.join('test.py')
    f.write('x = y\n')
    astprettier.main((f.strpath, '--no-show-offsets'))
    out, _ = capsys.readouterr()
    assert out == expected

