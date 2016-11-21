from setuptools import setup, find_packages

setup(
    name="kingjuke",
    version="0.1",
    author="Luka Peschke",
    author_email="luka.peschke@epitech.eu",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    entry_points= {
        "console_scripts": ["kingjuke-server=kingjuke.app:main"]
    },
    install_requires=[
        'falcon',
        'gunicorn',
        'pafy',
        'python-vlc',
    ],
)
