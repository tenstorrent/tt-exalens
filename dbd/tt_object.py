# Parent class for all objects (ops, queues, buffers, streams...)
class TTObject:
    def __str__(self):
        return f"{type(self).__name__}: id: {self.id()}"
    def id (self):
        return self._id

# Storage for sets of objects
# Using dicts as they are ordered
class TTObjectSet (dict):
    def __str__ (self):
        str_list = [ s.__str__() for s in self ]
        return ", ".join (str_list)

    def add (self, item):
        self[item] = None

    # Keeps/deletes the elements that pass the given lambda function
    def keep (self, lam):
        for k in list (self.keys ()):
            if not lam(k):
                del (self[k])
    def delete (self, lam):
        self.keep (lambda x: not lam (x))

    def compare (self, other):
        selfset = set(self.items())
        otherset = set(other.items())
        print (f"len(self)={len(self)} len(other)={len(other)}")
        print (selfset - otherset)
        print (otherset - selfset)

    # Returns the first element
    def first (self):
        return next(iter(self))

    def __setitem__(self, key, value):
        if value is not None:
            raise TypeError (f"TTObjectSet: Cannot assign value to the set element")
        else:
            return super().__setitem__(key, value)
