import tt_util as util
from ordered_set import OrderedSet

# Parent class for all objects (ops, queues, buffers, streams...)
class TTObject:
    def __str__(self):
        return f"{self.id()}:{type(self).__name__}"
    def id (self):
        return self._id # Assume children have the _id

# Storage for sets of objects
class TTObjectSet (OrderedSet):
    def __str__ (self):
        str_list = [ s.__str__() for s in self ]
        if len (self) > 0:
            return "{ " + ", ".join (str_list) + " }"
        else:
            return "{ }"

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
        return next(iter(self))

    # Finds and returns an element by id
    def find_id (self, id):
        for s in self:
            if s.id() == id:
                return s
        return None
