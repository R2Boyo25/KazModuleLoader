from importlib import import_module
import os
import sys


class Context:
    def __init__(self, **kwargs):
        self.attrs = kwargs

    def __getattr__(self, name):
        return self.attrs[name]


class Loader:
    def __init__(self, globals: dict = None):
        self.modules = {}
        self.globals = globals if globals else {}
        self.globals["modules"] = self.modules

    def log(self, type, *text):
        if "logger" not in self.globals:
            return

        if not self.globals["logger"]:
            return

        if len(text):
            getattr(self.globals["logger"], type)(" ".join(text))
        else:
            self.globals["logger"].warning(type)

    def setLogger(self, logger):
        self.globals["logger"] = logger

    def loadFile(self, filename: str) -> None:
        sfilename = os.path.splitext(os.path.basename(filename))[0]
        directory = os.path.dirname(filename).replace(
            "./", "").strip("/").strip("\\")
        importdir = directory.replace("/", ".").replace("\\", ".")
        toimport = (importdir + ".") + sfilename

        self.modules[filename.lower()] = import_module(toimport)

    def loadDir(self, dirname: str = "plugins") -> None:
        reldir = os.path.dirname(sys.argv[0]) + "./" + dirname
        for root, _, files in os.walk(reldir):
            if "__pycache__" in root:
                continue
            for file in files:
                self.loadFile(root + "/" + file)

    def getFunction(self, funcname: str) -> list:
        functions = []

        for module in self.modules:
            omodule = self.modules[module]
            for attributename in self.getAttrs(omodule):
                if attributename != funcname:
                    continue

                attribute = getattr(omodule, attributename)

                if str(type(attribute)) != "<class 'function'>":
                    continue

                functions.append(attribute)

        return functions

    def getAttrs(self, module) -> list:
        filteredattrs = []

        for attr in dir(module):
            if not attr.startswith('_'):
                filteredattrs.append(attr)

        return filteredattrs

    def setupModules(self):
        for setup in self.getFunction("setup"):
            setup(Context(log=self.log, **self.globals))
