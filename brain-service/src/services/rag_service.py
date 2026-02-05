class RAGService:
    """
    Handles retrieval-augmented generation for conversational context.
    """
    def __init__(self, vector_search, llm_client):
        self.vector_search = vector_search
        self.llm_client = llm_client

    def retrieve_context(self, query: str, last_context: list = None):
        # Use previous context for follow-ups, else search
        if last_context:
            return last_context
        return self.vector_search.search(query)

    def generate_reply(self, message: str, context: list, history: list):
        prompt = open("prompts/response_style.txt").read().format(
            message=message,
            context="\n".join(context),
            history="\n".join([f"{t.role}: {t.message}" for t in history])
        )
        return self.llm_client.generate_response(prompt)
