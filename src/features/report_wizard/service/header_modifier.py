"""
页眉修改服务模块
提供Word文档页眉修改相关的业务逻辑服务
"""

import os
from typing import Optional, Dict, Any
import pythoncom
from src.core.logger import logger

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

    def __init__(self, file_path: str, office_facade=None):
        """初始化页眉修改服务"""
        from src.infrastructure.office.facade import OfficeFacade
        self.file_path = file_path
        self._office_facade = office_facade or OfficeFacade()
        self.doc = None
        self.win_document = None
        self.word_app = None
        self._owns_win_document = False
        self._win_document_path = None

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
            # ✅ 使用 self._office_facade 管理生命周期
            return HeaderManager.modify_first_header(self.file_path, header_data, self._office_facade)

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

    def modify_revision_record_date_win32com(self, header_data: Dict[str, Any], is_customer_report: bool = False) -> bool:
        """
        使用win32com修改正文 'REVISION RECORD' 表格中的日期
        
        :param header_data: 页眉数据字典，包含 completion_date 等字段
        :param is_customer_report: 是否是客户报告，默认为 False
        :return: 是否成功
        """
        try:
            # 如果已有win_document（说明文档已被打开），直接使用它
            if self.win_document:
                return TableHandler.modify_revision_record_date_win32com(self.win_document, header_data, is_customer_report)
            else:
                # word_app 必须由调用方提供（通过 OfficeFacade session）
                if self.word_app is None:
                    logger.error("word_app 未设置，应由调用方通过 OfficeFacade session 提供")
                    return False
                
                self.word_app.Visible = False
                self.word_app.DisplayAlerts = False
                
                # 打开文档
                win_document = self.word_app.Documents.Open(os.path.normpath(self.file_path))
                
                try:
                    result = TableHandler.modify_revision_record_date_win32com(win_document, header_data, is_customer_report)
                    # 不保存文档，因为后续还有其他操作
                    return result
                finally:
                    try:
                        win_document.Close(SaveChanges=False)
                    except Exception as close_error:
                        logger.error(f"关闭修订记录日期文档时出错: {close_error}")

        except Exception as e:
            logger.error(f"使用win32com修改修订记录日期失败: {e}", exc_info=True)
            return False

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

    def update_document_content(self, data: Optional[Dict[str, Any]] = None, document_path: str = None) -> bool:
        """
        根据是否有数据来决定更新文档内容的方式
        如果提供了数据，则使用占位符替换方式；否则使用传统方式
        
        :param data: 包含替换数据的字典，如果为None则使用传统方式
        :param document_path: 要处理的文档路径，如果不提供则使用 self.file_path
        :return: 是否成功
        """
        if data:
            # 有数据时，使用新的占位符替换方式
            logger.info("检测到项目数据，使用占位符替换方式更新文档内容")
            return self.replace_document_placeholders(data, document_path)
        else:
            # 没有数据时，使用传统的样品接收日期修改方式
            logger.info("未检测到项目数据，使用传统方式更新样品接收日期")
            # 直接调用 _modify_sample_received_date_fallback 方法
            target_path = document_path if document_path else self.file_path
            return self._modify_sample_received_date_fallback(target_path)

    def _get_or_open_document(self, document_path: str):
        """Return the active document or open it via the caller-provided Word app."""
        if self.win_document:
            return self.win_document

        if self.word_app is None:
            logger.error("word_app 未设置，应由调用方通过 OfficeFacade session 提供")
            return None

        self.word_app.Visible = False
        self.word_app.DisplayAlerts = False
        normalized_path = os.path.normcase(os.path.abspath(os.path.normpath(document_path)))
        existing_document = self._find_open_document_by_path(normalized_path)
        if existing_document is not None:
            self.win_document = existing_document
            self._owns_win_document = False
            self._win_document_path = normalized_path
            logger.debug(f"复用已打开的 Word 文档，不关闭用户文档: {document_path}")
            return self.win_document

        self.win_document = self.word_app.Documents.Open(os.path.normpath(document_path))
        self._owns_win_document = True
        self._win_document_path = normalized_path
        logger.debug(f"通过调用方提供的 Word session 打开文档: {document_path}")
        return self.win_document

    def _find_open_document_by_path(self, normalized_path: str):
        """Find an already-open Word document by normalized absolute path."""
        try:
            for opened_document in self.word_app.Documents:
                try:
                    opened_path = os.path.normcase(
                        os.path.abspath(os.path.normpath(opened_document.FullName))
                    )
                except Exception:
                    continue
                if opened_path == normalized_path:
                    return opened_document
        except TypeError:
            logger.debug("当前 Word 文档集合不可遍历，跳过已打开文档检测")
        except Exception as exc:
            logger.debug(f"检测已打开 Word 文档失败，继续按新文档打开: {exc}")
        return None

    def close_owned_document(self) -> bool:
        """Close the current document only when this workflow owns it."""
        if self.win_document is None:
            return False

        if not self._owns_win_document:
            logger.debug("当前 Word 文档非本流程打开，跳过关闭")
            self.win_document = None
            self._win_document_path = None
            return False

        try:
            self.win_document.Close(SaveChanges=False)
            return True
        except pythoncom.com_error:
            logger.debug("Word文档COM连接已断开，跳过关闭")
        except (AttributeError, Exception) as exc:
            logger.debug(f"关闭Word文档时出错，跳过关闭: {exc}")
        finally:
            self.win_document = None
            self._owns_win_document = False
            self._win_document_path = None
        return False

    def replace_document_placeholders(self, data: Dict[str, Any], document_path: str = None) -> bool:
        """
        使用 win32com.client 根据 JSON 数据替换 Word 文档中的占位符
        
        :param data: 包含替换数据的字典
        :param document_path: 要处理的文档路径，如果不提供则使用 self.file_path
        :param output_path: 输出文档路径，如果不提供则使用原文件目录下的test_contact.docx
        :return: 是否成功
        """
        win_document = None
        try:
            # 确定要处理的文档路径
            target_path = document_path if document_path else self.file_path
            
            logger.info(f"使用 win32com.client 根据 JSON 数据替换 Word 文档中的占位符: {target_path}")
            logger.info(f"开始使用占位符替换方式更新文档: {target_path}")
            
            win_document = self._get_or_open_document(target_path)
            if win_document is None:
                return False
            logger.debug(f"使用文档实例操作占位符替换: {target_path}")
            
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
            
             # 统计替换结果
            replacement_stats = {}
            total_replacements = 0

            # 先统计各占位符的出现次数，再执行替换
            for placeholder, value in replacements.items():
                # 统计替换前的出现次数
                original_content = win_document.Range().Text
                original_count = original_content.count(placeholder)
                replacement_stats[placeholder] = original_count

                logger.debug(f"占位符 '{placeholder}' 在文档中出现 {original_count} 次")

                # 执行替换 - 使用正确的参数格式
                # 修复：根据经验教训，我们应该允许将占位符替换为空字符串，只要占位符本身存在
                if placeholder is not None and placeholder:  # 只要占位符存在就执行替换，无论替换值是否为空
                    logger.debug(f"替换占位符: '{placeholder}' -> '{value}'")
                    # 使用 Word 的查找替换功能
                    find_obj = win_document.Content.Find
                    find_obj.ClearFormatting()
                    find_obj.Text = placeholder
                    find_obj.Replacement.ClearFormatting()
                    find_obj.Replacement.Text = value
                    find_obj.Wrap = 1  # wdFindContinue
                    # 正确的Execute参数顺序: FindText, MatchCase, MatchWholeWord, 
                    # MatchWildcards, MatchSoundsLike, MatchAllWordForms, Forward, 
                    # Wrap, MatchByte, ReplaceWith, Replace
                    find_obj.Execute(placeholder, False, False, False, False, False, True, 1, False, value, 2)  # wdReplaceAll = 2
                    logger.debug(f"占位符 '{placeholder}' 替换执行完成")
                else:
                    logger.debug(f"跳过替换，因为占位符为空: placeholder='{placeholder}'")
            
            # 计算总替换次数
            total_replacements = sum(replacement_stats.values())

            # 输出替换统计（调试级别）
            logger.debug(f"替换完成统计:")
            for placeholder, count in replacement_stats.items():
                status = "✅" if count > 0 else "❌"
                logger.debug(f"   {status} '{placeholder}': 替换了 {count} 次")

            logger.debug(f"总计替换次数: {total_replacements}")

            if total_replacements == 0:
                logger.warning("警告: 未找到任何占位符进行替换，请检查模板文件！")
            else:
                logger.info("✅ 所有占位符替换完成！")
            
            # # 先保存文档到原始路径，确保修改生效
            # win_document.Save()
            # logger.info(f"✅ 文档占位符替换完成并已保存到原始路径: {target_path}")

            return True
            
        except Exception as e:
            logger.error(f"替换文档占位符失败: {e}", exc_info=True)
            return False
        # 不关闭文档，让主程序负责管理文档的生命周期

    def _modify_sample_received_date_fallback(self, document_path: str) -> bool:
        """
        使用win32com.client的传统方式修改样品接收日期
        这是用于没有项目数据时的备选方案
        """
        logger.info(f"使用传统方式（fallback）修改样品接收日期: {document_path}")
        try:
            win_document = self._get_or_open_document(document_path)
            if win_document is None:
                return False

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
            # ✅ 使用 self._office_facade 管理生命周期
            return HeaderManager.modify_second_header(self.file_path, header_data, self._office_facade)

    def cleanup(self):
        """清理资源"""
        try:
            if self.win_document:
                self.close_owned_document()
            
            # 注意：不要关闭word_app，因为它可能是共享实例
            # 但在当前场景下，我们仍需确保它不会显示界面
            if self.word_app:
                try:
                    # 确保Word应用保持不可见状态
                    self.word_app.Visible = False
                except pythoncom.com_error:
                    logger.debug("Word应用程序COM连接已断开，跳过设置可见性")
                    pass  # 如果设置不可见失败，则跳过
                except:
                    pass  # 如果设置不可见失败，则跳过
        except Exception as e:
            logger.debug(f"清理页眉修改器资源时出错: {e}")  # 改为debug级别，避免不必要的错误日志
    
    def __del__(self):
        """
        析构函数，确保Word应用程序资源被正确释放
        """
        try:
            if (
                hasattr(self, 'win_document')
                and self.win_document is not None
                and getattr(self, '_owns_win_document', False)
            ):
                try:
                    self.close_owned_document()
                    logger.debug("HeaderModifier: Document closed on destruction")
                except:
                    pass  # 如果关闭失败，跳过
        except Exception as e:
            logger.error(f"在析构函数中关闭文档时出错: {e}")
