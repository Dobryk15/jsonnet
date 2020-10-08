#!/usr/bin/env python
"""
.. module:: inference
   :synopsis: An implementation of the Hindley Milner type checking algorithm
              based on the Scala code by Andrew Forrest, the Perl code by
              Nikita Borisov and the paper "Basic Polymorphic Typechecking"
              by Cardelli.
.. moduleauthor:: Robert Smallshire
"""
from __future__ import print_function
from lambda_ast import *
from lambda_types import *
import copy

# =======================================================#
# Exception types

class InferenceError(Exception):
    """Raised if the type inference algorithm cannot infer types successfully"""

    def __init__(self, message):
        self.__message = message

    message = property(lambda self: self.__message)

    def __str__(self):
        return str(self.message)


class ParseError(Exception):
    """Raised if the type environment supplied for is incomplete"""

    def __init__(self, message):
        self.__message = message

    message = property(lambda self: self.__message)

    def __str__(self):
        return str(self.message)


# =======================================================#
# Type inference machinery

def analyse(node, env, non_generic=None):
    """Computes the type of the expression given by node.

    The type of the node is computed in the context of the
    supplied type environment env. Data types can be introduced into the
    language simply by having a predefined set of identifiers in the initial
    environment. environment; this way there is no need to change the syntax or, more
    importantly, the type-checking program when extending the language.

    Args:
        node: The root of the abstract syntax tree.
        env: The type environment is a mapping of expression identifier names
            to type assignments.
            to type assignments.
        non_generic: A set of non-generic variables, or None

    Returns:
        The computed type of the expression.

    Raises:
        InferenceError: The type of the expression could not be inferred, for example
            if it is not possible to unify two types such as Number and Bool
        ParseError: The abstract syntax tree rooted at node could not be parsed
    """

    if non_generic is None:
        non_generic = set()

    if isinstance(node, Identifier):
        result_type = get_type(node.name, env, non_generic)
        return result_type
    elif isinstance(node, LiteralNumber):
        result_type = Number
        return result_type
    elif isinstance(node, LiteralBoolean):
        result_type = Bool
        return result_type
    elif isinstance(node, LiteralString):
        result_type = String
        return result_type
    elif isinstance(node, Apply):
        fun_type = analyse(node.fn, env, non_generic)
        arg_type = analyse(node.arg, env, non_generic)
        result_type = TypeVariable()
        unify(Function(arg_type, result_type), fun_type, node.location)
        return result_type
    elif isinstance(node, Lambda):
        arg_type = TypeVariable()
        new_env = env.copy()
        new_env[node.v] = arg_type
        new_non_generic = non_generic.copy()
        new_non_generic.add(arg_type)
        result_type = analyse(node.body, new_env, new_non_generic)
        return Function(arg_type, result_type)
    elif isinstance(node, Let):
        defn_type = analyse(node.defn, env, non_generic)
        new_env = env.copy()
        new_env[node.v] = defn_type
        return analyse(node.body, new_env, non_generic)
    elif isinstance(node, Letrec):
        new_type = TypeVariable()
        new_env = env.copy()
        new_env[node.v] = new_type
        new_non_generic = non_generic.copy()
        new_non_generic.add(new_type)
        defn_type = analyse(node.defn, new_env, new_non_generic)
        unify(new_type, defn_type, node.location)
        return analyse(node.body, new_env, non_generic)
    elif isinstance(node, LetrecAnd):
        new_env = env.copy()
        new_non_generic = non_generic.copy()
        for v in node.bindings:
            new_type = TypeVariable()
            new_env[v] = new_type
            new_non_generic.add(new_type)
        for v, (defn, loc) in node.bindings.items():
            v_type = new_env[v]
            defn_type = analyse(defn, new_env, new_non_generic)
            unify(v_type, defn_type, loc, v)
        return analyse(node.body, new_env, new_non_generic)
    elif isinstance(node, Inherit):
        left_row = analyse(node.base, env, non_generic)
        new_env = env.copy()
        update_env_with_obj_type_info(node.base, new_env)
        right_row = analyse(node.child, new_env, non_generic)
        
        # since we work with the copy of base class, we over-approximate it,
        # and its field names can be used with different types within different objects
        result_type = TypeVariable()
        unify(left_row, result_type, node.location)
        unify(right_row, result_type, node.location)
        return result_type
    assert 0, "Unhandled syntax node {0}".format(type(node))


