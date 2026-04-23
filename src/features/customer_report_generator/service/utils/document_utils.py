"""
文档工具模块
提供文档处理的通用工具函数
"""

import os
import shutil
from PyQt5.QtWidgets import QFileDialog
from src.core.logger import logger
from src.core.config_manager import config_manager
from src.utils.word_utils import close_document


class DocumentUtils:
    """
    文档工具类
    提供文档处理的通用工具函数
    """
    
    @staticmethod
    def find_template_file():
        """
        查找客户报告模板文件
        
        Returns:
            str: 模板文件路径，如果未找到则返回空字符串
        """
        try:
            # 从配置中获取模板目录
            template_dir = config_manager.get_template_dir()
            if not template_dir or not os.path.exists(template_dir):
                logger.warning(f"模板目录不存在: {template_dir}")
                return ""
            
            # 查找以"E-4515"开头的Word文档
            for filename in os.listdir(template_dir):
                if filename.startswith("E-4515") and filename.endswith((".docx", ".doc")):
                    template_path = os.path.join(template_dir, filename)
                    # 规范化路径
                    template_path = os.path.normpath(template_path)
                    logger.debug(f"找到客户报告模板文件: {template_path}")
                    return template_path
            
            logger.warning("未找到以'E-4515'开头的客户报告模板文件")
            return ""
        except Exception as e:
            logger.error(f"查找模板文件时出错: {e}")
            return ""

    @staticmethod
    def select_source_document(parent_window=None, project_path=None):
        """
        选择源文档
        
        Args:
            parent_window: 父窗口
            project_path: 项目路径
            
        Returns:
            str: 源文档路径，如果用户取消则返回空字符串
        """
        try:
            # 设置默认目录
            default_dir = project_path if project_path and os.path.exists(project_path) else ""
            
            # 弹出文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                parent_window,
                "选择源文档",
                default_dir,
                "Word文档 (*.docx *.doc)"
            )
            
            if not file_path:
                logger.info("用户取消了文件选择")
                return ""
            
            # 规范化路径
            file_path = os.path.normpath(file_path)
            logger.debug(f"选择的源文档: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"选择源文档时出错: {e}")
            return ""

    @staticmethod
    def prepare_documents(source_path, template_path, word_app):
        """
        准备源文档和模板文档
        
        Args:
            source_path (str): 源文档路径
            template_path (str): 模板文档路径
            word_app: Word应用程序实例
            
        Returns:
            tuple: (source_doc, template_doc, temp_template_path)
        """
        try:
            # 规范化路径
            source_path = os.path.normpath(source_path)
            template_path = os.path.normpath(template_path)
            
            # 检查源文件是否存在
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"源文档不存在: {source_path}")
            
            # 检查模板文件是否存在
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"模板文档不存在: {template_path}")
            
            # 使用同一个 Word session 打开源文档（只读模式）
            source_doc = word_app.Documents.Open(
                source_path,
                ReadOnly=True,
                PasswordDocument="",
            )
            if source_doc is None:
                raise Exception(f"无法打开源文档: {source_path}")
            logger.debug(f"成功打开源文档: {source_path}")
            
            # 创建临时模板文件路径
            source_dir = os.path.dirname(source_path)
            temp_template_path = os.path.join(source_dir, "Temp_CustomerReport.docx")
            temp_template_path = os.path.normpath(temp_template_path)
            
            # 复制模板文件到临时路径
            shutil.copy2(template_path, temp_template_path)
            logger.debug(f"模板文件已复制到临时路径: {temp_template_path}")
            
            # 打开临时模板文件
            template_doc = word_app.Documents.Open(temp_template_path)
            logger.debug("临时模板文件已打开")
            
            return source_doc, template_doc, temp_template_path
        except Exception as e:
            logger.error(f"准备文档时出错: {e}")
            raise

    @staticmethod
    def validate_source_document_type(source_doc, expected_type="LABORATORY TEST REPORT"):
        """
        验证源文档类型是否为期望的报告类型
        
        Args:
            source_doc: 源文档对象
            expected_type (str): 期望的文档类型，默认为"LABORATORY TEST REPORT"
        
        Returns:
            bool: 如果是期望的文档类型返回True，否则返回False
        """
        try:
            # 检查文档是否成功打开
            if not source_doc:
                logger.error("源文档未打开，无法验证类型")
                return False

            # 获取源文档第一节首页页眉
            first_section = source_doc.Sections(1)
            header_range = first_section.Headers(2).Range  # wdHeaderFooterFirstPage = 2

            # 检查首页页眉中是否有表格
            if header_range.Tables.Count == 0:
                logger.info("❌ 源文档首节首页页眉中未找到表格")
                return False

            # 获取第一个表格
            header_table = header_range.Tables(1)
            if header_table.Rows.Count < 1 or header_table.Columns.Count < 2:
                logger.info("❌ 表格行列不足，无法检查标志")
                return False

            # 检查表格第1行第2列的内容
            cell_text = header_table.Cell(1, 2).Range.Text.strip()

            # 判断是否包含期望的文档类型
            if expected_type in cell_text:
                logger.info(f"✅ 检测到有效的{expected_type}")
                return True
            else:
                logger.info(f"⚠️ 文档类型不匹配，期望: {expected_type}, 实际内容: {cell_text[:50]}...")
                return False

        except Exception as e:
            logger.error(f"验证源文档类型时出错: {e}")
            return False

    @staticmethod
    def generate_new_filename(source_path):
        """
        生成新文件名
        
        Args:
            source_path (str): 源文件路径
            
        Returns:
            str: 新文件名
        """
        try:
            source_filename = os.path.basename(source_path)
            
            # 提取第一个连续非空格字符串
            parts = source_filename.split(" ")
            extracted_string = ""
            for part in parts:
                if part.strip():
                    extracted_string = part.strip()
                    break
            
            if not extracted_string:
                logger.error("提取的字符串为空，无法生成新文件名")
                return ""
            
            # 检查是否包含版本号（Rev.X格式）
            import re
            rev_match = re.search(r" Rev\.([A-Z]+)$", extracted_string)
            
            if rev_match:
                # 提取基础报告编号和版本号
                base_string = extracted_string[:rev_match.start()]
                version = rev_match.group(0)  # 包含空格的完整版本号，如" Rev.B"
                # 组合为新的文件名格式
                new_extracted_string = base_string + "-CR" + version
                new_filename = source_filename.replace(extracted_string, new_extracted_string)
            else:
                # 没有版本号的普通情况
                new_filename = source_filename.replace(extracted_string, extracted_string + "-CR")
            
            new_filename = new_filename.replace("Report", "Report_Customer")
            
            logger.debug(f"生成的新文件名: {new_filename}")
            return new_filename
        except Exception as e:
            logger.error(f"生成新文件名时出错: {e}")
            return ""

    @staticmethod
    def save_customer_report(source_path, new_filename, template_doc):
        """
        保存客户报告
        
        Args:
            source_path (str): 源文件路径
            new_filename (str): 新文件名
            template_doc: 模板文档对象
            
        Returns:
            str: 保存的文件路径，如果用户取消保存则返回空字符串
        """
        try:
            # 构造默认保存路径
            source_dir = os.path.dirname(source_path)
            default_save_path = os.path.join(source_dir, new_filename)
            # 规范化路径
            default_save_path = os.path.normpath(default_save_path)
            
            # 弹出保存对话框让用户确认保存路径
            save_path, _ = QFileDialog.getSaveFileName(
                None,
                "保存客户报告",
                default_save_path,
                "Word文档 (*.docx *.doc)"
            )
            
            # 如果用户取消了保存操作
            if not save_path:
                logger.info("用户取消了保存操作")
                return ""  # 返回空字符串表示用户取消操作
            
            # 规范化用户选择的路径
            save_path = os.path.normpath(save_path)
            
            # 保存文档
            template_doc.SaveAs2(save_path)
            logger.debug(f"客户报告已保存为: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"保存客户报告时出错: {e}")
            raise

    @staticmethod
    def cleanup_resources(template_doc=None, source_doc=None, temp_template_path=None):
        """
        清理资源
        
        Args:
            template_doc: 模板文档对象
            source_doc: 源文档对象
            temp_template_path: 临时模板文件路径
        """
        try:
            # 关闭文档
            if template_doc:
                try:
                    close_document(template_doc, save_changes=False)
                except:
                    pass  # 文档可能已经关闭
            
            if source_doc:
                try:
                    close_document(source_doc, save_changes=False)
                except:
                    pass  # 文档可能已经关闭
            
            # 删除临时文件
            if temp_template_path and os.path.exists(temp_template_path):
                try:
                    os.remove(temp_template_path)
                    logger.debug(f"临时文件已删除: {temp_template_path}")
                except Exception as e:
                    logger.warning(f"删除临时文件时出错: {e}")
            
            logger.debug("资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")
