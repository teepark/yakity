from paver.easy import *
from paver.path import path
from paver.setuputils import setup


VERSION = (0, 1, 0, "dev")

setup(
    name="yakity",
    description="A distributable chat server with easy configuration",
    packages=["yakity"],
    scripts=["bin/yakity"],
    version=".".join(filter(None, map(str, VERSION))),
    author="Travis Parker",
    author_email="travis.parker@gmail.com",
    url="http://github.com/teepark/yakity",
    license="BSD",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python",
    ],
    install_requires=['junction'],
)

MANIFEST = (
    "setup.py",
    "paver-minilib.zip",
    "bin/yakity",
)

@task
def manifest():
    path('MANIFEST.in').write_lines('include %s' % x for x in MANIFEST)

@task
@needs('generate_setup', 'minilib', 'manifest', 'setuptools.command.sdist')
def sdist():
    pass

@task
def clean():
    for p in map(path, (
        'yakity.egg-info', 'dist', 'build', 'MANIFEST.in', 'docs/build')):
        if p.exists():
            if p.isdir():
                p.rmtree()
            else:
                p.remove()
    for p in path(__file__).abspath().parent.walkfiles():
        if p.endswith(".pyc") or p.endswith(".pyo"):
            p.remove()

#@task
#def docs():
#    # have to touch the automodules to build them every time since changes to
#    # the module's docstrings won't affect the timestamp of the .rst file
#    sh("find docs/source/greenhouse -name *.rst | xargs touch")
#    sh("cd docs; make html")
#
#@task
#def test():
#    sh("nosetests --processes=8")
