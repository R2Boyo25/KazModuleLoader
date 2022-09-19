from importlib import import_module
import os
import sys
from .dag import Graph


class Context:
    def __init__(self, **kwargs):
        self.attrs = kwargs

    def __getattr__(self, name):
        return self.attrs[name]

def walkDir(dirname: str) -> list:
    out = []

    if not os.path.exists(dirname):
        return []

    entries = os.listdir(dirname)

    index = 0
    while index < len(entries):

        entry = dirname + "/" + entries[index]

        if os.path.isdir(entry):

            if entry.endswith("__pycache__"):
                index += 1
                continue

            if os.path.exists(entry + "/__init__.py"):
                out.append(entry)
            
            else:
                entries = [*entries, *[entry.lstrip(dirname + "/") + "/" + e for e in os.listdir(entry)]]

        elif os.path.isfile(entry):

            if entry.lower().endswith(".py"):
                out.append(entry)
        
        index += 1

    return out

class Loader:
    def __init__(self, globals: dict = None):
        self.modules = {}
        self.globals = globals if globals else {}
        self.globals["modules"] = self.modules

    def log(self, type, *text) -> None:
        if "logger" not in self.globals:
            return

        if not self.globals["logger"]:
            return

        if len(text):
            getattr(self.globals["logger"], type)(" ".join(text))
        else:
            self.globals["logger"].warning(type)

    def setLogger(self, logger) -> None:
        self.globals["logger"] = logger

    def loadFile(self, filename: str) -> None:
        sfilename = os.path.splitext(os.path.basename(filename))[0]
        directory = os.path.dirname(filename).replace(
            "./", "").strip("/").strip("\\")
        importdir = directory.replace("/", ".").replace("\\", ".")
        toimport = (importdir + ".") + sfilename

        self.modules[os.path.basename(filename)
                     ] = import_module(toimport)

    def loadDir(self, dirname: str = "plugins") -> None:
        reldir = os.path.dirname(sys.argv[0]) + "./" + dirname
        for plugin in walkDir(reldir):
            self.loadFile(plugin)

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

            if not ds:
                continue

            for dependency in ds:
                g.addEdge(i, m.index(dependency))

        return [self.modules[m[i]] for i in reversed(g.topologicalSort())]

    def setupModules(self) -> None:
        for setup in self.getFunction("setup", self.loadOrder()):
            setup(Context(log=self.log, **self.globals))
