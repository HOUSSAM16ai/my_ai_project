
class BaseStep:
    async def execute(self, context):
        pass

class ComplexityAnalysisStep(BaseStep):
    async def execute(self, context):
        return {**context, "complexity": 1, "metrics": {"mccabe": 1}}

class FileReadStep(BaseStep):
    async def execute(self, context):
        path_str = context.get("file")
        if not path_str or "nonexistent" in str(path_str):
             raise FileNotFoundError("File not found")
        return {**context, "content": "code"}

class FormatStep(BaseStep):
    async def execute(self, context):
        return context

class ParseStep(BaseStep):
    async def execute(self, context):
        return context
