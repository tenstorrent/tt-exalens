import tt_util as util
from sortedcontainers import SortedSet

# Parent class for all objects (ops, queues, buffers, streams...)
class TTObject:
    def __str__(self):
        return f"{self.id()}:{type(self).__name__}"
    def __repr__(self):
        return self.__str__()
    def id (self):
        return self._id # Assume children have the _id
    def __lt__(self, other):
        return self.id() < other.id()

# Storage for sets of objects
class TTObjectSet (SortedSet):
    def __str__ (self):
        str_list = [ s.__str__() for s in self ]
        if len (self) > 0:
            return "{ " + ", ".join (str_list) + " }"
        else:
            return "{ }"
    def __repr__(self):
        return f"[{len (self)}] {self.__str__()}"

    # Constructs a TTObjectSet from an iterable
    @classmethod
    def fromiterable(cls, S):
        return cls({ b : None for b in S })

    # Keeps/deletes the elements that pass the given lambda function
    def keep (self, lam):
        for k in list (self):
            if not lam(k):
                self.remove(k)
    def delete (self, lam):
        self.keep (lambda x: not lam (x))

    # Prints a simple comparison between sets
    def compare (self, other):
        print (f"  len(self)={len(self)} len(other)={len(other)}")
        print (f"  self - other: {self - other}")
        print (f"  other - self: {other - self}")

    # Returns the first element
    def first (self):
        if len(self):
            return next(iter(self))
        else:
            return None

    # Finds and returns an element by id
    def find_id (self, id):
        for s in self:
            if s.id() == id:
                return s
        return None

    # Temporary interface
    def id_filter (id):
        def _id_filter(elem):
            if not id: return True
            return id == elem.id()
        return _id_filter
    def filter (self, lam):
        ret_val = self.copy()
        ret_val.keep(lam)
        return ret_val
    def print (self, *args):
        for elem in self:
            for keyname in args:
                if hasattr(elem, keyname):
                    print (f"{getattr(elem, keyname)}", end=", ")
            print()
    def print_table (self, *args):
        table=util.TabulateTable(list ( { "key_name" : keyname, "title" : keyname, 'formatter': None } for keyname in args))
        for elem in self:
            elem_dict = { "_id" : elem.id() }
            table.add_row ("-", elem_dict)
        print(table)

# Example run command
def run(args, context, ui_state = None):
    qid = args[1] if len(args)>1 else None
    QS = context.netlist.queues
    OS = TTObjectSet

    qs = QS.filter (OS.id_filter(qid))

    qs.print_table("_id", "_id", "_id")

