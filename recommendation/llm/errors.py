class RecommendationLLMError(RuntimeError):
    pass


# Backward-compatible alias used by graph nodes
DevelopmentLLMError = RecommendationLLMError
