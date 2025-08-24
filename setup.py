from setuptools import setup

setup(
    name='refract',
    version='0.1.0',
    description='Lightweight Virtualenv Manager',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Shawn',
    py_modules=['refract'],
    entry_points={
        'console_scripts': [
            'refract = refract:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.7',
)
