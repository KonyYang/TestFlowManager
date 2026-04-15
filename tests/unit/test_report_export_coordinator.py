from __future__ import annotations

from unittest import mock

import pytest

from src.core.project_context import ProjectContext
from src.features.report_wizard.coordinator.report_export_coordinator import (
    ReportExportCoordinator,
)


class DummyGenerationService:
    def __init__(self):
        self.loaded_projects = []
        self.generated = []

    def load_project_data(self, project_context: ProjectContext):
        """接受 ProjectContext 对象而不是字符串路径"""
        self.loaded_projects.append(project_context)
        return {"report_no": "R123"}

    def create_report_from_template(
        self, header_data, *, output_dir=None, project_context=None
    ):
        """匹配实际 ReportGenerationService 的签名"""
        self.generated.append((header_data, project_context, output_dir))
        if project_context:
            return f"{project_context.project_path}/report.docx"
        return "report.docx"


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
def project_context(tmp_path) -> ProjectContext:
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    return ProjectContext.from_project_path(str(project_dir), dl_number="DL0001")


def test_coordinator_loads_header_data(project_context):
    gen_service = DummyGenerationService()
    updater_service = DummyUpdaterService()
    coord = ReportExportCoordinator(gen_service, updater_service)
    coord.set_project_context(project_context)

    header_data = coord.load_header_data()
    assert header_data["report_no"] == "R123"
    # load_project_data 现在接收的是 ProjectContext 对象
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

    # ensure project_context forwarded
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
