class AnalysisPipeline:
    def __init__(self, steps):
        self.steps = steps

    async def execute(self, context):
        try:
            result = {"file": str(context), "status": "success"}
            for step in self.steps:
                result = await step.execute(result)
            return result
        except Exception as e:
            return {"errors": [str(e)]}
