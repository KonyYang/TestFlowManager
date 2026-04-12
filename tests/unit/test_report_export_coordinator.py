from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import ModuleType
import shutil
import uuid
from unittest import mock

import pytest

from src.core.project_context import ProjectContext

tmp_gen_dir = Path(tempfile.gettempdir()) / "win32com_gen_py"
tmp_gen_dir.mkdir(parents=True, exist_ok=True)

win32com_module = ModuleType("win32com")
win32com_client_module = ModuleType("win32com.client")
win32com_gencache_module = ModuleType("win32com.client.gencache")

win32com_gencache_module.__gen_path__ = str(tmp_gen_dir)

def _get_generate_path():
    tmp_gen_dir.mkdir(parents=True, exist_ok=True)
    init_file = tmp_gen_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")
    return str(tmp_gen_dir)

win32com_gencache_module.GetGeneratePath = _get_generate_path
win32com_gencache_module.Rebuild = lambda: None

win32com_client_module.gencache = win32com_gencache_module
win32com_client_module.dynamic = ModuleType("win32com.client.dynamic")

win32com_module.client = win32com_client_module

sys.modules["win32com"] = win32com_module
sys.modules["win32com.client"] = win32com_client_module
sys.modules["win32com.client.gencache"] = win32com_gencache_module
sys.modules["win32com.client.dynamic"] = win32com_client_module.dynamic

from src.features.report_wizard.coordinator.report_export_coordinator import (
    ReportExportCoordinator,
)


class DummyGenerationService:
    def __init__(self):
        self.loaded_projects = []
        self.generated = []

    def load_project_data(self, project_context: ProjectContext):
        self.loaded_projects.append(project_context)
        return {"report_no": "R123"}

    def create_report_from_template(
        self,
        header_data,
        *,
        project_context: ProjectContext,
        output_dir=None,
    ):
        self.generated.append((header_data, project_context, output_dir))
        return f"{project_context.project_path}/report.docx"


class DummyUpdaterService:
    def __init__(self):
        self.updated = []
        self.last_context = None

    def set_project_context(self, project_context):
        self.last_context = project_context

    def update_equipment_list(self, report_path: str):
        self.updated.append(report_path)
        return True


@pytest.fixture
def project_context() -> ProjectContext:
    base_dir = Path("tmp_pytest_env") / "project_context" / str(uuid.uuid4())
    project_dir = base_dir / "proj"
    project_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield ProjectContext.from_project_path(str(project_dir), dl_number="DL0001")
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_coordinator_loads_header_data(project_context):
    gen_service = DummyGenerationService()
    updater_service = DummyUpdaterService()
    coord = ReportExportCoordinator(gen_service, updater_service)
    coord.set_project_context(project_context)

    header_data = coord.load_header_data()
    assert header_data["report_no"] == "R123"
    assert gen_service.loaded_projects == [project_context]


def test_coordinator_requires_context_for_generation(project_context):
    gen_service = DummyGenerationService()
    updater_service = DummyUpdaterService()
    coord = ReportExportCoordinator(gen_service, updater_service)
    coord.set_project_context(project_context)

    header_data = mock.Mock()
    output_path = coord.create_report_from_template(header_data, output_dir="out/")
    assert "report.docx" in output_path
    assert gen_service.generated

    # ensure project_path/context forwarded
    hdr, context_arg, dir_arg = gen_service.generated[-1]
    assert context_arg == project_context
    assert dir_arg == "out/"

def test_coordinator_update_equipment_calls_service(project_context):
    gen_service = DummyGenerationService()
    updater_service = DummyUpdaterService()
    coord = ReportExportCoordinator(gen_service, updater_service)
    coord.set_project_context(project_context)

    result = coord.update_equipment_list("/dummy/report.docx")
    assert result is True
    assert updater_service.updated == ["/dummy/report.docx"]
    assert updater_service.last_context == project_context
