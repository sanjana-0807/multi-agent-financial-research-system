from task import ResearchTask

class ResearchAgent:
    def __init__(self):
        self.task = ResearchTask()

    def run(self, query):
        return self.task.execute(query)


if __name__ == "__main__":
    agent = ResearchAgent()
    result = agent.run("Tesla revenue")
    print(result)