class Runnable(BaseSecureRunnable):
    def init(self):
        self.context['counter'] = 0

    def process(self, queries: List[Any]) -> List[Any]:
        return queries
#         c = self.context['counter']
#         self.context['counter'] = c + 1
#         self.context['other'] = f"other_{c}"

#         return [{
#             'index': self.context['counter'],
#             **query
#         } for query in queries]

    def process_stream(self, queries: List[Any]) -> Any:
        # yield from (self.process(query) for query in queries)
        pass
