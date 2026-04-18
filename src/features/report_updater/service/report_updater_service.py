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


class EquipmentConfigManager:
    """设备更新配置管理器"""
    
    def __init__(self, project_context: Optional[ProjectContext] = None):
        self.project_context = project_context
        self.config = self._load_config()

    def set_project_context(self, project_context: Optional[ProjectContext]) -> None:
        self.project_context = project_context
        self.config = self._load_config()

    def get_project_path(self) -> Optional[str]:
        return self.project_context.project_path if self.project_context else None

    def resolve_source_doc_path(self) -> str:
        project_path = self.get_project_path()
        if project_path and os.path.exists(project_path):
            return os.path.join(project_path, "EquipmentID.docx")
        return self.config["equipment_data_sources"]["source_doc_fallback_path"]

    def resolve_default_output_dir(self) -> str:
        project_path = self.get_project_path()
        if project_path and os.path.exists(project_path):
            document_context = ProjectDocumentContext.from_project_context(self.project_context)
            return (
                document_context.get_project_workspace_dir(create=False)
                or project_path
            )
        return self.config["equipment_data_sources"]["default_output_fallback_dir"]
    
    def _load_config(self):
        """加载设备更新配置。source/output 路径只表示无项目态兜底。"""
        excel_file_path = config_manager.get_equipment_data_source("excel_file_path", 
            "D:\\Source\\FCI Dongguan product test laboratory equipment list for report- Huan Revised.xls")
        default_source_doc_fallback_path = config_manager.get_equipment_data_source(
            "source_doc_path",
            OutputPathResolver.build_default_output_path("EquipmentID.docx"),
        )
        default_output_fallback_dir = config_manager.get_equipment_data_source(
            "default_output_path",
            OutputPathResolver.get_default_output_dir(),
        )
        
        return {
            "equipment_data_sources": {
                "excel_file_path": excel_file_path,
                "source_doc_fallback_path": default_source_doc_fallback_path,
                "default_output_fallback_dir": default_output_fallback_dir,
            },
            "equipment_table_settings": {
                "section_keyword": "EQUIPMENTS",
                "target_columns_mapping": {
                    "item_col": 1,
                    "manufacturer_col": 2,
                    "id_number_col": 3,
                    "last_cal_col": 4,
                    "cal_due_col": 5
                }
            }
        }

    def get_config(self):
        """获取配置"""
        return self.config

    def update_config(self, new_config: dict):
        """更新配置"""
        # 由于现在使用全局配置管理器，不再保存到本地文件
        # 只更新内存中的配置
        self.config.update(new_config)


