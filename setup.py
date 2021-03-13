'''Setup script for installing bibtexcleaner through pip.'''
import os
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(name='bibtexcleaner',
      version='0.1',
      description='Abbreviate journals in bibtex databases.',
      classifiers=[
        'Development Status :: Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Bibliographic :: BibTex',
      ],
      package_dir={"": "src"},
      packages=setuptools.find_packages(where="src"),
      python_requires=">=3.2",
      keywords='bibtex abbreviate',
      url='https://github.com/rchiechi/BibTexCleaner',
      author='Ryan C. Chiechi',
      author_email='r.c.chiechi@rug.nl',
      license='MIT',
      install_requires=[
          'bibtexparser>=1.2.0',
          'colorama>=0.4.4',
          'python-Levenshtein>=0.12.2',
          'titlecase>=2.0.0'
      ],
      include_package_data=True,
      scripts = [
        os.path.join("src", 'bibtexcleaner')
        ]
      )
