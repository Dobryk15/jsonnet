import jsonnet_ast as j_ast
import lambda_ast as lam_ast
from lambda_types import TypeVariable, TypeRowOperator, Function, TypeOperator


def translate_to_lambda_ast(ast_: j_ast.AST, my_env, obj_record):
    if isinstance(ast_, j_ast.Object):
        location = translate_location(ast_.location)
        ast_.fields = {
            translate_field_name(name): val for name, val in ast_.fields.items()
        }
        record = build_record_type_constructor(ast_.fields)
        record_id = get_next_record_id(my_env)
        obj_record[ast_] = record_id
        my_env[record_id] = record

        field_keys = list(ast_.fields.keys())
        body = apply_record(field_keys, record_id, my_env, location)
        return build_letrec_and(field_keys, ast_.fields, body, my_env, 
                                location, obj_record)

    elif isinstance(ast_, j_ast.Local):
        location = translate_location(ast_.location)
        bind_dic = {}
        for bind in ast_.binds:
            translated_body = translate_to_lambda_ast(bind.body, my_env, obj_record)
            bind_dic[bind.var] = (translated_body, None)
        body = translate_to_lambda_ast(ast_.body, my_env, obj_record)
        if isinstance(body, lam_ast.LetrecAnd):
            body.bindings.update(bind_dic)
            return body
        else:
            return lam_ast.LetrecAnd(bind_dic, body, location)

    elif isinstance(ast_, j_ast.Apply):
        location = translate_location(ast_.location)
        def build_apply(fn, args, location):
            if not args:
                return translate_to_lambda_ast(fn, my_env, obj_record)
            translated_arg = translate_to_lambda_ast(args[-1].expr, my_env, obj_record)
            return lam_ast.Apply(build_apply(fn, args[:-1], location), 
                                 translated_arg, 
                                 location)
        return build_apply(ast_.fn, ast_.arguments, location)

    elif isinstance(ast_, j_ast.Array):
        raise Exception('Not translated yet!\n')

    elif isinstance(ast_, j_ast.BinaryOp):
        location = translate_location(ast_.location)
        if ast_.op == '+':
            return build_plus_op(ast_.left_arg, ast_.right_arg, my_env, location, 
                                 obj_record)
        else:
            raise Exception('Not translated yet!\n')

    elif isinstance(ast_, j_ast.BuiltinFunction):
        raise Exception('Not translated yet!\n')

    elif isinstance(ast_, j_ast.Conditional):
        raise Exception('Not translated yet!\n')

    elif isinstance(ast_, j_ast.Error):
        raise Exception('Not translated yet!\n')

    elif isinstance(ast_, j_ast.Function):
        def build_lambda(args, body):
            if not args:
                return translate_to_lambda_ast(body, my_env, obj_record)
            return lam_ast.Lambda(args[0].id, build_lambda(args[1:], body))
        return build_lambda(ast_.arguments, ast_.body)

    elif isinstance(ast_, j_ast.InSuper):
        raise Exception('Not translated yet!\n')

    elif isinstance(ast_, j_ast.Index):
        location = translate_location(ast_.location)
        if isinstance(ast_.target, j_ast.Self) and isinstance(ast_.index, j_ast.LiteralString):
            return lam_ast.Identifier(ast_.index.value, location)
        else:
            raise Exception('Not translated yet!\n')

    elif isinstance(ast_, j_ast.LiteralBoolean):
        location = translate_location(ast_.location)
        return lam_ast.LiteralBoolean(ast_.value, location)

    elif isinstance(ast_, j_ast.LiteralNumber):
        location = translate_location(ast_.location)
        return lam_ast.LiteralNumber(ast_.value, location)

    elif isinstance(ast_, j_ast.LiteralString):
        location = translate_location(ast_.location)
        return lam_ast.LiteralString(ast_.value, location)

    elif isinstance(ast_, j_ast.LiteralNull):
        return lam_ast.Identifier("null")

    elif isinstance(ast_, j_ast.ObjectComprehensionSimple):
        raise Exception('Not translated yet!\n')

    elif isinstance(ast_, j_ast.Self):
        return lam_ast.Identifier("self")

    elif isinstance(ast_, j_ast.SuperIndex):
        return lam_ast.Identifier(ast_.index.value)

    elif isinstance(ast_, j_ast.UnaryOp):
        raise Exception('Not translated yet!\n')

    elif isinstance(ast_, j_ast.Var):
        location = translate_location(ast_.location)
        return lam_ast.Identifier(ast_.id, location)

    else:
        print(ast_.__class__)
        raise Exception('Node is not found in jsonnet_ast\n')


def build_record_type_constructor(fields):
    var_type = {}
    name_type = {}
    for i, field in enumerate(fields):
        name, _ = field
        var = f'var{i}'
        var_type[var] = TypeVariable()
        name_type[name] = var_type[var]
    record_type = TypeRowOperator(name_type)

    def rec_build(i, n, var_type, record_type):
        if n == 0:
            return record_type
        var = var_type[f'var{i}']
        if (i == n-1):
            return Function(var, record_type)
        return Function(var, rec_build(i+1, n, var_type, record_type))

    return rec_build(0, len(var_type), var_type, record_type)


def build_letrec_and(field_keys, fields, body, env, location, obj_record):
    translated_fields = {}
    for key in field_keys:
        translated_body = translate_to_lambda_ast(fields[key], env, obj_record)
        name, loc = key
        translated_fields[name] = (translated_body, loc)
    return lam_ast.LetrecAnd(translated_fields, body, location)


def get_next_record_id(env):
    record_id = "record_{n}".format(n=env["__record_count__"])
    env["__record_count__"] += 1
    return record_id


def get_next_plus_id(env):
    plus_id = "plus_{n}".format(n=env["__plus_count__"])
    env["__plus_count__"] += 1
    return plus_id


def apply_record(field_keys, record_id, env, location):
    if not field_keys:
        return lam_ast.Identifier(record_id)
    name, loc = field_keys[-1]
    return lam_ast.Apply(apply_record(field_keys[:-1], record_id, env, location),
                         lam_ast.Identifier(name, loc),
                         location)


def translate_field_name(name):
    location = translate_location(name.location)
    if isinstance(name, j_ast.LiteralString):
        return (name.value, location)
    else:
        raise Exception(f"Expected LiteralString but got {name.__class__}")


def build_plus_op(left_arg, right_arg, env, location, obj_record):
    if isinstance(right_arg, j_ast.Object):
        base_obj = translate_to_lambda_ast(left_arg, env, obj_record)
        child_obj = translate_to_lambda_ast(right_arg, env, obj_record)
        return lam_ast.Inherit(base_obj, child_obj, location)
    else:
        var = TypeVariable()
        plus_id = get_next_plus_id(env)
        env[plus_id] = Function(var, Function(var, var))
        return lam_ast.Apply(lam_ast.Apply(lam_ast.Identifier(plus_id),
                                           translate_to_lambda_ast(
                                               left_arg, env, obj_record),
                                           location),
                             translate_to_lambda_ast(right_arg, env, obj_record),
                             location)

def translate_location(location):
    return lam_ast.Location(location.begin, location.end)