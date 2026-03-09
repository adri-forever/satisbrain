from typing import Any

def pretty_dict_print(dict_: dict[str, Any], deep: bool = True, level: int = 0):
    indent = level*'\t'
    for key, value in dict_.items():
        if isinstance(value, dict) and deep:
            print(indent+f'{key} :')
            pretty_dict_print(value, deep=True, level=level+1)
        else:
            print(f'{indent}{key} : {value}')

def searchDictionary(dict_: dict[str, Any]):
    pass