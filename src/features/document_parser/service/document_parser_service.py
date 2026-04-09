"""
文档解析服务模块
提供文档解析和处理的核心功能
"""

import os
import shutil
import json
from typing import Dict, Any, Optional
import win32com.client
import pythoncom
from src.core.logger import logger
from src.utils.word_utils import get_shared_word_app, release_word_app, open_word_file
from src.utils.file_utils import ensure_directory_exists


class DocumentParserService:
    """
    文档解析服务类
    提供文档解析和处理的核心功能
    """

    def __init__(self):
        """初始化文档解析服务"""
        pass

    def copy_ltr_application_form(self, application_data: Dict[str, Any], submitted_dir: str, src_dir: str) -> bool:
        """
        复制LTR申请单到submitted目录

        Args:
            application_data: 申请数据
            submitted_dir: 提交目录路径
            src_dir: 源目录路径

        Returns:
            是否成功复制
        """
        try:
            # 确保目标目录存在
            if not ensure_directory_exists(submitted_dir):
                logger.error(f"无法创建或访问目录: {submitted_dir}")
                return False

            # 获取选中的文件名和DL编号
            selected_filename = application_data.get('selected_filename', '')
            dl_number = application_data.get('DL', '')
            logger.debug(f"选中的文件名: {selected_filename}")
            logger.debug(f"DL编号: {dl_number}")

            # 先复制所有文件到Submitted Material目录
            self._copy_all_files_to_submitted(src_dir, submitted_dir)

            # 如果有选中的文件名，则查找完全匹配的文件
            if selected_filename:
                submitted_files = [f for f in os.listdir(submitted_dir) 
                                 if os.path.isfile(os.path.join(submitted_dir, f))]
                
                # 查找完全匹配的文件
                matched_files = [f for f in submitted_files if f == selected_filename]
                
                if matched_files:
                    # 找到匹配的文件，不需要额外操作
                    logger.info(f"找到匹配的文件: {selected_filename}")
                    return True
                else:
                    # 没有找到匹配的文件，从模板文件夹复制
                    logger.warning(f"在Submitted Material中未找到匹配的文件: {selected_filename}")
                    return self._copy_from_template(submitted_dir, selected_filename, dl_number)
            else:
                # selected_filename为空，从模板文件夹复制
                logger.info("selected_filename为空，从模板文件夹复制文件")
                return self._copy_from_template(submitted_dir, selected_filename, dl_number)

        except Exception as e:
            logger.error(f"复制LTR申请单时出错: {e}", exc_info=True)
            return False

    def _copy_all_files_to_submitted(self, src_dir: str, submitted_dir: str) -> None:
        """
        复制所有相关文件到Submitted Material目录

        Args:
            src_dir: 源目录路径
            submitted_dir: 提交目录路径
        """
        try:
            # 复制除.msg和application_data.json之外的所有文件
            other_files = [
                f for f in os.listdir(src_dir)
                if os.path.isfile(os.path.join(src_dir, f))
                   and not f.endswith(".msg")  # 排除.msg文件，因为它们在Step 7中已经处理过了
                   and f != "application_data.json"
            ]
            
            for f in other_files:
                src_path = os.path.join(src_dir, f)
                dst_path = os.path.join(submitted_dir, f)
                try:
                    shutil.copy2(src_path, dst_path)
                    logger.info(f"复制文件: {src_path} -> {dst_path}")
                except Exception as e:
                    logger.error(f"复制文件失败: {src_path} -> {dst_path}, 错误: {e}")
        except Exception as e:
            logger.error(f"复制文件到Submitted Material时出错: {e}", exc_info=True)

    def _copy_from_template(self, submitted_dir: str, selected_filename: str, dl_number: str = "") -> bool:
        """
        从模板文件夹复制文件

        Args:
            submitted_dir: 提交目录路径
            selected_filename: 选中的文件名
            dl_number: LTR编号，用于重命名文件

        Returns:
            是否成功复制
        """
        try:
            # 获取模板目录
            from src.core.config_manager import config_manager
            template_dir = config_manager.get_template_dir()
            ltr_template_dir = os.path.join(template_dir, "LTR")
            
            if not os.path.exists(ltr_template_dir):
                logger.warning(f"LTR模板目录不存在: {ltr_template_dir}")
                # 尝试查找E-3718开头的文件作为备选
                return self._copy_e3718_file(submitted_dir)
            
            # 查找模板文件
            template_files = [f for f in os.listdir(ltr_template_dir) 
                            if os.path.isfile(os.path.join(ltr_template_dir, f))]
            
            if not template_files:
                logger.warning(f"LTR模板目录中没有文件: {ltr_template_dir}")
                return self._copy_e3718_file(submitted_dir)
            
            source_file = None
            dest_file = None
            
            # 如果有选中的文件名，尝试查找匹配的模板
            if selected_filename:
                matched_templates = [f for f in template_files if f == selected_filename]
                if matched_templates:
                    source_file = os.path.join(ltr_template_dir, matched_templates[0])
                    # 使用LTR编号重命名文件
                    if dl_number:
                        name, ext = os.path.splitext(matched_templates[0])
                        dest_file = os.path.join(submitted_dir, f"{dl_number} Laboratory Test Request{ext}")
                    else:
                        dest_file = os.path.join(submitted_dir, matched_templates[0])
            
            # 如果没有匹配的文件或没有指定selected_filename，使用第一个模板文件
            if not source_file:
                source_file = os.path.join(ltr_template_dir, template_files[0])
                # 使用LTR编号重命名文件
                if dl_number:
                    name, ext = os.path.splitext(template_files[0])
                    dest_file = os.path.join(submitted_dir, f"{dl_number} Laboratory Test Request{ext}")
                else:
                    dest_file = os.path.join(submitted_dir, template_files[0])
            
            shutil.copy2(source_file, dest_file)
            logger.info(f"从模板复制文件: {source_file} -> {dest_file}")
            return True
            
        except Exception as e:
            logger.error(f"从模板复制文件时出错: {e}", exc_info=True)
            return self._copy_e3718_file(submitted_dir)

    def _copy_e3718_file(self, submitted_dir: str) -> bool:
        """
        查找并复制E-3718开头的文件

        Args:
            submitted_dir: 提交目录路径

        Returns:
            是否成功复制
        """
        try:
            # 在Submitted Material目录中查找E-3718文件
            e3718_files = [f for f in os.listdir(submitted_dir) 
                          if f.startswith('E-3718') and os.path.isfile(os.path.join(submitted_dir, f))]
            
            if e3718_files:
                logger.info(f"找到E-3718文件: {e3718_files[0]}")
                return True
            
            logger.warning("未找到E-3718文件")
            return False
        except Exception as e:
            logger.error(f"查找E-3718文件时出错: {e}", exc_info=True)
            return False

    def update_word_document(self, file_path: str, application_data: Dict[str, Any]) -> bool:
        """
        更新Word文档内容，分别处理页眉和表格内容

        Args:
            file_path: Word文档路径
            application_data: 应用数据

        Returns:
            是否成功更新
        """
        word_app = None
        doc = None
        try:
            # 初始化COM
            pythoncom.CoInitialize()
            
            # 创建Word应用实例
            word_app = win32com.client.Dispatch("Word.Application")
            word_app.Visible = False  # 确保Word应用程序不可见
            word_app.DisplayAlerts = False  # 禁用显示警告
            
            # 打开文档
            doc = word_app.Documents.Open(file_path, ReadOnly=False)
            
            # 先处理页眉中的LTR编号
            dl_number = application_data.get('DL', application_data.get('dl_number', ''))
            if dl_number:
                self._update_header_ltr_number(doc, dl_number)
            
            # 定义文档更新字段映射表
            update_field_map = {
                'Project Type': ('project_type', True),
                'Test Type': ('test_type', True),
                'Requested By:': ('requested_by', False),
                'Mfg. Site:': ('location', False),
                'Can testing be subcontracted?': ('sub_contract', False),
                'Phone #:': ('phone', False),
                'Email:': ('email_requestor', False),
                'Lab Performing the Tests:': ('lab_performing_the_tests', False),
                'Condition of Samples when Received:': ('condition_of_samples_when_received', False),
                'Lab Personnel Assigned:': ('project_leader', False),
                'Date Lab Received Samples:': ('date_lab_received_samples', False),
                'Estimated Completion Date:': ('estimated_completion_date', False),
            }
            
            # 构建要写入文档的字段映射
            modifications = []
            for keyword, (field_key, next_row) in update_field_map.items():
                value = application_data.get(field_key, '')
                logger.debug(f"字段 '{keyword}' 对应值 '{value}' 准备写入")
                modifications.append({'keyword': keyword, 'new_value': value, 'next_row': next_row})

            # 应用修改到表格内容
            for mod in modifications:
                keyword = mod.get("keyword")
                new_value = mod.get("new_value", "")
                next_row = mod.get("next_row", False)
                
                target_cell = self._find_target_cell_after_keyword(doc, keyword, next_row)
                if target_cell:
                    success = self._modify_cell_content(target_cell, new_value)
                    if success:
                        logger.info(f"修改字段 '{keyword}' 为 '{new_value}'")
                    else:
                        logger.warning(f"修改字段 '{keyword}' 失败")
                else:
                    logger.warning(f"未找到关键词 '{keyword}'")

            # 保存文档
            doc.Save()
            
            logger.info(f"成功更新Word文档: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"更新Word文档时出错: {e}", exc_info=True)
            return False
        finally:
            # 确保资源被正确释放
            try:
                if doc:
                    doc.Close()
                if word_app:
                    word_app.Quit()
            except Exception as e:
                logger.error(f"关闭Word文档时出错: {e}")
            finally:
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass

    def _update_header_ltr_number(self, doc, dl_number: str) -> bool:
        """
        更新文档页眉中的LTR编号

        Args:
            doc: Word文档对象
            dl_number: LTR编号

        Returns:
            是否成功更新
        """
        try:
            for section in doc.Sections:
                # 只检查主页眉
                header = section.Headers(1)  # wdHeaderFooterPrimary = 1
                if not header.Exists:
                    continue

                for table in header.Range.Tables:
                    for i in range(1, table.Rows.Count + 1):
                        for j in range(1, table.Columns.Count + 1):
                            try:
                                cell = table.Cell(i, j)
                                cell_text = cell.Range.Text.replace('\a', '').strip()

                                if "Lab Test Request Number:" in cell_text:
                                    paragraphs = cell.Range.Paragraphs
                                    para_texts = [para.Range.Text.replace('\a', '') for para in paragraphs]

                                    # 找到起始段落索引
                                    start_index = None
                                    for idx, text in enumerate(para_texts):
                                        if "Lab Test Request Number:" in text.strip():
                                            start_index = idx
                                            break
                                    if start_index is None:
                                        continue

                                    # 找到结束段落索引（以 "Page" 开头）
                                    end_index = None
                                    for idx in range(start_index + 1, len(para_texts)):
                                        if para_texts[idx].strip().startswith("Page"):
                                            end_index = idx
                                            break
                                    if end_index is None:
                                        continue

                                    logger.info(f"找到 'Lab Test Request Number:' 段落，索引: {start_index}")
                                    logger.info(f"找到 'Page' 段落，索引: {end_index}")

                                    # 删除 start_index+1 到 end_index-1 之间的段落（从后往前删）
                                    for idx in range(end_index - 1, start_index, -1):
                                        paragraphs(idx + 1).Range.Delete()  # Word 段落索引从 1 开始

                                    # 插入空白段落和新测试编号段落
                                    insert_range = paragraphs(start_index + 1).Range
                                    insert_range.InsertAfter("\r")  # 插入空白段落
                                    insert_range.InsertAfter(dl_number + "\r")  # 插入新编号

                                    logger.info(f"成功在页眉中插入新测试编号: {dl_number}")
                                    return True

                            except Exception as e:
                                logger.error(f"处理页眉单元格时出错: {e}")
                                continue

            logger.warning("未找到匹配的 'Lab Test Request Number:' 单元格")
            return False

        except Exception as e:
            logger.error(f"修改页眉测试编号时出错: {str(e)}")
            return False

    def _find_target_cell_after_keyword(self, doc, search_keyword: str, next_row: bool = False):
        """
        在文档表格中查找包含关键词的单元格，并返回指定相邻单元格

        Args:
            doc: Word文档对象
            search_keyword: 搜索关键词
            next_row: 是否在下一行查找目标单元格

        Returns:
            目标单元格对象，如果未找到则返回None
        """
        try:
            for table in doc.Tables:
                for i in range(1, table.Rows.Count + 1):
                    for j in range(1, table.Columns.Count + 1):
                        try:
                            cell_text = table.Cell(i, j).Range.Text.strip().replace('\r', '').replace('\a', '').strip()
                            if search_keyword.lower() in cell_text.lower():
                                target_cell = None
                                if next_row and i < table.Rows.Count:
                                    target_cell = table.Cell(i + 1, j)
                                elif not next_row and j < table.Columns.Count:
                                    target_cell = table.Cell(i, j + 1)
                                if target_cell:
                                    return target_cell
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"查找目标单元格时出错: {e}")
        return None

    def _modify_cell_content(self, cell, new_text: str) -> bool:
        """
        修改单元格内容，支持内容控件和表单字段

        Args:
            cell: Word单元格对象
            new_text: 新的文本内容

        Returns:
            是否成功修改
        """
        try:
            if cell.Range.ContentControls.Count > 0:
                cc = cell.Range.ContentControls(1)
                logger.debug(f"ContentControl Title: '{cc.Title}', Type: {cc.Type}, Locked: {cc.LockContents}")
                if hasattr(cc, 'LockContents') and cc.LockContents:
                    logger.warning(f"Content control is locked; cannot modify: '{cc.Title}'")
                    return False
                if cc.Type == 4:  # Dropdown list
                    found = False
                    for entry in cc.DropdownListEntries:
                        option_text = entry.Text.strip().replace('\r', '').replace('\a', '')
                        if option_text == new_text:
                            entry.Select()
                            found = True
                            break
                    if not found:
                        logger.warning(f"Dropdown option '{new_text}' not found in content control")
                        return False
                    return True
                elif cc.Type == 3:
                    cc.Range.Text = new_text
                    return True
                elif cc.Type == 2:  # ComboBox ContentControl
                    cc.Dropdown.Select(new_text)
                    return True
                elif cc.Type in [0, 1]:  # RichText or PlainText ContentControl
                    cc.Range.Text = new_text
                    return True
                elif cc.Type == 6:  # Date ContentControl
                    cc.Range.Text = new_text
                    return True
                else:
                    logger.warning(f"Unsupported content control type {cc.Type}")
                    return False
            elif cell.Range.FormFields.Count > 0:
                ff = cell.Range.FormFields(1)
                if ff.Type == 70:  # Text Input FormField
                    ff.Result = new_text
                    return True
                else:
                    logger.warning(f"Unsupported FormField type {ff.Type}")
                    return False
            else:
                cell.Range.Text = new_text
                return True
        except Exception as e:
            logger.error(f"修改单元格内容时出错: {e}")
            return False

    def process_word_document(self, file_path: str) -> Dict[str, Any]:
        """
        处理Word文档，提取内容

        Args:
            file_path: Word文档路径

        Returns:
            提取的数据
        """
        try:
            # 初始化COM
            pythoncom.CoInitialize()
            
            # 创建Word应用实例
            word_app = win32com.client.Dispatch("Word.Application")
            word_app.Visible = False  # 确保Word应用程序不可见
            word_app.DisplayAlerts = False  # 禁用显示警告
            
            # 打开文档
            doc = word_app.Documents.Open(file_path, ReadOnly=True)
            
            # 提取数据的逻辑可以在这里实现
            # 这里只是示例，实际实现需要根据具体需求来定
            
            data = {}
            
            # 关闭文档和应用
            doc.Close()
            word_app.Quit()
            
            # 反初始化COM
            pythoncom.CoUninitialize()
            
            return data
            
        except Exception as e:
            logger.error(f"处理Word文档时出错: {e}", exc_info=True)
            # 确保即使出错也反初始化COM
            try:
                pythoncom.CoUninitialize()
            except:
                pass
            return {"error": str(e)}
