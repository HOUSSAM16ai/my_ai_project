class Config:
    def __init__(self, description, category, aliases):
        self.description = description
        self.category = category
        self.aliases = aliases

class Tool:
    def __init__(self, name, description, category, aliases, handler):
        self.name = name
        self.config = Config(description, category, aliases)
        self.handler = handler

    def can_execute(self):
        return callable(self.handler)

class ToolBuilder:
    def __init__(self, name):
        self.name = name
        self.description = ""
        self.category = ""
        self.handler = None
        self.aliases = []

    def with_description(self, description):
        self.description = description
        return self

    def with_category(self, category):
        self.category = category
        return self

    def with_handler(self, handler):
        self.handler = handler
        return self

    def with_aliases(self, aliases):
        self.aliases = aliases
        return self

    def build(self):
        if not self.description:
             raise ValueError("Invalid tool configuration: Description required")
        if not self.handler:
             raise ValueError("Invalid tool configuration: Handler required")
        return Tool(self.name, self.description, self.category, self.aliases, self.handler)
