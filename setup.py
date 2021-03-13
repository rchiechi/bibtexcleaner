'''Setup script for installing bibtexcleaner through pip.'''
from setuptools import setup

setup(name='bibtexcleaner',
      version='0.1',
      description='Abbreviate journals in bibtex databases.',
      long_description='An interactive script to clean and abbreviate entries in bibtex databases',
      classifiers=[
        'Development Status :: Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Bibliographic :: BibTex',
      ],
      keywords='bibtex abbreviate',
      url='https://github.com/rchiechi/BibTexCleaner',
      author='Ryan C. Chiechi',
      author_email='r.c.chiechi@rug.nl',
      license='MIT',
      packages=['btcleaner'],
      install_requires=[
          'bibtexparser',
          'colorama',
          'python-levenshtein',
          'titlecase'
      ],
      include_package_data=True,
      zip_safe=False)
