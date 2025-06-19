from setuptools import setup

setup(
    name='tramp',
    version='0.1',
    py_modules=['tramp'],
    entry_points={
        'console_scripts': [
            'tramp = tramp:main',
        ],
    },
)