def get_type(name, env, non_generic):
    """Get the type of identifier name from the type environment env.

    Args:
        name: The identifier name
        env: The type environment mapping from identifier names to types
        non_generic: A set of non-generic TypeVariables

    Raises:
        ParseError: Raised if name is an undefined symbol in the type
            environment.
    """
    if name in env:
        return fresh(env[name], non_generic)
    else:
        raise ParseError("Undefined symbol {0}".format(name))


def fresh(t, non_generic):
    """Makes a copy of a type expression.

    The type t is copied. The the generic variables are duplicated and the
    non_generic variables are shared.

    Args:
        t: A type to be copied.
        non_generic: A set of non-generic TypeVariables
    """
    mappings = {}  # A mapping of TypeVariables to TypeVariables

    def freshrec(tp):
        p = prune(tp)
        if isinstance(p, TypeVariable):
            if is_generic(p, non_generic):
                if p not in mappings:
                    mappings[p] = TypeVariable()
                return mappings[p]
            else:
                return p
        elif isinstance(p, TypeOperator):
            return TypeOperator(p.name, [freshrec(x) for x in p.types])
        elif isinstance(p, TypeRowOperator):
            return TypeRowOperator(
                {k: freshrec(v) for k, v in p.fields.items()},
                p.flags
            )
    
    return freshrec(t)


def unify(t1, t2, loc=None, field_name=None):
    """Unify the two types t1 and t2.

    Makes the types t1 and t2 the same.

    Args:
        t1: The first type to be made equivalent
        t2: The second type to be be equivalent

    Returns:
        None

    Raises:
        InferenceError: Raised if the types cannot be unified.
    """
    a = prune(t1)
    b = prune(t2)
    if isinstance(a, TypeVariable):
        if a != b:
            if occurs_in_type(a, b):
                raise InferenceError("recursive unification")
            a.instance = b
    elif (isinstance(a, TypeOperator) or isinstance(a, TypeRowOperator)) and isinstance(b, TypeVariable):
        unify(b, a, loc)
    elif isinstance(a, TypeOperator) and isinstance(b, TypeOperator):
        if a.name != b.name or len(a.types) != len(b.types):
            err_msg = "Type mismatch: {0} != {1}, {2}".format(str(a), str(b), loc)
            if field_name:
                err_msg += f", field '{field_name}'"
            raise InferenceError(err_msg)
        for p, q in zip(a.types, b.types):
            unify(p, q, loc)
    elif isinstance(a, TypeRowOperator) and isinstance(b, TypeRowOperator):
        for k in a.fields:
            if k in b.fields:
                unify(a.fields[k], b.fields[k], loc, k)
        unified_fields = a.fields.copy()
        unified_fields.update(b.fields)
        b.fields = unified_fields
    else:
        assert 0, "Not unified"


def prune(t):
    """Returns the currently defining instance of t.

    As a side effect, collapses the list of type instances. The function Prune
    is used whenever a type expression has to be inspected: it will always
    return a type expression which is either an uninstantiated type variable or
    a type operator; i.e. it will skip instantiated variables, and will
    actually prune them from expressions to remove long chains of instantiated
    variables.

    Args:
        t: The type to be pruned

    Returns:
        An uninstantiated TypeVariable or a TypeOperator
    """
    if isinstance(t, TypeVariable):
        if t.instance is not None:
            t.instance = prune(t.instance)
            return t.instance
    return t


def is_generic(v, non_generic):
    """Checks whether a given variable occurs in a list of non-generic variables

    Note that a variables in such a list may be instantiated to a type term,
    in which case the variables contained in the type term are considered
    non-generic.

    Note: Must be called with v pre-pruned

    Args:
        v: The TypeVariable to be tested for genericity
        non_generic: A set of non-generic TypeVariables

    Returns:
        True if v is a generic variable, otherwise False
    """
    return not occurs_in(v, non_generic)


