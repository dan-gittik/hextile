import sys
import pathlib


root = pathlib.Path(__file__).absolute().parent


sys.path.append(str(root.parent))


import hextile


def simple():
    junk = hextile.transpile(root / 'simple.template')
    print(junk.render(n=10))


def multab():
    junk = hextile.transpile(root / 'multab.template')
    print(junk.render(n=10))


def dirs():
    junk = hextile.transpile(root / 'dirs.template')
    junk.render(root=root)


def dirs2():
    junk = hextile.transpile(root / 'dirs2.template')
    junk.render(root=root)


def html():
    junk = hextile.transpile(root / 'index.template')
    print(junk.render(
        components_directory = root / 'components',
        build_directory = root / 'build',
        output_directory = root / 'output',
    ))


scenarios = {
    'simple': simple,
    'multab': multab,
    'dirs': dirs,
    'dirs2': dirs2,
    'html': html,
}


def main(argv):
    if len(argv) != 2 or argv[1] not in scenarios:
        print(f'USAGE: {argv[0]} <{"|".join(scenarios)}>')
        return 1
    scenarios[argv[1]]()


if __name__ == '__main__':
    sys.exit(main(sys.argv))