class ReportUpdaterService:
    """报告更新服务类"""
    
    def __init__(self, project_context: Optional[ProjectContext] = None):
        """初始化报告更新服务"""
        self.project_context = project_context
        self.config_manager = EquipmentConfigManager(self.project_context)
        self.config = self.config_manager.get_config()
        # 初始化子服务
        self.equipment_extractor = EquipmentExtractor()
        self.equipment_excel_reader = EquipmentExcelReader()
        self.date_formatter = DateFormatter()
        self.table_finder = EquipmentTableFinder()
        self.table_updater = EquipmentTableUpdater()  # ⭐ 新增
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

    def _extract_equipment_ids_from_doc(self, doc_path: str) -> List[str]:
        """
        从文档中提取设备ID（已委托给 EquipmentExtractor）
        
        ⚠️ DEPRECATED: 此方法保留用于兼容性，内部已委托给 EquipmentExtractor
        """
        return self.equipment_extractor.extract_equipment_ids(doc_path)

    def _find_equipment_table_win32com(self, word_doc, paragraph_keyword: str = "EQUIPMENTS"):
        """
        使用win32com在Word文档中根据段落关键字查找紧跟其后的表格（已委托给 EquipmentTableFinder）
        
        ⚠️ DEPRECATED: 此方法保留用于兼容性，内部已委托给 EquipmentTableFinder
        """
        return self.table_finder.find_table_after_keyword(word_doc, paragraph_keyword)

    def _format_date(self, date_value):
        """
        将日期格式转换为 DD-MMM-YYYY 格式（已委托给 DateFormatter）
        
        ⚠️ DEPRECATED: 此方法保留用于兼容性，内部已委托给 DateFormatter
        """
        return self.date_formatter.format_to_dd_mmm_yyyy(date_value)

    def _find_matching_row_in_excel(self, df, equipment_id):
        """
        在Excel数据中查找匹配的设备ID行（已委托给 EquipmentExcelReader）
        
        ⚠️ DEPRECATED: 此方法保留用于兼容性，内部已委托给 EquipmentExcelReader
        """
        return self.equipment_excel_reader.find_matching_row(df, equipment_id)

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
        # 检查Excel文件
        if not os.path.exists(excel_file_path):
            logger.error(f"Excel file does not exist: {excel_file_path}")
            
            # 构建上下文信息（供日志和 Controller 使用）
            context_info = {
                "配置来源": config_manager.describe_config_source(),
                "当前工作目录": os.getcwd(),
                "配置文件路径": self._get_actual_config_path(),
                "运行模式": '可执行文件模式' if getattr(sys, 'frozen', False) else '开发模式'
            }
            
            # ✅ 抛出专用异常，不再直接操作 UI
            raise EquipmentDataSourceNotFoundError(
                file_path=excel_file_path,
                file_type="excel",
                context_info=context_info
            )
        
        # 检查源文档
        if not os.path.exists(source_doc_path):
            logger.error(f"Source document does not exist: {source_doc_path}")
            project_dir = os.path.dirname(source_doc_path)
            project_path = self.config_manager.get_project_path()
            
            # 确定错误类型描述
            if project_path and project_dir == project_path:
                error_message = "项目文件夹下没有找到EquipmentID.docx"
            else:
                error_message = "默认路径下没有找到EquipmentID.docx"
            
            # 构建上下文信息
            context_info = {
                "错误类型": error_message,
                "配置来源": config_manager.describe_config_source(),
                "查找路径": source_doc_path,
                "项目路径": project_path or '无',
                "当前工作目录": os.getcwd(),
                "配置文件实际路径": self._get_actual_config_path(),
                "运行模式": '可执行文件模式' if getattr(sys, 'frozen', False) else '开发模式'
            }
            
            # ✅ 抛出专用异常，不再直接操作 UI
            raise EquipmentDataSourceNotFoundError(
                file_path=source_doc_path,
                file_type="word",
                context_info=context_info
            )
        
        return True
    
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

            # 使用 win32com 打开 Word 文档
            logger.debug("Initializing Word application via COM...")
            # 注意：使用 Dispatch 而不是 gencache.EnsureDispatch 以避免缓存文件损坏问题
            # 如果遇到问题，可以手动清理 win32com 缓存目录：%TEMP%\\gen_py\\
            word_app = win32.Dispatch('Word.Application')
            word_app.Visible = False  # 不显示Word界面
            word_app.DisplayAlerts = False  # 关闭警告提示

            # 确保路径使用正确的反斜杠格式
            normalized_report_path = os.path.normpath(report_path)
            
            # 打开文档
            logger.debug(f"Opening document: {normalized_report_path}")
            word_doc = word_app.Documents.Open(normalized_report_path)

            # 使用win32com查找指定的关键字标题和表格
            logger.info(f"Finding 'EQUIPMENTS' section and table using win32com...")
            logger.debug(f"About to call _find_equipment_table_win32com with keyword 'EQUIPMENTS'")
            target_table = self._find_equipment_table_win32com(word_doc, "EQUIPMENTS")

            if target_table is None:
                logger.warning(f"Could not find 'EQUIPMENTS' section or table!")
                logger.debug(f"Could not find table with keyword 'EQUIPMENTS'")
                word_doc.Close()
                word_app.Quit()
                # ✅ 抛出专用异常
                raise EquipmentTableNotFoundError(report_path, "EQUIPMENTS")
            else:
                logger.info("Successfully found equipment table using win32com")
                logger.debug(f"Successfully found equipment table with {target_table.Rows.Count} rows")
                logger.info(f"Table has {target_table.Rows.Count} rows initially")

            # 从Excel中读取设备列表（委托给 EquipmentExcelReader）
            logger.info(f"Reading Excel file: {excel_file_path}")
            try:
                excel_df = self.equipment_excel_reader.read_equipment_data(excel_file_path)
            except Exception as e:
                logger.error(f"Failed to read Excel file: {excel_file_path}")
                word_doc.Close()
                word_app.Quit()
                # ✅ 抛出专用异常
                raise EquipmentDataReadError(excel_file_path, e)
            
            if excel_df is None:
                logger.error(f"Failed to read Excel file: {excel_file_path}")
                word_doc.Close()
                word_app.Quit()
                raise EquipmentDataReadError(excel_file_path)
            
            logger.info(f"Loaded Excel data with {len(excel_df)} rows and {len(excel_df[0]) if len(excel_df) > 0 else 0} columns")

            # 从源文档中提取设备ID
            logger.info("Extracting equipment IDs from source document...")
            logger.debug(f"Extracting equipment IDs from source document: {source_doc_path}")
            equipment_ids = self._extract_equipment_ids_from_doc(source_doc_path)
            logger.info(f"Found {len(equipment_ids)} unique equipment IDs")
            logger.debug(f"Found {len(equipment_ids)} unique equipment IDs: {equipment_ids}")
            if equipment_ids:
                logger.debug(f"Equipment IDs: {equipment_ids[:5]}...")  # 只显示前5个

            if not equipment_ids:
                logger.warning("No equipment IDs found in source document!")
                word_doc.Close()
                word_app.Quit()
                # ✅ 抛出专用异常
                raise NoEquipmentIdsFoundError(source_doc_path)

            # 将设备ID填入表格（委托给 EquipmentTableUpdater）
            self.table_updater.fill_equipment_ids(target_table, equipment_ids, row_start=2)

            # 从Excel获取数据并填充表格其他列（委托给 EquipmentTableUpdater）
            col_map = self.config["equipment_table_settings"]["target_columns_mapping"]
            self.table_updater.fill_excel_data_to_table(
                target_table, excel_df, col_map, self.date_formatter, row_start=2
            )

            # 为新增的行添加边框（委托给 EquipmentTableUpdater）
            self.table_updater.add_borders_to_rows(target_table, row_start=2)

            # 保存文档
            logger.info("Saving updated document...")
            word_doc.Save()
            logger.info("Document saved successfully")
            
            word_doc.Close()
            word_app.Quit()
            logger.info(f"Successfully updated equipment list in {report_path}")
            return True

        except Exception as e:
            logger.error(f"Error updating equipment list in Word document {report_path}: {e}")
            import traceback
            traceback.print_exc()
            try:
                # 确保文档和应用程序被正确关闭
                if 'word_doc' in locals():
                    word_doc.Close()
                if 'word_app' in locals():
                    word_app.Quit()
            except:
                pass
            return False
    

    
    def _get_actual_config_path(self) -> str:
        """获取实际使用的配置文件路径"""
        try:
            return config_manager.get_paths_config_path()
        except Exception as e:
            return f"无法确定配置路径: {e}"
    
