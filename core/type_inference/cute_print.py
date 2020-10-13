import jsonnet_ast as ast


def to_str(ast_, indent, curr_indent):
    """Function to_str() creates formatted string of Jsonnet AST object.

    Parameters:
        ast_: object to print; this object has to consist of objects from 
            jsonnet_ast.py module;
        indent(str): indent-unit, e.g. '\t';
        curr_indent(str): total indent from the beginning of the line 
            for the current object.

    Returns:
        str: formatted Jsonnet AST string
    """

    next_indent = curr_indent + indent

    if isinstance(ast_, ast.Object):
        res = 'Object(\n{ind}{loc},\n{ind}{{\n'.format(
            ind = next_indent,
            loc=to_str(ast_.location, indent, next_indent)
        )
        field_indent = next_indent + indent
        for k, v in ast_.fields.items():
            res += '{field_indent}{k_str} : {v_str},\n'.format(
                field_indent = field_indent,
                k_str = to_str(k, indent, field_indent),
                v_str = to_str(v, indent, field_indent)
            )
        res += f'{next_indent}}}\n{curr_indent})'
        return res

    elif isinstance(ast_, ast.Local):
        res = 'Local(\n{ind}{loc},\n{ind}{body_str},\n'.format(
            ind = next_indent,
            loc = to_str(ast_.location, indent, next_indent),
            body_str = to_str(ast_.body, indent, next_indent)
        )
        for bind in ast_.binds:
            res += '{next_indent}{bind_str},\n'.format(
                next_indent = next_indent,
                bind_str = to_str(bind, indent, next_indent)
            )
        res += f'{curr_indent})' 
        return res       

    elif isinstance(ast_, ast.Apply):
        loc = to_str(ast_.location, indent, next_indent)
        fn_str = to_str(ast_.fn, indent, next_indent)
        res = f'Apply(\n{next_indent}{loc},\n{next_indent}{fn_str},\n'
        for arg in ast_.arguments:
            arg_str = to_str(arg, indent, next_indent)
            res += f'{next_indent}{arg_str},\n'
        res += f'{curr_indent})'
        return res 

    elif isinstance(ast_, ast.Array):
        loc = to_str(ast_.location, indent, next_indent)
        res = f'Array({loc}, elements=[\n'
        elem_indent = next_indent + indent
        for el in ast_.elements:
            res += '{elem_indent}{el_str},\n'.format(
                elem_indent = elem_indent,
                el_str = to_str(el, indent, elem_indent)
            )
        res += f'{next_indent}]\n{curr_indent})'
        return res

    elif isinstance(ast_, ast.BinaryOp):
        res = 'BinaryOp(\n{ind}{loc},\n{ind}{l},\n{ind}"{op}",\n{ind}{r},\n'.format(
            loc = to_str(ast_.location, indent, next_indent),
            ind = next_indent,
            op = ast_.op,
            l = to_str(ast_.left_arg, indent, next_indent),
            r = to_str(ast_.right_arg, indent, next_indent)
        )
        res += f'{curr_indent})'
        return res 

    elif isinstance(ast_, ast.BuiltinFunction):
        loc = to_str(ast_.location, indent, next_indent)
        res = f'BuiltinFunction({loc}, name="{ast_.name}", params=('
        delim=', '
        n = len(ast_.params)
        for i, param in enumerate(ast_.params):
            if i == (n-1):
                delim = ''
            res += f'{param}{delim}'
        res += '))'
        return res

    elif isinstance(ast_, ast.Conditional):
        res = 'Conditional(\n{ind}{loc},\n{ind}{cond},\n{ind}{t},\n{ind}{f},\n'.format(
            loc = to_str(ast_.location, indent, next_indent),
            ind = next_indent,
            cond = to_str(ast_.cond, indent, next_indent),
            t = to_str(ast_.branchTrue, indent, next_indent),
            f = to_str(ast_.branchFalse, indent, next_indent)
        )
        res += f'{curr_indent})'
        return res

    elif isinstance(ast_, ast.Error):
        loc = to_str(ast_.location, indent, next_indent)
        res = f'Error(\n{next_indent}{loc},\n{next_indent}{ast_.msg}\n'
        res += f'{curr_indent})'
        return res

    elif isinstance(ast_, ast.Function):
        loc = to_str(ast_.location, indent, next_indent)
        body_str = to_str(ast_.body, indent, next_indent)
        res = f'Function(\n{next_indent}{loc},\n{next_indent}{body_str},\n'
        for arg in ast_.arguments:
            arg_str = to_str(arg, indent, next_indent)
            res += f'{next_indent}{arg_str},\n'
        res += f'{curr_indent})'
        return res

    elif isinstance(ast_, ast.InSuper):
        loc = to_str(ast_.location, indent, next_indent)
        elem = to_str(ast_.element, indent, next_indent)
        res = f'InSuper(\n{next_indent}{loc},\n{next_indent}{elem}\n'
        res += f'{curr_indent})'
        return res

    elif isinstance(ast_, ast.Index):
        res = 'Index(\n{ind}{loc},\n{ind}{target},\n{ind}{index}\n'.format(
            ind = next_indent,
            loc = to_str(ast_.location, indent, next_indent),
            target = to_str(ast_.target, indent, next_indent),
            index = to_str(ast_.index, indent, next_indent)
        )
        res += f'{curr_indent})'
        return res 

    elif isinstance(ast_, ast.LiteralBoolean):
        loc = to_str(ast_.location, indent, next_indent)
        res = f'LiteralBoolean({loc}, {ast_.value})'
        return res 

    elif isinstance(ast_, ast.LiteralNumber):
        loc = to_str(ast_.location, indent, next_indent)
        res = f'LiteralNumber({loc}, {ast_.value})'
        return res 

    elif isinstance(ast_, ast.LiteralString):
        loc = to_str(ast_.location, indent, next_indent)
        res = f'LiteralString({loc}, "{ast_.value}")'
        return res 

    elif isinstance(ast_, ast.LiteralNull):
        res = 'null'
        return res 

    elif isinstance(ast_, ast.ObjectComprehensionSimple):
        res = 'ObjectComprehention()'
        return res 

    elif isinstance(ast_, ast.Self):
        loc = to_str(ast_.location, indent, next_indent)
        res = f'Self({loc})'
        return res 

    elif isinstance(ast_, ast.SuperIndex):
        res = 'SuperIndex(\n{ind}{loc},\n{ind}{index}\n'.format(
            ind = next_indent,
            loc = to_str(ast_.location, indent, next_indent),
            index = to_str(ast_.index, indent, next_indent)
        )
        res += f'{curr_indent})'
        return res 

    elif isinstance(ast_, ast.UnaryOp):
        res = 'UnaryOp(\n{ind}{loc},\n{ind}"{op}",\n{ind}{arg},\n'.format(
            loc = to_str(ast_.location, indent, next_indent),
            ind = next_indent,
            op = ast_.op,
            arg = to_str(ast_.arg, indent, next_indent)
        )
        res += f'{curr_indent})'
        return res

    elif isinstance(ast_, ast.Var):
        loc = to_str(ast_.location, indent, next_indent)
        res = f'Var({loc}, {ast_.id})'
        return res 
    
    elif isinstance(ast_, ast.Location):
        res = f'Location({ast_.begin}, {ast_.end})'
        return res
    
    elif isinstance(ast_, ast.Bind):
        res = 'Bind(var="{var_str}", val={body_str})'.format(
            var_str = ast_.var,
            body_str = to_str(ast_.body, indent, curr_indent)
        )
        return res
    
    elif isinstance(ast_, ast.ArgParam):
        id_str = ''
        expr_str = ''
        delim = ''
        if ast_.id:
            id_str = f'id={ast_.id}'
            delim = ', '
        if ast_.expr:
            expr_str = f'{delim}expr={to_str(ast_.expr, indent, curr_indent)}'
        res = f'ArgParam({id_str}{expr_str})'
        return res

    else:
        raise Exception('{} was not found in jsonnet_ast\n'.format(
            ast_.__class__.__name__))


def cute_print(ast_, indent):
    ast_str = to_str(ast_, indent, '')
    print(ast_str)
