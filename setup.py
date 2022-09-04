from setuptools import setup


setup(
    name="clifs",
    version="0.1.0",
    author="Felix Segerer",
    packages=["clifs", "clifs.plugins", "clifs.plugins.backup"],
    license="LICENSE",
    description="Command line interface for basic file system operations.",
    entry_points={
        "console_scripts": [
            "clifs = clifs.__main__:main",
        ],
        "clifs_plugins": [
            "tree = clifs.plugins.tree:DirectoryTree",
            "du = clifs.plugins.disc_usage:DiscUsageExplorer",
            "copy = clifs.plugins.como:FileCopier",
            "move = clifs.plugins.como:FileMover",
            "del = clifs.plugins.delete:FileDeleter",
            "ren = clifs.plugins.rename:FileRenamer",
            "backup = clifs.plugins.backup.backup:FileSaver"
        ],
    },
)
