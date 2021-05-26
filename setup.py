from setuptools import setup


setup(
    name='clifs',
    version='0.1.0',
    author='Felix Segerer',
    packages=['clifs'],
    license='LICENSE',
    description='Command line interface for basic file system operations.',
    entry_points={
        'console_scripts': [
            'clifs = clifs.__main__:main',
        ],
        'clifs_plugins': [
            'tree = clifs.plugins.tree:DirectoryTree',
        ],
     }
)