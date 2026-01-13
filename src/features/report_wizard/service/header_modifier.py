"""
页眉修改服务模块
提供Word文档页眉修改相关的业务逻辑服务
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from docx import Document
from datetime import datetime
import pythoncom
from src.core.logger import logger
from src.utils.word_utils import get_shared_word_app

# 导入拆分的工具模块
from .utils.date_handler import DateHandler
from .utils.header_manager import HeaderManager
from .utils.table_handler import TableHandler
from .utils.cell_modifier import CellModifier


class HeaderModifier:
    """
    页眉修改服务类
    提供Word文档页眉修改相关的业务逻辑服务
    """

    def __init__(self, file_path: str):
        """初始化页眉修改服务"""
        self.file_path = file_path
        self.doc = None
        self.win_document = None
        self.word_app = None

    def modify_header(self, header_data: Dict[str, Any]) -> bool:
        """
        使用 win32com.client 精准填写 Word 首页页眉内容

        :param header_data: 页眉数据字典，包含 report_no, version, date, tester 等字段
        :return: 是否成功
        """
        return HeaderManager.modify_first_header(self.file_path, header_data, self.word_app)

    def modify_revision_record_date(self, header_data: Dict[str, Any], is_customer_report: bool = False, doc=None) -> bool:
        """
        修改正文 'REVISION RECORD' 表格中的日期
        
        :param header_data: 页眉数据字典，包含 completion_date 等字段
        :param is_customer_report: 是否是客户报告，默认为 False
        :param doc: python-docx Document 对象，如果为None则使用self.doc
        :return: 是否成功
        """
        # 使用传入的doc参数，如果为None则使用self.doc
        doc_to_use = doc if doc is not None else self.doc
        if doc_to_use is None:
            logger.error("❌ 文档对象未提供且self.doc为None")
            return False

        return TableHandler.modify_revision_record_date(doc_to_use, header_data, is_customer_report)

    def modify_sample_received_date(self, header_data: Dict[str, Any], doc=None) -> bool:
        """
        修改正文中的样品接收日期
        查找 "Samples were received at the laboratory on [DATE]. Prior to testing..." 并替换其中的日期部分
        
        :param header_data: 页眉数据字典，包含 date_lab_received_samples 字段
        :param doc: python-docx Document 对象，如果为None则使用self.doc
        :return: 是否成功
        """
        try:
            # 从header_data中获取样品接收日期
            sample_received_date_str = header_data.get("date_lab_received_samples", "")
            logger.debug(f"modify_sample_received_date: 从header_data获取的date_lab_received_samples = '{sample_received_date_str}'")
            if not sample_received_date_str:
                logger.warning("header_data 中未找到 date_lab_received_samples 字段！")
                return False

            # 将日期格式化为 "MMM dd, yyyy" 格式 (例如 "Dec 20, 2024")
            formatted_date = DateHandler.format_date_to_month_day_year(sample_received_date_str)
            logger.debug(f"modify_sample_received_date: 格式化后的日期 = '{formatted_date}'")

            # 使用传入的doc参数，如果为None则使用self.doc
            doc_to_use = doc if doc is not None else self.doc
            if doc_to_use is None:
                logger.error("❌ 文档对象未提供且self.doc为None")
                return False

            # 查找包含样品接收日期的段落
            sample_received_pattern_start = "Samples were received at the laboratory on"
            sample_received_pattern_end = "Prior to testing, the samples were examined at low magnification and judged to be acceptable for testing."
            
            # 完整的目标句子，包含要保留的最后部分
            full_pattern = r'(Samples were received at the laboratory on )(.+?)(\.\s*Prior to testing,\s*the samples were examined at low magnification and judged to be acceptable for testing\.\s*(?:The results of testing only apply to the samples as received in the laboratory\.)?)'

            found = False
            for para in doc_to_use.paragraphs:
                if sample_received_pattern_start in para.text:
                    original_text = para.text
                    logger.info(f"找到样品接收日期段落: '{original_text}'")

                    # 使用正则表达式查找并替换日期部分，保留完整的后续文本
                    import re
                    # 匹配 "Samples were received at the laboratory on [任意日期]. Prior to testing..." 模式，以及可能的后续句子
                    match = re.search(full_pattern, para.text)

                    if match:
                        # 保留前后部分，替换中间的日期部分
                        before_date = match.group(1)  # "Samples were received at the laboratory on "
                        current_date = match.group(2)  # 当前日期
                        after_date = match.group(3)    # ". Prior to testing..." 包括后续句子
                        
                        # 创建新的段落文本，保留原有的后续句子
                        new_text = before_date + formatted_date + after_date
                        para.text = new_text
                        
                        logger.info(f"样品接收日期已更新: '{current_date}' -> '{formatted_date}'")
                        logger.info(f"完整段落更新为: '{new_text}'")
                        found = True
                    else:
                        logger.warning(f"未能在段落中找到预期的日期模式: '{para.text}'")
                        # 如果正则表达式未匹配，尝试更简单的替换方法
                        # 找到开始和结束位置，直接替换中间部分
                        start_pos = para.text.find(sample_received_pattern_start)
                        
                        if start_pos != -1:
                            # 找到日期开始位置后的部分
                            after_start = para.text[start_pos + len(sample_received_pattern_start):]
                            # 查找第一个句号，表示日期结束
                            dot_pos = after_start.find('.')
                            if dot_pos != -1:
                                current_date = after_start[:dot_pos].strip()
                                # 获取剩余部分，包含后续句子
                                remaining_text = after_start[dot_pos+1:]
                                
                                # 重新构造完整句子，保留后续部分
                                para.text = sample_received_pattern_start + " " + formatted_date + "." + remaining_text
                                logger.info(f"使用简单替换方法更新样品接收日期: '{current_date}' -> '{formatted_date}'")
                                found = True

            if not found:
                logger.warning("未找到包含样品接收日期的段落")
                # 尝试查找包含关键词的段落，即使格式略有不同
                for para in doc_to_use.paragraphs:
                    if "Samples were received at the laboratory" in para.text:
                        logger.info(f"找到包含样品接收信息的段落: '{para.text}'")
                        original_text = para.text
                        
                        # 尝试使用更全面的正则表达式匹配各种可能的格式，确保保留所有后续文本
                        import re
                        # 匹配 "Samples were received at the laboratory on [任意日期]." 及其后的完整句子
                        patterns = [
                            r'(Samples were received at the laboratory on )(.+?)(\.\s*Prior to testing,\s*the samples were examined at low magnification and judged to be acceptable for testing\.\s*(?:The results of testing only apply to the samples as received in the laboratory\.)?)',
                            r'(Samples were received at the laboratory on )(.+?)(\.\s*Prior to)',
                            r'(Samples were received at the laboratory on )(.+?)(\.\s*Prior)',
                            r'(Samples were received at the laboratory on )(.+?)(\.)'
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, para.text, re.IGNORECASE)
                            if match:
                                before_date = match.group(1)
                                current_date = match.group(2)
                                after_date = match.group(3)
                                
                                new_text = before_date + formatted_date + after_date
                                para.text = new_text
                                
                                logger.info(f"使用备用模式更新样品接收日期: '{current_date}' -> '{formatted_date}'")
                                logger.info(f"完整段落更新为: '{new_text}'")
                                found = True
                                break
                        
                        if found:
                            break

            if found:
                logger.info(f"✅ 样品接收日期已成功更新为: {formatted_date}")
                return True
            else:
                logger.warning("❌ 未找到匹配的样品接收日期段落")
                return False

        except Exception as e:
            logger.error(f"修改样品接收日期失败: {e}", exc_info=True)
            return False

    def modify_second_header(self, header_data: Dict[str, Any]) -> bool:
        """
        使用 win32com.client 精准填写 Word 第二节页眉中的 "Report No." 字段，
        替换其后的内容，保留原格式和换行符。

        :param header_data: 页眉数据字典，包含 report_no 等字段
        :return: 是否成功
        """
        return HeaderManager.modify_second_header(self.file_path, header_data, self.word_app)

    def cleanup(self):
        """清理资源"""
        try:
            if self.win_document:
                # 检查文档是否仍然可用
                try:
                    # 尝试访问文档的一个属性来检查连接状态
                    _ = self.win_document.Name
                    # 如果能成功访问，则关闭文档
                    self.win_document.Close()
                except (AttributeError, Exception):
                    # 如果文档已断开连接，则跳过关闭
                    pass
                self.win_document = None
            
            # 注意：不要关闭word_app，因为它可能是共享实例
            # 但在当前场景下，我们仍需确保它不会显示界面
            if self.word_app:
                try:
                    # 确保Word应用保持不可见状态
                    self.word_app.Visible = False
                except:
                    pass  # 如果设置不可见失败，则跳过
        except Exception as e:
            logger.debug(f"清理页眉修改器资源时出错: {e}")  # 改为debug级别，避免不必要的错误日志
    
    def __del__(self):
        """
        析构函数，确保Word应用程序资源被正确释放
        """
        try:
            if hasattr(self, 'win_document') and self.win_document is not None:
                try:
                    self.win_document.Close(SaveChanges=False)
                    logger.debug("HeaderModifier: Document closed on destruction")
                except:
                    pass  # 如果关闭失败，跳过
        except Exception as e:
            logger.error(f"在析构函数中关闭文档时出错: {e}")