import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

from src.core.config_manager import config_manager
from src.core.logger import logger
from src.core.project_context import ProjectContext
from src.features.ltr_manager.service.application_processing.data_extractor import (
    LTRApplicationDataExtractor,
)
from src.features.ltr_manager.utils.field_config_loader import LTRFieldConfigLoader


@dataclass(frozen=True)
class ProjectOpenResult:
    project_context: ProjectContext
    json_file_path: str
    project_data: Dict
    created_application_data: bool = False


class ProjectOpenService:
    """处理打开项目时的项目数据补建与上下文准备。"""

    def resolve_default_project_path(self) -> str:
        default_project_path = config_manager.get_path("default_project_path", "")
        if default_project_path and os.path.exists(default_project_path):
            return default_project_path
        return ""

    def prepare_project(self, project_path: str) -> ProjectOpenResult:
        json_file_path, created = self._ensure_project_data_file(project_path)
        project_data = self._load_project_data(json_file_path)
        dl_number = project_data.get("DL") or os.path.basename(project_path)
        project_context = ProjectContext.from_project_path(project_path, dl_number)
        return ProjectOpenResult(
            project_context=project_context,
            json_file_path=json_file_path,
            project_data=project_data,
            created_application_data=created,
        )

    def _ensure_project_data_file(self, project_path: str) -> tuple[str, bool]:
        json_files = sorted(
            [f for f in os.listdir(project_path) if f.endswith(".json")]
        )
        if json_files:
            return os.path.join(project_path, json_files[0]), False

        logger.info(f"在项目路径 {project_path} 中未找到JSON文件，开始创建新的application_data.json文件")
        dl_number = os.path.basename(project_path)
        json_file_path = os.path.join(project_path, "application_data.json")
        test_request_data = self._extract_test_request_data(project_path, dl_number)
        application_data = self._build_application_data(dl_number, test_request_data)

        with open(json_file_path, "w", encoding="utf-8") as handle:
            json.dump(application_data, handle, ensure_ascii=False, indent=4)
        logger.info(f"Created new application_data.json file: {json_file_path}")
        return json_file_path, True

    def _extract_test_request_data(self, project_path: str, dl_number: str) -> Dict:
        submitted_material_path = self._resolve_submitted_material_path(project_path, dl_number)
        if not submitted_material_path:
            logger.info(f"未找到以DL编号'{dl_number}'开头的子文件夹，跳过查找Submitted Material文件夹并继续后续逻辑")
            return {}

        logger.info(f"检查Submitted Material文件夹: {submitted_material_path}")
        if not os.path.exists(submitted_material_path):
            logger.info(f"Submitted Material文件夹不存在: {submitted_material_path}")
            return {}

        logger.info("Submitted Material文件夹存在，开始搜索包含'test request'关键字的.docx文件")
        docx_files = []
        for file_name in os.listdir(submitted_material_path):
            if not file_name.lower().endswith(".docx"):
                continue
            lowered = file_name.lower()
            if ("test" in lowered and "request" in lowered) or ("e-3718" in lowered and "request" in lowered):
                docx_files.append(file_name)

        if not docx_files:
            logger.info("在Submitted Material文件夹中未找到包含'test request'关键字的.docx文件")
            return {}

        logger.info(f"找到 {len(docx_files)} 个匹配的.docx文件: {docx_files}")
        docx_file_path = os.path.normpath(os.path.join(submitted_material_path, docx_files[0]))
        logger.info(f"从文件中提取信息: {docx_file_path}")
        extracted = self._extract_info_from_test_request(docx_file_path)
        logger.info(f"提取到的数据: {extracted}")
        return extracted

    def _resolve_submitted_material_path(self, project_path: str, dl_number: str) -> Optional[str]:
        for item in sorted(os.listdir(project_path)):
            item_path = os.path.join(project_path, item)
            if os.path.isdir(item_path) and item.startswith(dl_number):
                return os.path.normpath(os.path.join(item_path, "Submitted Material"))
        return None

    def _build_application_data(self, dl_number: str, test_request_data: Dict) -> Dict:
        config_loader = LTRFieldConfigLoader()
        field_mapping = config_loader.load_application_field_mapping()
        application_data = {}

        for field in field_mapping:
            key = field["key"]
            if key == "DL":
                application_data[key] = dl_number
            elif key in test_request_data:
                application_data[key] = test_request_data[key]
            else:
                application_data[key] = self._get_default_field_value(key)

        application_data["status"] = "new"
        application_data["error"] = ""
        application_data["selected_filename"] = test_request_data.get("selected_filename", "")
        application_data["file_path"] = test_request_data.get("file_path", "")
        return application_data

    def _get_default_field_value(self, key: str) -> str:
        if key == "project_leader":
            return config_manager.get_default("project_leader", "")
        if key == "sub_contract":
            return "Yes"
        if key == "test_result":
            return "In progress"
        if key == "test_type":
            return "Partial Qualification"
        if key == "lab_performing_the_tests":
            return "Dongguan"
        if key == "condition_of_samples_when_received":
            return "Acceptable"
        if key == "project_type":
            return "NPD"
        return ""

    def _extract_info_from_test_request(self, docx_file_path: str) -> Dict:
        try:
            logger.info(f"开始从测试申请文档中提取信息: {docx_file_path}")
            extractor = LTRApplicationDataExtractor()
            extracted_data = extractor.extract_application_data(docx_file_path)
            if "error" in extracted_data:
                logger.error(f"Failed to extract info from test request document: {extracted_data['error']}")
                return {}
            extracted_data.pop("file_path", None)
            logger.info(f"成功从测试申请文档中提取数据: {extracted_data}")
            return extracted_data
        except Exception as exc:
            logger.error(f"Failed to extract info from test request document: {exc}")
            return {}

    def _load_project_data(self, json_file_path: str) -> Dict:
        try:
            with open(json_file_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            logger.warning(f"读取项目JSON文件时出错: {exc}")
            return {}
