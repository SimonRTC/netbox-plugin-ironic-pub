from django.utils.safestring import mark_safe

class AtelierException(Exception):

    def __init__(self, type, source, exception):
        self._type = type
        self._source = source
        self._exception = exception
    
    @property
    def type(self):
        return self._type
    
    @property
    def source(self):
        return self._source
    
    @property
    def exception(self):
        return self._exception

    @property
    def message(self):
        message = str(self.exception).replace("/", "/<wbr>").replace(",", ",<wbr>")
        return mark_safe(f'Unable to connect to {self.source}:<br>{message}')