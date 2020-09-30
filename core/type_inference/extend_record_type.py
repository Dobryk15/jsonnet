import jsonnet_ast as ast
import lambda_types as lt

def extend(ast_: ast.AST, env, obj_record, record_id):
    """Extends record types for the objects, which use fields undefined
       in objects' bodies but which should be defined during object 
       inheritanse before materialisation. 
       
       Example: local t = {x: self.y}. 
            Before applying 'extend' functin, the type of t is: {x: a}
            After applying: {x: a, y: b} 
            (during type inference should be infered that a=b)
            
    """

    if isinstance(ast_, ast.Object):
        record_id = obj_record[ast_]
        for _, body in ast_.fields.items():
            extend(body, env, obj_record, record_id)

    elif isinstance(ast_, ast.Local):
        extend(ast_.body, env, obj_record, record_id)
        for bind in ast_.binds:
            extend(bind.body, env, obj_record, record_id) 

    elif isinstance(ast_, ast.Apply):
        for arg in ast_.arguments:
            if arg.expr:
                extend(arg.expr, env, obj_record, record_id)

    elif isinstance(ast_, ast.Array):
        for el in ast_.elements:
            extend(el, env, obj_record, record_id)

    elif isinstance(ast_, ast.BinaryOp):
        if ast_.op == '+':
            extend(ast_.left_arg, env, obj_record, record_id)
            extend(ast_.right_arg, env, obj_record, record_id)

    elif isinstance(ast_, ast.BuiltinFunction):
        return    

    elif isinstance(ast_, ast.Conditional):
        extend(ast_.branchTrue, env, obj_record, record_id)
        extend(ast_.branchFalse, env, obj_record, record_id)

    elif isinstance(ast_, ast.Error):
        return
       
    elif isinstance(ast_, ast.Function):
        extend(ast_.body, env, obj_record, record_id)

    elif isinstance(ast_, ast.InSuper):
        return

    elif isinstance(ast_, ast.Index):
        def set_flag(record_type, name):
            return_type = record_type.types[1]
            if isinstance(return_type, lt.TypeRowOperator):
                if name not in return_type.fields:
                    return_type.flags[name] = 'r'
                    record_type.types[1] = return_type
                return
            set_flag(return_type, name)
        
        if isinstance(ast_.target, ast.Self) and isinstance(ast_.index, ast.LiteralString):
            record_type = env[record_id]
            if not isinstance(record_type, lt.Function):
                raise Exception("Expected Function type, got: {tp}".format(
                    record_type.__class__.__name__))
            name = ast_.index.value
            set_flag(record_type, name)

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
        extend(ast_.arg, env, obj_record, record_id)

    elif isinstance(ast_, ast.Var):
        return

    else:
        raise Exception('Node {x} is not found in jsonnet_ast\n'.format(
            x=ast_.__class__.__name__))

