from importlib import import_module
import os
import sys
from .dag import Graph


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

    def loadFile(self, filename: str, root: str = "") -> None:
        sfilename = os.path.splitext(os.path.basename(filename))[0]
        directory = os.path.dirname(filename).replace(
            "./", "").strip("/").strip("\\")
        importdir = directory.replace("/", ".").replace("\\", ".")
        toimport = (importdir + ".") + sfilename

        self.modules[filename.lower().lstrip(root).lstrip("/")
                     ] = import_module(toimport)

    def loadDir(self, dirname: str = "plugins") -> None:
        reldir = os.path.dirname(sys.argv[0]) + "./" + dirname
        for root, _, files in os.walk(reldir):
            if "__pycache__" in root:
                continue
            for file in files:
                self.loadFile(root + "/" + file, root)

    def getAttribute(self, attrname: str, custommodulelist: list = None) -> list:
        attributes = []

        if not custommodulelist:
            for module in self.modules:
                omodule = self.modules[module]
                for attributename in self.getAttrs(omodule):
                    if attributename != attrname:
                        continue

                    attribute = getattr(omodule, attributename)

                    attributes.append(attribute)
        else:
            for omodule in custommodulelist:
                for attributename in self.getAttrs(omodule):
                    if attributename != attrname:
                        continue

                    attribute = getattr(omodule, attributename)

                    attributes.append(attribute)

        return attributes

    def getFunction(self, funcname: str, custommodulelist: list = None) -> list:
        return filter(lambda x: str(type(x)) == "<class 'function'>", self.getAttribute(funcname, custommodulelist))

    def getValueOfAttribute(self, module, attrname: str) -> list:
        for attributename in self.getAttrs(module):
            if attributename == attrname:
                attribute = getattr(module, attributename)
                return attribute if str(type(attribute)) != "<class 'function'>" else attribute()

    def getAttrs(self, module) -> list:
        filteredattrs = []

        for attr in dir(module):
            if not attr.startswith('_'):
                filteredattrs.append(attr)

        return filteredattrs

    def loadOrder(self) -> list:
        m = list(self.modules.keys())
        g = Graph(len(self.modules))

        for i, modulen in enumerate(m):
            module = self.modules[modulen]

            ds = self.getValueOfAttribute(module, "dependencies")

            if ds:
                for dependency in ds:
                    g.addEdge(i, m.index(dependency))

            rd = self.getValueOfAttribute(module, "reversedependencies")

            if rd:
                for rdep in rd:
                    g.addEdge(m.index(rdep), i)

        return [self.modules[m[i]] for i in reversed(g.topologicalSort())]

    def setupModules(self) -> None:
        for setup in self.getFunction("setup", self.loadOrder()):
            setup(Context(log=self.log, **self.globals))
