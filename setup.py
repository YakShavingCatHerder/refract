from setuptools import setup

setup(
    name='refract',
    version='0.1',
    py_modules=['refract'],
    entry_points={
        'console_scripts': [
            'refract = refract:main',
        ],
    },
)
