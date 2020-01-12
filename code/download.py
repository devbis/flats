import js2py

import requests


def main():
    with requests.get(
        'https://www.avito.ru/s/cc/'
        '0cfed52cab4c417618b16cf145dfa467b3180549.js',
    ) as r:
        python = js2py.translate_js(r.text)
        # with open('secret.js', 'rt') as f:
        #     content = f.read()
        #
        #     python = js2py.translate_js(content)
        #     # context = js2py.EvalJs({
        #     #     'decodeURI': unquote,
        #     # })
        #     # f = context.(content)
        print(python)


main()
