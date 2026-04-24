"""
报告更新模块服务层
处理报告更新的具体业务逻辑

注意：部分功能已拆分为子服务（equipment/ 目录）
- EquipmentExtractor: 设备ID提取
- EquipmentExcelReader: Excel数据读取
"""
import os
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import OrderedDict
from openpyxl import load_workbook
from docx import Document
from docx.shared import Inches
from docx.oxml.shared import OxmlElement, qn
import win32com.client as win32
import win32com.client.gencache as gencache
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.domain.project.output_paths import OutputPathResolver
from src.core.project_context import ProjectContext
from src.domain.project.project_document_context import ProjectDocumentContext
# 导入已提取的子服务
from src.features.report_updater.service.equipment import (
    EquipmentExtractor, 
    EquipmentExcelReader,
    DateFormatter,
    EquipmentTableFinder,
    EquipmentTableUpdater  # ⭐ 新增
)
# ✅ 导入专用异常，替代直接 UI 操作
from src.features.report_updater.service.exceptions import (
    EquipmentDataSourceNotFoundError,
    EquipmentDataReadError,
    EquipmentTableNotFoundError,
    NoEquipmentIdsFoundError,
)
from src.features.report_updater.service.report_word_equipment_update_service import (
    ReportWordEquipmentUpdateService,
)
from src.features.report_updater.service.report_updater_source_validator import (
    ReportUpdaterSourceValidator,
)
from src.infrastructure.office.facade import OfficeFacade
from src.features.report_updater.model.equipment_config import EquipmentConfigManager


class ReportUpdaterService:
    """报告更新服务类"""
    
    def __init__(
        self,
        project_context: Optional[ProjectContext] = None,
        word_equipment_update_service: Optional[ReportWordEquipmentUpdateService] = None,
        source_validator: Optional[ReportUpdaterSourceValidator] = None,
        office_facade: Optional[OfficeFacade] = None,
    ):
        """初始化报告更新服务"""
        self.project_context = project_context
        self._office_facade = office_facade or OfficeFacade()
        self.config_manager = EquipmentConfigManager(self.project_context)
        self.config = self.config_manager.get_config()
        self.source_validator = source_validator or ReportUpdaterSourceValidator()
        # 初始化子服务
        self.equipment_extractor = EquipmentExtractor()
        self.equipment_excel_reader = EquipmentExcelReader()
        self.date_formatter = DateFormatter()
        self.table_finder = EquipmentTableFinder()
        self.table_updater = EquipmentTableUpdater()  # ⭐ 新增
        self.word_equipment_update_service = (
            word_equipment_update_service
            or ReportWordEquipmentUpdateService(
                equipment_extractor=self.equipment_extractor,
                equipment_excel_reader=self.equipment_excel_reader,
                date_formatter=self.date_formatter,
                table_finder=self.table_finder,
                table_updater=self.table_updater,
                office_facade=self._office_facade,
            )
        )
        logger.info("ReportUpdaterService initialized")

    def set_project_context(self, project_context: Optional[ProjectContext]) -> None:
        self.project_context = project_context
        self.config_manager.set_project_context(project_context)
        self.config = self.config_manager.get_config()

    def _get_project_base_directory(self) -> Optional[str]:
        document_context = ProjectDocumentContext.from_project_context(self.project_context)
        return document_context.get_project_workspace_dir(create=False)
    
    def update_equipment_list(self, report_path: str, equipment_data: List[Dict[str, Any]] = None) -> bool:
        """
        更新报告中的设备列表

        Args:
            report_path: 报告文件路径
            equipment_data: 设备数据列表（可选，如果不提供则从Excel源获取）

        Returns:
            更新是否成功
        """
        try:
            logger.info(f"Starting equipment list update for report: {report_path}")
            
            # 根据文件类型选择相应的处理方式
            file_extension = os.path.splitext(report_path)[1].lower()
            
            if file_extension in ['.docx', '.doc']:
                return self._update_equipment_list_in_word_with_excel_source(report_path, equipment_data)
            elif file_extension in ['.xlsx', '.xls']:
                logger.warning(f"Excel report equipment update is not yet implemented: {report_path}")
                return False
            elif file_extension == '.pdf':
                logger.warning(f"Cannot update PDF file directly: {report_path}")
                return False
            else:
                logger.error(f"Unsupported file type for equipment update: {file_extension}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating equipment list in report {report_path}: {e}")
            return False

    def _validate_source_files(self, excel_file_path: str, source_doc_path: str) -> bool:
        """
        验证源文件是否存在
        
        Args:
            excel_file_path: Excel文件路径
            source_doc_path: 源文档路径
            
        Returns:
            验证是否通过
            
        Raises:
            EquipmentDataSourceNotFoundError: 当文件不存在时抛出，由 Controller 层处理 UI 展示
        """
        return self.source_validator.validate(
            excel_file_path=excel_file_path,
            source_doc_path=source_doc_path,
            project_path=self.config_manager.get_project_path(),
            config_path_provider=self._get_actual_config_path,
        )
    
    def _update_equipment_list_in_word_with_excel_source(self, report_path: str, equipment_data: List[Dict[str, Any]] = None) -> bool:
        """
        从Excel源获取数据并更新Word文档中的设备列表
        """
        try:
            logger.info(f"Updating equipment list in Word document with Excel source: {report_path}")

            # 从配置中获取Excel文件路径
            excel_file_path = self.config["equipment_data_sources"]["excel_file_path"]
            
            # 根据项目状态动态确定源文档路径
            source_doc_path = self.config_manager.resolve_source_doc_path()
            # section_keyword 不再使用，直接使用 "EQUIPMENTS" 进行匹配

            # 确保路径使用正确的反斜杠格式
            excel_file_path = os.path.normpath(excel_file_path)
            source_doc_path = os.path.normpath(source_doc_path)
            
            logger.debug(f"Using Excel file: {excel_file_path}")
            logger.debug(f"Using source document: {source_doc_path}")
            logger.debug("Looking for section keyword: EQUIPMENTS")

            # 验证源文件是否存在（委托给 _validate_source_files）
            if not self._validate_source_files(excel_file_path, source_doc_path):
                return False
            col_map = self.config["equipment_table_settings"]["target_columns_mapping"]
            return self.word_equipment_update_service.update_from_excel_source(
                report_path=report_path,
                excel_file_path=excel_file_path,
                source_doc_path=source_doc_path,
                column_mapping=col_map,
                section_keyword="EQUIPMENTS",
            )

        except Exception as e:
            logger.error(f"Error updating equipment list in Word document {report_path}: {e}")
            logger.error(
                "Word equipment update failed",
                exc_info=True,
            )
            return False
    

    
    def _get_actual_config_path(self) -> str:
        """获取实际使用的配置文件路径"""
        try:
            return config_manager.get_paths_config_path()
        except Exception as e:
            return f"无法确定配置路径: {e}"
    
