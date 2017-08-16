import collections

#WinStructType = collections.namedtuple('WinStructType', ['name'])

#Ptr = collections.namedtuple('Ptr', [''])

class WinStructType(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, self.name)

    def generate_ctypes(self):
        return self.name

class Ptr(object):

    def __init__(self, struct):
        self.type = struct
        self.name = struct.name

    def generate_ctypes(self):
        return "POINTER({0})".format(self.name)

    def __repr__(self):
        return "Ptr({0})".format(repr(self.type))


class WinStruct(object):
    ctypes_type = "Structure"
    def __init__(self, name, pack=None):
        self.name = name
        self.pack = pack
        self.fields = []
        self.typedef = {}

    def add_field(self, field):
        self.fields.append(field)

    def add_typedef(self, name):
        if name in self.typedef:
            raise ValueError("nop")
        self.typedef[name] = self

    def add_ptr_typedef(self, name):
        if name in self.typedef:
            raise ValueError("nop")
        self.typedef[name] = Ptr(self)

    def is_self_referencing(self):
        for type in [f[0] for f in self.fields]:
            if type.name == self.name:
                return True
            if type.name in self.typedef:
                return True
        return False

    def generate_selfref_ctypes_class(self):
        res = ["# Self referencing struct tricks"]
        res += ["""class {0}(Structure): pass""".format(self.name)]
        res += [self.generate_typedef_ctypes()]

        if self.pack:
            res += ["{0}._pack_ = ".format(self.pack)]
        res += ["{0}._fields_ = [".format(self.name)]
        for (ftype, name, nb_rep) in self.fields:
            if  nb_rep == 1:
                res+= ['    ("{0}", {1}),'.format(name, ftype.generate_ctypes())]
            else:
                res+= ['    ("{0}", {1} * {2}),'.format(name, ftype.generate_ctypes(), nb_rep)]
        res += ["]"]
        return "\n".join(res)

    def generate_ctypes_class(self):
        res = "class {0}({1}):\n".format(self.name, self.ctypes_type)
        if self.pack:
            res += "    _pack_ = {0}\n".format(self.pack)
        res += "    _fields_ = [\n"""


        for (ftype, name, nb_rep) in self.fields:
            if  nb_rep == 1:
                res+= '        ("{0}", {1}),\n'.format(name, ftype.generate_ctypes())
            else:
                res+= '        ("{0}", {1} * {2}),\n'.format(name, ftype.generate_ctypes(), nb_rep)
        res += "    ]"
        return res

    def generate_typedef_ctypes(self):
        typedef_ctypes = []
        for typedef_name, value in self.typedef.items():
            str_value = self.name
            if type(value) == Ptr:
                str_value = "POINTER({0})".format(self.name)
            typedef_ctypes += ["{0} = {1}".format(typedef_name, str_value)]
        return "\n".join(typedef_ctypes)

    def generate_ctypes(self):
        if self.is_self_referencing():
            print("{0} is self referencing".format(self.name))
            return self.generate_selfref_ctypes_class() + "\n"

        ctypes_class = self.generate_ctypes_class()
        ctypes_typedef = self.generate_typedef_ctypes()
        return "\n".join([ctypes_class, ctypes_typedef]) + "\n"

class WinUnion(WinStruct):
    ctypes_type = "Union"

class WinEnum(object):
    def __init__(self, name):
        self.name = name
        self.fields = []
        self.typedef = {}

    def add_enum_entry(self, number, name):
        self.fields.append((number, name))

    def add_typedef(self, name):
        if name in self.typedef:
            raise ValueError("nop")
        self.typedef[name] = self

    def add_ptr_typedef(self, name):
        if name in self.typedef:
            raise ValueError("nop")
        self.typedef[name] = Ptr(self)

    # Assert that enum are DWORD
    def generate_ctypes(self):
        #lines = ["{0} = DWORD".format(self.name)]
        lines = []
        for i, name in self.fields:
            lines.append('{0} = EnumValue("{2}", "{0}", {1})'.format(name, "{0:#x}".format(i), self.name))

        lines += ["class {0}(EnumType):".format(self.name)]
        lines += ["    values = [{0}]".format(", ".join([name for i, name in self.fields]))]
        lines += ["    mapper = {{x:x for x in values}}".format(self.name)]

        for typedef_name, value in self.typedef.items():
            str_value = self.name
            if type(value) == Ptr:
                str_value = "POINTER({0})".format(self.name)
            lines += ["{0} = {1}".format(typedef_name, str_value)]
        #lines += ["{0} = {1}".format(t, self.name) for t in self.typedef]
        lines += [""]
        ctypes_class = "\n".join(lines)
        return ctypes_class + "\n"
