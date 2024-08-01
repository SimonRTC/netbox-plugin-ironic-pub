from django.utils.safestring import mark_safe
import re

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
        split = re.split(' |-|/', str(self.exception))
        max_length = max(len(item) for item in split)
        font_size = min(0.875, round(40 * 0.875 / max_length, 3))
        return mark_safe(f'Unable to connect to {self.source}:<br><div style="font-size: {font_size}rem;">{str(self.exception).replace("/", "/<wbr>")}</div>')