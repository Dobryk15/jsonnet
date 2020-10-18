# =======================================================#
# Types and type constructors
import copy

class TypeVariable(object):
    """A type variable standing for an arbitrary type.

    All type variables have a unique id, but names are only assigned lazily,
    when required.
    """

    next_variable_id = 0

    def __init__(self):
        self.id = TypeVariable.next_variable_id
        TypeVariable.next_variable_id += 1
        self.instance = None
        self.__name = None

    next_variable_name = 'a'

    @property
    def name(self):
        """Names are allocated to TypeVariables lazily, so that only TypeVariables
        present after analysis consume names.
        """
        if self.__name is None:
            self.__name = TypeVariable.next_variable_name
            TypeVariable.next_variable_name = chr(
                ord(TypeVariable.next_variable_name) + 1)
        return self.__name

    def __str__(self):
        if self.instance is not None:
            return str(self.instance)
        else:
            return self.name

    def __repr__(self):
        return "TypeVariable(id = {0})".format(self.id)
    

class TypeRowOperator(object):
    """Record constructor
        fields - dict(field_name, field_type)
        flags - dict(field_name, field_flag), where:
            field_flag = 'r' # required and needs to be overloaded in each child obj
                        |'ol' # overloaded but still should be presented in other child objects 
                        |'o' # optional (field in child class that may be in base class)
            flags are used only for special fields
    """

    def __init__(self, fields, flags=None):
        self.fields = fields
        if not flags:
            self.flags = {}
        else:
            self.flags = flags

    def __str__(self):
        num_types = len(self.fields)

        if num_types == 0:
            return '{}'

        name_type_pairs = [f"{x[0]}: {x[1]}" for x in self.fields.items()]

        return "{{{0}}}".format(', '.join(name_type_pairs))
    

class TypeOperator(object):
    """An n-ary type constructor which builds a new type from old"""

    def __init__(self, name, types):
        self.name = name
        self.types = types

    def __str__(self):
        num_types = len(self.types)
        if num_types == 0:
            return self.name
        elif num_types == 2:
            return "({0} {1} {2})".format(str(self.types[0]), self.name, str(self.types[1]))
        else:
            return "{0} {1}" .format(self.name, ' '.join(self.types))
    

class Function(TypeOperator):
    """A binary type constructor which builds function types"""

    def __init__(self, from_type, to_type):
        super(Function, self).__init__("->", [from_type, to_type])


# =============================================================#
# Basic types, constructed with a nullary type constructor

Number = TypeOperator("number", [])  # Basic number: int, float
Bool = TypeOperator("boolean", [])  # Basic boolean
String = TypeOperator("string", [])  # string
