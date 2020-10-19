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
    """ Record/Row constructor """

    def __init__(self, fields):
        """ fields: dict(field_name: str, field: Field) """
        self.fields = fields

    def __str__(self):
        num_types = len(self.fields)
        if num_types == 0:
            return '{}'
        name_type_pairs = [f'{field}' for _, field in self.fields.items()]
        return "{{{0}}}".format(', '.join(name_type_pairs))


class Field(object):
    """ Class that keeps information about the type and flags of the field,
        and maybe about location.
    """
    def __init__(self, field_name, field_type, flags):
        """ field_flag = '!' # required and needs to exist on the right oder left in the inheritance chain
                        |'?' # optional field 
        """
        self.name = field_name
        self.type = field_type
        self.flags = flags
        self.location = None
    
    def __str__(self):
        return "{name}: {t}".format(name=self.name, t=self.type)
    
    def __repr__(self):
        return "Field(name={name}, type={t}, flags={flags})".format(
            name = self.name,
            t = self.type,
            flags = self.flags
        )
    

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
