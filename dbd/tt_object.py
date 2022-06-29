# Parent class for all objects (ops, queues, buffers, streams...)
class TTObject:
    def __str__(self):
        return f"{type(self).__name__}: id: {self.id()}"
    def id (self):
        return self._id