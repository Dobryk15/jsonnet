import jsonnet_ast as j_ast
from lambda_types import TypeVariable, TypeRowOperator, Function, TypeOperator


def build(ast_: j_ast.AST, my_env, obj_record):
    if isinstance(ast_, j_ast.Object):
        fields = {
            name.value: val for name, val in ast_.fields.items()
        }
        record_id = get_next_record_id(my_env)
        record, record_type = build_record_type_constructor(fields)
        my_env[record_id] = record_type
        obj_record[ast_] = (record_id, record)

        for _, val in fields.items():
            build(val, my_env, obj_record)

    elif isinstance(ast_, j_ast.Local):
        for bind in ast_.binds:
            build(bind.body, my_env, obj_record)
        build(ast_.body, my_env, obj_record)

    elif isinstance(ast_, j_ast.Apply):
        for arg in ast_.arguments:
            build(arg.expr, my_env, obj_record)

    elif isinstance(ast_, j_ast.Array):
        raise Exception('Not processed yet!\n')

    elif isinstance(ast_, j_ast.BinaryOp):
        build(ast_.left_arg, my_env, obj_record)
        build(ast_.right_arg, my_env, obj_record)

    elif isinstance(ast_, j_ast.BuiltinFunction):
        raise Exception('Not processed yet!\n')

    elif isinstance(ast_, j_ast.Conditional):
        build(ast_.branchTrue, my_env, obj_record)
        build(ast_.branchFalse, my_env, obj_record)

    elif isinstance(ast_, j_ast.Error):
        return

    elif isinstance(ast_, j_ast.Function):
        build(ast_.body, my_env, obj_record)

    elif isinstance(ast_, j_ast.InSuper):
        raise Exception('Not processed yet!\n')

    elif isinstance(ast_, j_ast.Index):
        return

    elif isinstance(ast_, j_ast.LiteralBoolean):
        return 

    elif isinstance(ast_, j_ast.LiteralNumber):
        return

    elif isinstance(ast_, j_ast.LiteralString):
        return

    elif isinstance(ast_, j_ast.LiteralNull):
        return

    elif isinstance(ast_, j_ast.ObjectComprehensionSimple):
        return

    elif isinstance(ast_, j_ast.Self):
        return

    elif isinstance(ast_, j_ast.SuperIndex):
        return

    elif isinstance(ast_, j_ast.UnaryOp):
        return 

    elif isinstance(ast_, j_ast.Var):
        return 

    else:
        print(ast_.__class__)
        raise Exception('Node is not found in jsonnet_ast\n')


def build_record_type_constructor(fields):
    var_type = {}
    name_type = {}
    for i, name in enumerate(fields):
        var = f'var{i}'
        var_type[var] = TypeVariable()
        name_type[name] = var_type[var]
    record = TypeRowOperator(name_type)

    def rec_build(i, n, var_type, record):
        if n == 0:
            return record
        var = var_type[f'var{i}']
        if (i == n-1):
            return Function(var, record)
        return Function(var, rec_build(i+1, n, var_type, record))

    return record, rec_build(0, len(var_type), var_type, record)


def get_next_record_id(env):
    record_id = "record_{n}".format(n=env["__record_count__"])
    env["__record_count__"] += 1
    return record_id
