import js2py
from urllib.parse import unquote


def main():
    print(js2py.EvalJs({
        'document': {'write': print}
    }).eval(
        """
    document.write('test')
    """
    ))
    # with open('check_res.py', 'rt') as f:
    #     res = exec(f.read(), {
    #         'decodeURI': lambda x: unquote(x.value),
    #         'window': {},
    #         'document': {'cookie': ''},
    #         'setTimeout': lambda x, y, *args: print(x(y)),
    #         'Image': lambda *args: print(*args)
    #     })
    #     print(res)

main()
