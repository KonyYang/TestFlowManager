"""
LTR申请单对话框模块
提供一个对话框用于显示和编辑LTR申请单信息
"""

import logging
import re
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QWidget, QScrollArea, QLabel, QComboBox, QTextEdit)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtWidgets import QDesktopWidget

from src.features.ltr_manager.model.ltr_application_data import LTRApplicationData
from src.features.ltr_manager.service.ltr_application_service import LTRApplicationService
from src.features.ltr_manager.utils.field_config_loader import LTRFieldConfigLoader
from src.features.ltr_manager.widgets import EnglishDateEdit, convert_to_english_format, MONTH_ABBREVIATIONS
from src.features.ltr_manager.view import LTRFormDialogBase
from src.core.event_dispatcher import event_dispatcher
from src.core.window_utils import WindowUtils

# Configure logging for this module
logger = logging.getLogger(__name__)


class LTRApplicationDialog(LTRFormDialogBase):
    """LTRApplicationDialog
    LTR申请单对话框类
    用于显示和编辑LTR申请单信息
    """

    def __init__(self, application_data, parent=None, parent_controller=None, temp_folder_path: Optional[str] = None, extracted_word_data: Optional[Dict[str, Any]] = None):
        """
        初始化LTR申请单对话框

        Args:
            application_data: 包含申请单数据的字典
            parent: 父窗口
            extracted_word_data: 从Word文档提取的完整数据（可选）
        """
        self.parent_controller = parent_controller
        self.application_data = application_data
        # 保存临时文件夹路径
        self.temp_folder_path = temp_folder_path
        # 保存从Word文档提取的完整数据
        self.extracted_word_data = extracted_word_data

        self.dl_number = application_data.get('dl_number', '')
        self.original_data = application_data.get('data', {})
        self.modified_data = self.original_data.copy()

        # 初始化数据模型
        self.data_model = LTRApplicationData.from_dict(self.original_data)

        # 初始化服务层和控制器
        self.service = LTRApplicationService()
        self.controller = parent_controller
        
        # 初始化版本标签
        self.version_label = None

        # 调用基类构造函数
        super().__init__(f"LTR申请单: {self.dl_number}" if self.dl_number else "新LTR申请单", self.data_model.to_dict(), parent)
        
        # 添加版本标签
        self._add_version_label()

    def _add_version_label(self):
        """添加版本标签"""
        # 设置版本信息
        version = self.data_model.to_dict().get("version", "N/A")
        self.version_label = QLabel(f"Application Version: {version}")
        
        # 将版本标签添加到布局的顶部
        layout = self.layout()
        if isinstance(layout, QVBoxLayout):
            layout.insertWidget(0, self.version_label)

    def _populate_data(self):
        """填充数据到表格"""
        # 获取数据
        data = self.data_model.to_dict()

        # 设置版本信息
        if self.version_label:
            version = data.get("version", "N/A")
            self.version_label.setText(f"Application Version: {version}")

        # 处理特殊字段格式
        for key in ['sample_information', 'tests_to_be_performed', 'applicable_specifications']:
            if key in data:
                # 查找对应的字段配置
                item = None
                for field in self._default_items_structure:
                    if field['key'] == key:
                        item = field
                        break
                        
                if item and item.get('editor_type') == 'multiline':
                    # 仅在需要显示到multiline编辑器时才换行，不影响原始数据
                    data[key] = data[key].replace(';', '\n')

        # 如果project_leader为空，使用配置中的默认值
        from src.core.config_manager import config_manager
        if not data.get('project_leader'):
            data['project_leader'] = config_manager.get_default("project_leader", "")

        # 调用基类方法填充数据，但先更新self.data
        self.data = data
        super()._populate_data()

    def accept(self):
        """重写accept方法，添加数据验证和处理"""
        logger.debug("LTRApplicationDialog.accept() called")
        # 收集表单数据
        form_data = self._collect_form_data()
        logger.debug(f"Collected form data: {form_data}")

        # 如果有控制器，调用控制器处理LTR申请
        if self.controller and hasattr(self.controller, 'apply_ltr_number'):
            logger.debug("Controller found, calling apply_ltr_number")
            try:
                # 传递临时文件夹路径和提取的Word文档数据给控制器
                result = self.controller.apply_ltr_number(form_data, self, self.temp_folder_path, self.extracted_word_data)
                logger.debug(f"apply_ltr_number result: {result}")

                # 根据结果决定是否关闭对话框
                if result.get("success"):
                    logger.debug("LTR application successful, scheduling dialog close")
                    # 使用QTimer延迟关闭对话框，确保所有事件处理完成
                    QTimer.singleShot(100, self._delayed_accept)
                elif result.get('retry', False):
                    # 需要重新输入，保持对话框打开
                    logger.debug("LTR application needs retry, keeping dialog open")
                    return
                else:
                    # 其他情况关闭对话框
                    logger.debug("LTR application failed, rejecting dialog")
                    self.reject()

            except Exception as e:
                import traceback
                from PyQt5.QtWidgets import QMessageBox
                logger.error(f"Exception in apply_ltr_number: {e}", exc_info=True)
                QMessageBox.critical(self, "错误", f"处理申请时发生异常: {str(e)}")
                self.reject()
        else:
            logger.debug("No controller found, closing dialog directly")
            super().accept()
            
    def _delayed_accept(self):
        """延迟接受对话框，确保所有操作完成"""
        logger.debug("_delayed_accept called")
        try:
            # 确保所有COM对象被释放
            try:
                from src.utils import word_utils, excel_utils
                word_utils.release_word_app()
                excel_utils.release_excel_app()
            except:
                pass
                
            # 调用父类的accept方法
            logger.debug("Calling super().accept()")
            super().accept()
        except Exception as e:
            logger.error(f"Error in _delayed_accept: {e}", exc_info=True)
            try:
                super().accept()
            except:
                self.reject()