def occurs_in_type(v, type2):
    """Checks whether a type variable occurs in a type expression.

    Note: Must be called with v pre-pruned

    Args:
        v:  The TypeVariable to be tested for
        type2: The type in which to search

    Returns:
        True if v occurs in type2, otherwise False
    """
    pruned_type2 = prune(type2)
    if pruned_type2 == v:
        return True
    elif isinstance(pruned_type2, TypeOperator):
        return occurs_in(v, pruned_type2.types)
    elif isinstance(pruned_type2, TypeRowOperator):
        return occurs_in(v, pruned_type2.fields.values())
    return False


def occurs_in(t, types):
    """Checks whether a types variable occurs in any other types.

    Args:
        t:  The TypeVariable to be tested for
        types: The sequence of types in which to search

    Returns:
        True if t occurs in any of types, otherwise False
    """
    return any(occurs_in_type(t, t2) for t2 in types)


def update_env_with_obj_type_info(obj, env):
    if isinstance(obj, Identifier):
        if obj.name not in env:
            return
        obj_type = prune(env[obj.name])
        if isinstance(obj_type, TypeRowOperator):
            fields = obj_type.fields
            for v, tp in fields.items():
                env[v] = tp
    elif isinstance(obj, Apply):
        if obj.fn.name not in env:
            return
        obj_type = prune(env[obj.fn.name])
        if isinstance(obj_type, Function):
            return_type = prune(obj_type.types[1])
            if isinstance(return_type, TypeRowOperator):
                fields = return_type.fields
                for v, tp in fields.items():
                    env[v] = tp
    else:
        raise Exception(f'Unexpected type of base: {obj.__class__.__name__}')


# ==================================================================#
# Example code to exercise the above
def try_exp(env, node):
    """Try to evaluate a type printing the result or reporting errors.

    Args:
        env: The type environment in which to evaluate the expression.
        node: The root node of the abstract syntax tree of the expression.

    Returns:
        None
    """
    try:
        t = analyse(node, env)
        print(str(t))
        return str(t)
    except (ParseError, InferenceError) as e:
        print(e)
        return str(e)


def main():
    """The main example program.

    Sets up some predefined types using the type constructors TypeVariable,
    TypeOperator and Function.  Creates a list of example expressions to be
    evaluated. Evaluates the expressions, printing the type or errors arising
    from each.

    Returns:
        None
    """

    var1 = TypeVariable()
    var2 = TypeVariable()

    record_type_2 = TypeRowOperator({'x': var1, 'y': var2})
    null = Letrec("null", Identifier("null"), Identifier("null"))

    my_env = {
        "record": Function(var1, Function(var2, record_type_2)),
        "true": Bool,
        "times": Function(Number, Function(Number, Number)),
    }

    examples = {
        # null example
        Apply(Apply(Identifier("times"), null), null),

        # object with local variable z
        Let("z",
            LiteralNumber(5),
            Let("x",
                Identifier("z"),
                Let("y",
                    Identifier("true"),
                    Apply(Apply(Identifier("record"),
                                Identifier("x")),
                          Identifier("y"))))),

        # simple object withput internal local variables
        Let("x",
            LiteralNumber(3),
            Let("y",
                Identifier("x"),
                Apply(Apply(Identifier("record"),
                            Identifier("y")),
                      Identifier("x")))),

        # cyclic declaration
        # Letrec(x=y and y=x in pair(x,y)) : (var1, var1)
        LetrecAnd(
            {
                "x": Identifier("y"),
                "y": Identifier("x")
            },
            Apply(
                Apply(
                    Identifier("record"),
                    Identifier("x")
                ),
                Identifier("y")
            )
        ),

        LetrecAnd(
            {
                "x": Identifier("z"),
                "z": Identifier("m"),
                "m": Identifier("k"),
                "y": LiteralString("3"),
                "k": LiteralNumber(5),
            },
            Apply(
                Apply(
                    Identifier("record"),
                    Identifier("x")
                ),
                Identifier("y")
            )
        ),

    }

    for example in examples:
        try_exp(my_env, example)


if __name__ == '__main__':
    main()
