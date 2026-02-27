from core.controller import BaseController
from machine.models import Documents, ExtractedText
from machine.repositories import DocumentsRepository, ExtractedTextRepository

        
class DocumentsController(BaseController[Documents]):
    def __init__(self, documents_repository: DocumentsRepository):
        super().__init__(model_class=Documents, repository=documents_repository)
        self.documents_repository = documents_repository
        
        
class ExtractedTextController(BaseController[ExtractedText]):
    def __init__(self, extracted_text_repository: ExtractedTextRepository):
        super().__init__(model_class=ExtractedText, repository=extracted_text_repository)
        self.extracted_text_repository = extracted_text_repository