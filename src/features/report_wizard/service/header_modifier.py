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
import win32com.client
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
        # 如果已有win_document（说明文档已被打开），直接使用它
        if self.win_document:
            return HeaderManager.modify_first_header_with_document(self.win_document, header_data)
        else:
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
        logger.info("使用传统方式修改样品接收日期")
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

    def update_document_content(self, data: Optional[Dict[str, Any]] = None, document_path: str = None, skip_save: bool = False) -> bool:
        """
        根据是否有数据来决定更新文档内容的方式
        如果提供了数据，则使用占位符替换方式；否则使用传统方式
        
        :param data: 包含替换数据的字典，如果为None则使用传统方式
        :param document_path: 要处理的文档路径，如果不提供则使用 self.file_path
        :param skip_save: 是否跳过保存操作，如果为True则不保存文档，供后续操作使用
        :return: 是否成功
        """
        if data:
            # 有数据时，使用新的占位符替换方式
            logger.info("检测到项目数据，使用占位符替换方式更新文档内容")
            return self.replace_document_placeholders(data, document_path, skip_save)
        else:
            # 没有数据时，使用传统的样品接收日期修改方式
            logger.info("未检测到项目数据，使用传统方式更新样品接收日期")
            # 直接调用 _modify_sample_received_date_fallback 方法
            target_path = document_path if document_path else self.file_path
            return self._modify_sample_received_date_fallback(target_path)

    def replace_document_placeholders(self, data: Dict[str, Any], document_path: str = None, skip_save: bool = False) -> bool:
        """
        使用 win32com.client 根据 JSON 数据替换 Word 文档中的占位符
        
        :param data: 包含替换数据的字典
        :param document_path: 要处理的文档路径，如果不提供则使用 self.file_path
        :param skip_save: 是否跳过保存操作，如果为True则不保存文档，供后续操作使用
        :return: 是否成功
        """
        win_document = None
        try:
            # 确定要处理的文档路径
            target_path = document_path if document_path else self.file_path
            
            logger.info(f"开始使用占位符替换方式更新文档: {target_path}")
            
            # 获取共享的 Word 应用程序实例
            word_app = get_shared_word_app()
            if not word_app:
                logger.error("无法获取Word应用程序实例")
                return False
            
            # 确保Word应用程序不可见
            word_app.Visible = False
            word_app.DisplayAlerts = False
            
            # 打开文档
            win_document = word_app.Documents.Open(os.path.normpath(target_path))
            
            # 保存对win_document的引用，以便后续操作使用
            if skip_save:
                self.win_document = win_document
            
            # 提取所需字段
            original_date = data.get("date_lab_received_samples", "")
            gs_info = data.get("applicable_specifications", "")
            product_name = data.get("product_description", "")
            test_description = data.get("tests_to_be_performed", "")
            
            logger.info(f"从项目数据中提取字段: date='{original_date}', gs_info='{gs_info}', product_name='{product_name}', test_description='{test_description}'")
            
            # 使用 DateHandler 格式化日期
            formatted_date = DateHandler.format_date_to_month_day_year(original_date)
            
            # 执行替换
            replacements = {
                "[RECEIVED SAMPLES DATE]": formatted_date,
                "[GS-XX-XXXX (Rev.X, DATE)]": gs_info,
                "[PRODUCT NAME]": product_name,
                "[TEST DESCRIPTION]": test_description
            }
            
            for find_text, replace_text in replacements.items():
                if find_text and replace_text:  # 只处理非空的替换
                    logger.debug(f"替换占位符: '{find_text}' -> '{replace_text}'")
                    # 使用 Word 的查找替换功能
                    find_obj = win_document.Content.Find
                    find_obj.ClearFormatting()
                    find_obj.Text = find_text
                    find_obj.Replacement.ClearFormatting()
                    find_obj.Replacement.Text = replace_text
                    # 执行替换所有匹配项
                    find_obj.Execute(Replace=2, Forward=True)  # wdReplaceAll = 2
            
            # 根据skip_save参数决定是否保存文档
            if not skip_save:
                win_document.Save()
                logger.info(f"✅ 文档占位符替换完成并已保存: {target_path}")
            else:
                logger.info(f"✅ 文档占位符替换完成，跳过保存: {target_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"替换文档占位符失败: {e}", exc_info=True)
            return False
        finally:
            # 根据skip_save参数决定是否关闭文档
            # 如果skip_save为True，意味着文档需要供后续操作使用，因此不关闭
            # 如果skip_save为False，可以安全关闭文档
            if win_document and skip_save is False:
                try:
                    win_document.Close()
                except:
                    pass  # 如果关闭失败，跳过

    def _modify_sample_received_date_fallback(self, document_path: str) -> bool:
        """
        使用win32com.client的传统方式修改样品接收日期
        这是用于没有项目数据时的备选方案
        """
        logger.info(f"使用传统方式（fallback）修改样品接收日期: {document_path}")
        try:
            # 获取共享的 Word 应用程序实例
            word_app = get_shared_word_app()
            if not word_app:
                logger.error("无法获取Word应用程序实例")
                return False
            
            # 确保Word应用程序不可见
            word_app.Visible = False
            word_app.DisplayAlerts = False
            
            # 打开文档
            win_document = word_app.Documents.Open(os.path.normpath(document_path))
            
            # 查找包含样品接收信息的段落并使用当前日期替换
            # 这是简化版本，实际可根据需要扩展
            import re
            sample_received_pattern = r"(Samples were received at the laboratory on )(.+?)(\. Prior to testing)"
            
            # 遍历文档中的所有段落
            for para in win_document.Paragraphs:
                original_text = para.Range.Text
                if "Samples were received at the laboratory on" in original_text:
                    # 使用当前日期替换
                    from datetime import datetime
                    current_date = datetime.now().strftime("%b %d, %Y")  # 格式如 "Dec 20, 2024"
                    
                    # 使用正则表达式替换日期
                    new_text = re.sub(sample_received_pattern, 
                                     rf"\g<1>{current_date}\g<3>", 
                                     original_text)
                    
                    if new_text != original_text:
                        para.Range.Text = new_text
                        logger.info(f"样品接收日期已更新: '{original_text}' -> '{new_text}'")
                        break
            
            logger.info(f"✅ 传统方式文档更新完成: {document_path}")
            return True
            
        except Exception as e:
            logger.error(f"传统方式更新文档失败: {e}", exc_info=True)
            return False

    def modify_second_header(self, header_data: Dict[str, Any]) -> bool:
        """
        使用 win32com.client 精准填写 Word 第二节页眉中的 "Report No." 字段，
        替换其后的内容，保留原格式和换行符。

        :param header_data: 页眉数据字典，包含 report_no 等字段
        :return: 是否成功
        """
        # 如果已有win_document（说明文档已被打开），直接使用它
        if self.win_document:
            return HeaderManager.modify_second_header_with_document(self.win_document, header_data)
        else:
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