from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', to='rst', format='md')
    long_description += "\n\n" + pypandoc.convert('AUTHORS.md', to='rst', format='md')
except (IOError, ImportError):
    long_description = ''

setup(
    name='wad',
    version='0.1.1',
    description='A tool for detecting technologies used by web applications.',
    long_description=long_description,
    url='https://github.com/CERN-CERT/WAD',
    license='GPLv3',
    author='Sebastian Lopienski',
    author_email='sebastian.lopienski@cern.ch',
    packages=find_packages(),
    include_package_data=True,
    requires=['six'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Security',
        'Topic :: Internet :: WWW/HTTP',
    ],
    entry_points={
        'console_scripts': [
            'wad = wad.__main__:main'
        ]
    },
)
