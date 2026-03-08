from typing import Any

def pretty_dict_print(dict_: dict[Any, Any], deep: bool = True, level: int = 0):
    indent = level*'\t'
    for key, value in dict_.items():
        if isinstance(value, dict) and deep:
            print(indent+f'{key} :')
            pretty_dict_print(value, deep=True, level=level+1)
        else:
            print(f'{indent}{key} : {value}')
    
def dict_getmax(d: dict[str, float]):
    mk, m = list(d.items())[0]
    for k, v in d.items():
        if v > m:
            m = v
            mk = k
    return mk, m