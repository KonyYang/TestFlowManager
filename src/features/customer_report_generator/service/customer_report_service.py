"""
客户报告生成服务模块
提供客户报告生成相关的业务逻辑服务
"""

import os
from datetime import datetime
from pathlib import Path
from src.core.logger import logger
from src.utils.word_utils import get_shared_word_app
from .utils import HeaderProcessor, ContentCopier, FormatProcessor, DocumentUtils


class CustomerReportService:
    """
    客户报告生成服务类
    提供客户报告生成相关的业务逻辑服务
    """

    def __init__(self):
        """初始化客户报告生成服务"""
        self.word_app = None
        self.source_doc = None
        self.template_doc = None
        self.temp_template_path = None

    def _initialize_word_app(self):
        """初始化Word应用程序"""
        try:
            self.word_app = get_shared_word_app()
            if self.word_app is None:
                raise Exception("无法获取Word应用程序实例")
            self.word_app.Visible = False
            logger.debug("Word应用程序初始化成功")
        except Exception as e:
            logger.error(f"初始化Word应用程序失败: {e}")
            raise

    def _find_template_file(self):
        """
        查找客户报告模板文件
        
        Returns:
            str: 模板文件路径，如果未找到则返回空字符串
        """
        return DocumentUtils.find_template_file()

    def _select_source_document(self, parent_window=None, project_path=None):
        """
        选择源文档
        
        Args:
            parent_window: 父窗口
            project_path: 项目路径
            
        Returns:
            str: 源文档路径，如果用户取消则返回空字符串
        """
        return DocumentUtils.select_source_document(parent_window, project_path)

    def _prepare_documents(self, source_path, template_path):
        """
        准备源文档和模板文档
        
        Args:
            source_path (str): 源文档路径
            template_path (str): 模板文档路径
        """
        try:
            self.source_doc, self.template_doc, self.temp_template_path = DocumentUtils.prepare_documents(
                source_path, template_path, self.word_app
            )
        except Exception as e:
            logger.error(f"准备文档时出错: {e}")
            raise

    def _validate_source_document_type(self, expected_type="LABORATORY TEST REPORT"):
        """
        验证源文档类型是否为期望的报告类型
        
        Args:
            expected_type (str): 期望的文档类型，默认为"LABORATORY TEST REPORT"
        
        Returns:
            bool: 如果是期望的文档类型返回True，否则返回False
        """
        return DocumentUtils.validate_source_document_type(self.source_doc, expected_type)

    def _modify_header(self):
        """
        修改页眉信息
        
        Returns:
            bool: 是否成功修改页眉
        """
        return HeaderProcessor.modify_header(self.source_doc, self.template_doc)

    def _copy_purpose_to_equipments_content(self):
        """
        复制从"1. PURPOSE"到"7. EQUIPMENTS"的内容
        """
        return ContentCopier.copy_purpose_to_equipments_content(self.source_doc, self.template_doc)

    def _remove_number_and_dot_in_formatted_paragraphs(self):
        """
        清理章节标题格式（去除数字和点）
        """
        return FormatProcessor.remove_number_and_dot_in_formatted_paragraphs(self.template_doc)

    def _copy_revision_record(self):
        """
        复制修订记录（8. REVISION RECORD）
        """
        return ContentCopier.copy_revision_record(self.source_doc, self.template_doc)

    def _move_and_format_text(self):
        """
        移动并格式化特定文本
        """
        return FormatProcessor.move_and_format_text(self.template_doc)

    def _generate_new_filename(self, source_path):
        """
        生成新文件名
        
        Args:
            source_path (str): 源文件路径
            
        Returns:
            str: 新文件名
        """
        return DocumentUtils.generate_new_filename(source_path)

    def _save_customer_report(self, source_path, new_filename):
        """
        保存客户报告
        
        Args:
            source_path (str): 源文件路径
            new_filename (str): 新文件名
            
        Returns:
            str: 保存的文件路径，如果用户取消保存则返回空字符串
        """
        return DocumentUtils.save_customer_report(source_path, new_filename, self.template_doc)

    def _cleanup(self):
        """清理资源"""
        DocumentUtils.cleanup_resources(self.template_doc, self.source_doc, self.temp_template_path)
        self.template_doc = None
        self.source_doc = None
        self.temp_template_path = None

    def generate_customer_report(self, parent_window=None, project_path=None):
        """
        生成客户报告主函数
        
        Args:
            parent_window: 父窗口
            project_path: 项目路径
            
        Returns:
            tuple: (是否成功, 保存路径或错误信息)
        """
        try:
            logger.info("开始生成客户报告")
            
            # 初始化Word应用程序
            self._initialize_word_app()
            
            # 查找模板文件
            template_path = self._find_template_file()
            if not template_path:
                return False, "未找到客户报告模板文件"
            
            # 选择源文档
            source_path = self._select_source_document(parent_window, project_path)
            if not source_path:
                return False, "用户取消了操作"
            
            # 准备文档
            self._prepare_documents(source_path, template_path)
            
            # 检查文档是否成功打开
            if not self.source_doc or not self.template_doc:
                return False, "未能成功打开源文档或模板文档"
            
            # 验证源文档类型是否为实验室测试报告
            if not self._validate_source_document_type("LABORATORY TEST REPORT"):
                return False, "源文档不是有效的实验室测试报告"
            
            # 修改页眉信息
            if not self._modify_header():
                return False, "修改页眉信息失败"
            
            # 复制核心内容（包含修订记录）
            if not self._copy_purpose_to_equipments_content():
                return False, "复制核心内容失败"

            # 清理章节标题格式
            if not self._remove_number_and_dot_in_formatted_paragraphs():
                return False, "清理章节标题格式失败"

            # 移动并格式化特定文本
            if not self._move_and_format_text():
                return False, "移动并格式化特定文本失败"
            
            # 生成新文件名
            new_filename = self._generate_new_filename(source_path)
            if not new_filename:
                return False, "生成新文件名失败"
            
            # 保存客户报告
            save_path = self._save_customer_report(source_path, new_filename)
            
            logger.info(f"客户报告生成完成: {save_path}")
            return True, save_path
        except Exception as e:
            logger.error(f"生成客户报告时出错: {e}")
            error_msg = str(e)
            return False, error_msg
        finally:
            # 清理资源
            self._cleanup()