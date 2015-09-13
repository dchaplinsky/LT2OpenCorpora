#!/usr/bin/env python
from setuptools import setup

from lt2opencorpora import __version__

setup(
    name='LT2OpenCorpora',
    version=__version__,
    author='Dmitry Chaplinsky',
    author_email='chaplinsky.dmitry@gmail.com',
    packages=['lt2opencorpora'],
    url='https://github.com/dchaplinsky/LT2OpenCorpora',
    description='Python script to convert Ukrainian morphological dictionary '
                'from LanguageTool project to OpenCorpora forma',
    scripts=['bin/lt_convert.py', 'bin/lt_plot.py'],
    package_data={"lt2opencorpora": ["mapping.csv",
                                     "open_corpora_tagset.xml"]},
    license='MIT license',
    install_requires=[
        'blinker >= 1.3',
        'unicodecsv >= 0.9.4',
        'bz2file >= 0.98',
        'requests',
    ],
    extras_require={
        'plot': ["pydot >= 1.0.2"],
    },
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Text Processing :: Linguistic',
    ],
)
