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

    # Keeps/deletes the elements that pass the given lambda function
    def keep (self, lam):
        for k in list (self.keys ()):
            if not lam(k):
                del (self[k])
    def delete (self, lam):
        self.keep (lambda x: not lam (x))
