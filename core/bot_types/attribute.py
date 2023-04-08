from typing import Union


class NoDefault:
    def __repr__(self):
        return 'core.bot_types.attribute.no_default'


no_default = NoDefault()


class Attribute:
    def __init__(self, name: str, attr_type: Union[type, object], default=no_default):
        self.name = name
        self.type = attr_type
        self.default = default

    @classmethod
    def from_dict(cls, raw_data: dict):
        data = {
            'name': raw_data.get('name'),
            'attr_type': raw_data.get('attr_type'),
            'default': raw_data.get('default', no_default)
        }

        if data['name'] is None and data['attr_type'] is None:
            raise AttributeError('Attribute does not have a name and an attr_type')
        if data['name'] is None:
            raise AttributeError('Attribute does not have a name')
        if data['attr_type'] is None:
            raise AttributeError('Attribute does not have an attr_type')

        return Attribute(**data)

    def __repr__(self):
        return f'{__name__}.Attribute(name="{self.name}", ' + \
               f'attr_type={self.type}, ' + \
               f'default={self.default.__repr__()})'
