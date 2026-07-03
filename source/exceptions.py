class WriteupError(Exception):
    pass

class StorageError(WriteupError):
    pass

class MarkdownGenerationError(WriteupError):
    pass

class ApiAuthError(WriteupError):
    pass

class TranslationError(WriteupError):
    pass
