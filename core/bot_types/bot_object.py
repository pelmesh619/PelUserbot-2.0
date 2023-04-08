import importlib

from .attribute import no_default


class BotObject:
    attributes: list = []

    def __init__(self, *args, **kwargs):

        unused_attrs = list(self.attributes)

        for arg, attr in zip(args, self.attributes):
            setattr(self, attr.name, arg)
            if attr in unused_attrs:
                unused_attrs.remove(attr)

        for attr_name, value in kwargs.items():
            for attr in self.attributes:
                if attr.name == attr_name:
                    setattr(self, attr_name, value)
                    if attr in unused_attrs:
                        unused_attrs.remove(attr)
                    break
            else:
                setattr(self, attr_name, value)

        there_are_no_arguments = []
        for attr in unused_attrs:
            if attr.default == no_default:
                there_are_no_arguments.append(attr)
            else:
                setattr(self, attr.name, attr.default)

        if there_are_no_arguments:
            raise TypeError(
                'Object did not get those arguments: {args}'.format(
                    args=', '.join([i.name for i in there_are_no_arguments])
                )
            )

    def __repr__(self):
        return str(type(self))[8:-2] + '(' + \
               ', '.join([attr.name + '=' + repr(getattr(self, attr.name)) for attr in self.attributes]) + \
               ')'

    def to_dict(self):
        """
        Makes from BotObject dictionary object where keys are attribute's names
        and values are its values
        If object's variable is not in attributes then it remains hidden
        and will be not added

        :return: data: dict
        """

        data = {
            '__module__': self.__class__.__module__,
            '__class__': self.__class__.__name__
        }

        for attr in self.attributes:
            if issubclass(type(getattr(self, attr.name)), BotObject):
                data[attr.name] = getattr(self, attr.name).to_dict()
            else:
                data[attr.name] = getattr(self, attr.name)

        return data

    @classmethod
    def from_dict(cls, data: dict):
        """
        Makes BotObject object from dictionary elements
        Takes keys as attribute's names and values as its values
        If some keys are not in object's attributes, method will assign it and its value

        :param data: dict
        :return: BotObject
        :raise TypeError() if there is not some argument and
        its attribute does not have default value
        """

        arguments = {}
        data = data.copy()

        if data.get('__class__') and data.get('__module__'):
            try:
                module_path = data.get('__module__')
                module_object = importlib.import_module(module_path)
                class_object = getattr(module_object, data.get('__class__'))
                del data['__class__']
                del data['__module__']
            except ImportError:
                class_object = cls
            except SyntaxError:
                class_object = cls
        else:
            class_object = cls

        there_are_no_arguments = []
        if hasattr(class_object, 'attributes'):
            for attr in class_object.attributes:
                if attr.name in data:
                    if isinstance(data[attr.name], dict) and data[attr.name].get('__class__') and \
                            data[attr.name].get('__module__'):
                        arguments[attr.name] = BotObject.from_dict(data[attr.name])
                    else:
                        arguments[attr.name] = data[attr.name]
                    del data[attr.name]
                elif attr.default == no_default:
                    there_are_no_arguments.append(attr)

        for key in data:
            if key in arguments:
                continue

            if isinstance(data[key], dict) and data[key].get('__class__') and data[key].get('__module__'):
                arguments[key] = BotObject.from_dict(data[key])
            else:
                arguments[key] = data[key]

        if there_are_no_arguments:
            raise TypeError(
                'Class "{cls}" did not get those arguments: {args}'.format(
                    cls=class_object,
                    args=', '.join([i.name for i in there_are_no_arguments])
                )
            )

        return class_object(**arguments)


