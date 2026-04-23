"""Application-facing Office facade skeleton."""

from __future__ import annotations

from .document_pipeline import DocumentPipeline
from .engine_policy import OfficeEnginePolicy
from .excel_runtime import ExcelRuntime
from .models import OfficeDocumentRequest, OfficeSessionConfig
from .outlook_runtime import OutlookRuntime
from .runtime_manager import OfficeRuntimeManager
from .session import OfficeSession
from .word_runtime import WordRuntime


class OfficeFacade:
    """Shared entry point for future Office/document migrations."""

    def __init__(
        self,
        runtime_manager: OfficeRuntimeManager | None = None,
        engine_policy: OfficeEnginePolicy | None = None,
        pipeline: DocumentPipeline | None = None,
    ) -> None:
        self.runtime_manager = runtime_manager or OfficeRuntimeManager()
        self.engine_policy = engine_policy or OfficeEnginePolicy()
        self.pipeline = pipeline or DocumentPipeline()
        self._register_default_runtimes()

    def open_word_document(self, path: str, *, read_only: bool = False, require_fidelity: bool = True):
        request = OfficeDocumentRequest(
            path=path,
            engine=self.engine_policy.choose_engine(path, require_fidelity=require_fidelity),
            read_only=read_only,
        )
        session = OfficeSession(self.runtime_manager, "word")
        return self.pipeline.run(session, lambda app: app.Documents.Open(request.path, ReadOnly=request.read_only))

    def open_excel_document(self, path: str, *, read_only: bool = False, require_fidelity: bool = True):
        request = OfficeDocumentRequest(
            path=path,
            engine=self.engine_policy.choose_engine(path, require_fidelity=require_fidelity),
            read_only=read_only,
        )
        session = OfficeSession(self.runtime_manager, "excel")
        return self.pipeline.run(session, lambda app: app.Workbooks.Open(request.path, ReadOnly=request.read_only))

    def create_session(self, runtime_name: str, config: OfficeSessionConfig | None = None) -> OfficeSession:
        _ = config
        return OfficeSession(self.runtime_manager, runtime_name)

    def mutate_excel_workbook(
        self,
        file_path: str,
        operation,
        *,
        data_only: bool = False,
        read_only: bool = False,
        save: bool = True,
    ):
        """Open an existing workbook, mutate it, then save via openpyxl."""
        return self.pipeline.run_openpyxl_workbook(
            file_path,
            operation,
            data_only=data_only,
            read_only=read_only,
            save=save,
        )

    def with_excel_workbook(
        self,
        file_path: str,
        operation,
        *,
        read_only: bool = False,
        save: bool = True,
    ):
        """Open an Excel workbook via COM, run an operation, then close and release."""
        session = self.create_session("excel")
        handle = session.acquire()
        try:
            excel_app = handle.application
            workbook = excel_app.Workbooks.Open(file_path, ReadOnly=read_only)
            try:
                result = operation(workbook)
                if save and not read_only:
                    workbook.Save()
                return result
            finally:
                workbook.Close(SaveChanges=False)
        finally:
            session.release()

    def with_word_document(
        self,
        file_path: str,
        operation,
        *,
        read_only: bool = False,
        save: bool = True,
    ):
        """Open a Word document, run an operation, then close and release.

        Args:
            file_path: Path to the Word document
            operation: Callable that receives a win32com Document object
            read_only: Whether to open in read-only mode (default: False)
            save: Whether to save changes after operation (default: True)

        Returns:
            The result of the operation callable
        """
        session = self.create_session("word")
        handle = session.acquire()
        try:
            word_app = handle.application
            doc = word_app.Documents.Open(file_path, ReadOnly=read_only)
            try:
                result = operation(doc)
                if save and not read_only:
                    doc.Save()
                return result
            finally:
                doc.Close(SaveChanges=False)  # Already saved above if needed
        finally:
            session.release()

    def mutate_word_document(
        self,
        file_path: str,
        operation,
        *,
        read_only: bool = False,
        save: bool = True,
    ):
        """Open an existing Word document, mutate it via COM, then save.

        Compatibility wrapper for write-oriented callers. New read-only and
        write workflows should share with_word_document(...) so document
        lifecycle policy has one implementation.
        """
        return self.with_word_document(
            file_path,
            operation,
            read_only=read_only,
            save=save,
        )

    def _register_default_runtimes(self) -> None:
        if not self.runtime_manager.has_provider("word"):
            self.runtime_manager.register_provider(WordRuntime())
        if not self.runtime_manager.has_provider("excel"):
            self.runtime_manager.register_provider(ExcelRuntime())
        if not self.runtime_manager.has_provider("outlook"):
            self.runtime_manager.register_provider(OutlookRuntime())
