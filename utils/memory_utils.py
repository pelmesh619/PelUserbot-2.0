class MemoryStr(str):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._value = None
        self._measure = None

    @property
    def measure(self):
        pass

    @measure.getter
    def measure(self):
        return self._measure

    @measure.setter
    def measure(self, value):
        self._measure = value

    @property
    def value(self):
        pass

    @value.getter
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


def memory_to_string(memory_value, app, measure=None, round_value=2, lang_code=None):
    sizes = ['b', "kb", "mb", "gb", "tb"]
    count = 0
    if measure != sizes[0]:
        while (memory_value > 1024 or measure is not None) and count < len(sizes):
            memory_value /= 1024
            if measure == sizes[count]:
                break
            count += 1

    string = MemoryStr(str(round(memory_value, round_value)) + ' ' +
                       app.get_core_string(f'memory_{sizes[count]}', lang_code=lang_code))

    string.value = memory_value
    string.measure = sizes[count]

    return string
