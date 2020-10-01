import jsonnet_ast as ast
import lambda_types as lt

def extend(ast_: ast.AST, obj_record, record):
    """Extends record types for the objects, which use fields undefined
    in objects' bodies but which should be defined during object 
    inheritanse before materialisation. 
       
        Example: local t = {x: self.y}. 
            Before applying 'extend' functin, the type of t is: {x: a}
            After applying: {x: a, y: b} 
            (during type inference should be infered that a=b)
    """

    if isinstance(ast_, ast.Object):
        if ast_ not in obj_record:
            raise Exception(f'Object node was not found in obj_record')
        _, record = obj_record[ast_]
        for _, body in ast_.fields.items():
            extend(body, obj_record, record)

    elif isinstance(ast_, ast.Local):
        extend(ast_.body, obj_record, record)
        for bind in ast_.binds:
            extend(bind.body, obj_record, record) 

    elif isinstance(ast_, ast.Apply):
        for arg in ast_.arguments:
            if arg.expr:
                extend(arg.expr, obj_record, record)

    elif isinstance(ast_, ast.Array):
        for el in ast_.elements:
            extend(el, obj_record, record)

    elif isinstance(ast_, ast.BinaryOp):
        if ast_.op == '+':
            extend(ast_.left_arg, obj_record, record)
            extend(ast_.right_arg, obj_record, record)

    elif isinstance(ast_, ast.BuiltinFunction):
        return    

    elif isinstance(ast_, ast.Conditional):
        extend(ast_.branchTrue, obj_record, record)
        extend(ast_.branchFalse, obj_record, record)

    elif isinstance(ast_, ast.Error):
        return
       
    elif isinstance(ast_, ast.Function):
        extend(ast_.body, obj_record, record)

    elif isinstance(ast_, ast.InSuper):
        return

    elif isinstance(ast_, ast.Index):
        if isinstance(ast_.target, ast.Self) and isinstance(ast_.index, ast.LiteralString):
            name = ast_.index.value
            if isinstance(record, lt.TypeRowOperator):
                if name not in record.fields:
                    record.flags[name] = 'r'
            else:
                raise Exception("Unexpected type")

    elif isinstance(ast_, ast.LiteralBoolean):
        return

    elif isinstance(ast_, ast.LiteralNumber):
        return

    elif isinstance(ast_, ast.LiteralString):
        return

    elif isinstance(ast_, ast.LiteralNull):
        return

    elif isinstance(ast_, ast.ObjectComprehensionSimple):
        return

    elif isinstance(ast_, ast.Self):
        return

    elif isinstance(ast_, ast.SuperIndex):
        return

    elif isinstance(ast_, ast.UnaryOp):
        extend(ast_.arg, obj_record, record)

    elif isinstance(ast_, ast.Var):
        return

    else:
        raise Exception('Node {x} is not found in jsonnet_ast\n'.format(
            x=ast_.__class__.__name__))

