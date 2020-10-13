import subprocess
import argparse

import hm_algo
import jsonnet_ast as ast
from lambda_types import TypeVariable
from rename import rename_local
from build_records import build
from extend_records import extend
from translate_jsonnet_to_lambda import translate_to_lambda_ast
import cute_print


def get_jsonnet_ast_str(jsonnet, rebuild=False):
    """ Prints desugared Jsonnet AST.

        jsonnet: Jsonnet program 
        rebuild: Pass True if you want to rebuild print_ast.cpp
                 You can pass False or skip this parameter if there are
                 no changes in print_ast.cpp and current binary is up to date 
    """
    if rebuild:
        command1 = ['bazel', 'build', '//core/type_inference:print_ast']
        subprocess.run(command1, check=True, text=True)

    command2 = ['bazel-bin/core/type_inference/print_ast', f'{jsonnet}']
    result = subprocess.run(command2, stdout=subprocess.PIPE, 
                            check=True, text=True, shell=False)
    return result.stdout


def parse_ast(ast_str):
    """Evaluates passed string to the python AST object"""
    return eval(ast_str)


def create_init_env():
    """Creates initial type environment for type inference algorithm"""
    init_env = {}
    init_env["__record_count__"] = 0
    init_env["__plus_count__"] = 0
    init_env["None"] = TypeVariable()
    init_env["null"] = TypeVariable()
    init_env["self"] = TypeVariable()
    return init_env


def run(jsonnet_program):
    """Performs a couple of transformations to convert Jsonnet program 
       to Lambda AST. Runs type inference algorithm.
    """
    jsonnet_ast_str = get_jsonnet_ast_str(jsonnet_program)
    jsonnet_ast = parse_ast(jsonnet_ast_str)

    print("\n----Jsonnet AST----")
    cute_print.cute_print(jsonnet_ast, indent='    ')

    name_env = {'std': 'std'}
    rename_local(jsonnet_ast, name_env)

    env = create_init_env()
    obj_record = {}
    
    build(jsonnet_ast, env, obj_record)
    extend(jsonnet_ast, None, None, env, obj_record)
    lambda_ast = translate_to_lambda_ast(jsonnet_ast, env, obj_record)
    print(f"\n----Lambda AST----\n{lambda_ast}")
    
    return hm_algo.try_exp(env, lambda_ast)


def read_file(file_name):
    f = open(file_name, "r")
    return f.read()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run type inference.')
    parser.add_argument('--file_path', type=str, required=True,
                        help='path to file with jsonnet program')
    args = parser.parse_args()
    jsonnet_program = read_file(args.file_path)
    print(jsonnet_program)
    run(jsonnet_program)
