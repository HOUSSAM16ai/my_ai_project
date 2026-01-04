class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.aliases = {}

    def register(self, tool):
        if tool.name in self.tools:
            raise ValueError("Tool already registered")
        self.tools[tool.name] = tool
        for alias in tool.config.aliases:
             self.aliases[alias] = tool.name

    def get(self, name):
        if name in self.tools:
            return self.tools[name]
        if name in self.aliases:
            return self.tools[self.aliases[name]]
        return None
