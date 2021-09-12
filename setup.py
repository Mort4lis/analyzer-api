import os
from importlib.machinery import SourceFileLoader
from types import ModuleType
from typing import List

from pkg_resources import parse_requirements
from setuptools import setup, find_packages

module_name = 'analyzer'
loader = SourceFileLoader(
    fullname=module_name,
    path=os.path.join(module_name, '__init__.py')
)
module = ModuleType(loader.name)
loader.exec_module(module)


def load_requirements(filename: str) -> List[str]:
    requirements = []
    with open(file=filename, mode='r') as file:
        for requirement in parse_requirements(file.read()):
            extras = ''
            if requirement.extras:
                extras = '[{0}]'.format(','.join(requirement.extras))
            parsed = '{0}{1}{2}'.format(requirement.name, extras, requirement.specifier)
            requirements.append(parsed)
    return requirements


setup(
    name=module_name,
    version=module.__version__,
    author=module.__author__,
    author_email=module.__email__,
    license=module.__license__,
    description=module.__doc__,
    long_description='',
    url='https://github.com/Mort4lis/analyzer-api.git',
    platforms='all',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: Russian',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    python_requires='>=3.8',
    packages=find_packages(exclude=['tests']),
    install_requires=load_requirements('requirements.txt'),
    extras_require={'dev': load_requirements('requirements.dev.txt')},
    entry_points={
        'console_scripts': [
            '{0}-api = {0}.api.__main__:main'.format(module_name),
            '{0}-db = {0}.db.__main__:main'.format(module_name)
        ]
    },
    include_package_data=True
)
