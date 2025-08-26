from enum import Enum

from utils import separate_upper_class


class ExtraEnum(Enum):
    @classmethod
    def get_info(cls, title="", list_str=False):
        str_info = """
        """
        str_info += title
        if list_str:
            for name, member in cls.__members__.items():
                str_info += """
            %s
            """ % (
                    name.lower().replace("_", "."),
                )
        else:
            for name, member in cls.__members__.items():
                str_info += """
            %s: %s
            """ % (
                    member.value,
                    name,
                )
        return str_info

    @classmethod
    def to_choices(cls, string_as_value=False, separate_class_name=False):
        if string_as_value:
            choices = [
                (name.lower().replace("_", "."), name)
                for name, member in cls.__members__.items()
            ]
        elif separate_class_name:
            choices = [
                (separate_upper_class(name), name)
                for name, member in cls.__members__.items()
            ]
        else:
            choices = [
                (member.value, name)
                for name, member in cls.__members__.items()
            ]

        return choices

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls.__members__.values()))

    @classmethod
    def names(cls):
        return [name.lower() for name, _ in cls.__members__.items()]
