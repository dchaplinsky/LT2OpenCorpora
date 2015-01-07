from setuptools import setup
import os

from lt2opencorpora import __version__

with open(os.path.join(os.path.dirname(__file__),
                       "requirements.txt")) as req_file:
    requirements = req_file.read().splitlines()

setup(
    name='LT2OpenCorpora',
    version=__version__,
    author='Dmitry Chaplinsky',
    author_email='chaplinsky.dmitry@gmail.com',
    packages=['lt2opencorpora'],
    url='https://github.com/dchaplinsky/LT2OpenCorpora',
    description='Python script to convert ukrainian morphological dictionary '
                'from LanguageTool project to OpenCorpora forma',
    scripts=['bin/lt_convert.py', 'bin/lt_plot.py'],
    package_data={"lt2opencorpora": ["mapping.csv",
                                     "open_corpora_tagset.xml"]},
    install_requires=requirements
)
