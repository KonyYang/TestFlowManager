"""
报告更新模块服务层
处理报告更新的具体业务逻辑
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
from src.core.project_context import ProjectContext, get_current_project_context


class EquipmentConfigManager:
    """设备更新配置管理器"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self):
        """加载设备更新配置"""
        # 从INI配置文件中读取设备数据源配置
        excel_file_path = config_manager.get("equipment_data_sources.excel_file_path", 
            "D:\\Source\\FCI Dongguan product test laboratory equipment list for report- Huan Revised.xls")
        default_source_doc_path = config_manager.get("equipment_data_sources.source_doc_path", 
            "D:\\OutFile\\EquipmentID.docx")
        default_output_path = config_manager.get("equipment_data_sources.default_output_path", 
            "D:\\OutFile\\")
        
        # 检查当前是否有项目打开，如果有则在项目目录下查找EquipmentID.docx
        # 优先使用实例变量中存储的项目路径
        if hasattr(self, 'project_path') and self.project_path and os.path.exists(self.project_path):
            # 在项目目录下查找EquipmentID.docx
            project_equipment_doc_path = os.path.join(self.project_path, "EquipmentID.docx")
            if os.path.exists(project_equipment_doc_path):
                source_doc_path = project_equipment_doc_path
            else:
                # 如果项目目录下没有EquipmentID.docx，弹出提醒信息并退出
                from PyQt5.QtWidgets import QMessageBox
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("文件未找到")
                msg_box.setText("当前项目路径下没有EquipmentID.docx")
                msg_box.exec_()
                # 抛出异常以中断配置加载
                raise FileNotFoundError(f"项目目录下未找到EquipmentID.docx: {project_equipment_doc_path}")
        else:
            # 没有项目打开时，使用默认路径
            source_doc_path = default_source_doc_path
        
        return {
            "equipment_data_sources": {
                "excel_file_path": excel_file_path,
                "source_doc_path": source_doc_path,
                "default_output_path": default_output_path
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
    
    def __init__(self, project_path: str = None, project_context: Optional[ProjectContext] = None):
        """初始化报告更新服务"""
        self.project_context = project_context or get_current_project_context()
        if self.project_context is None and project_path:
            self.project_context = ProjectContext.from_project_path(project_path)
        self.config_manager = EquipmentConfigManager()
        # 优先使用上下文中的项目路径，兼容旧 project_path 入口
        if self.project_context:
            self.config_manager.project_path = self.project_context.project_path
        elif project_path:
            self.config_manager.project_path = project_path
        self.config = self.config_manager.get_config()
        logger.info("ReportUpdaterService initialized")
    
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
                return self._update_equipment_list_in_excel(report_path, equipment_data)
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
        从文档中提取设备ID，查找所有非表格中的段落内容
        """
        try:
            logger.debug(f"Extracting equipment IDs from document: {doc_path}")
            doc = Document(doc_path)
            unique_ids = OrderedDict()
            
            # 检查文档级段落（不在表格中的段落）
            for i, paragraph in enumerate(doc.paragraphs):
                para_text = paragraph.text.strip()
                # 检查段落是否包含设备ID模式（如Q-XXXX或L-XXXX或DG-开头）
                if para_text and (re.search(r'(Q-\\d{4}|L-\\d{4})', para_text, re.IGNORECASE) or "DG-" in para_text.upper()):
                    clean_text = para_text.replace('\\r\\n', '').replace('\\n', '').strip()
                    # 添加去重逻辑
                    if clean_text not in unique_ids:
                        unique_ids[clean_text] = True
                        # logger.debug(f"Found equipment ID in paragraph {i}: {clean_text}")
            
            # 还要检查表格中的内容（以防设备ID在表格中）
            for i, table in enumerate(doc.tables):
                for row in table.rows:
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text and (re.search(r'(Q-\\d{4}|L-\\d{4})', cell_text, re.IGNORECASE) or "DG-" in cell_text.upper()):
                            clean_text = cell_text.replace('\\r\\n', '').replace('\\n', '').strip()
                            if clean_text not in unique_ids:
                                unique_ids[clean_text] = True
                                # logger.debug(f"Found equipment ID in table {i}: {clean_text}")
            
            ids_list = list(unique_ids.keys())
            logger.info(f"Total {len(ids_list)} unique equipment IDs extracted")
            return ids_list
        except Exception as e:
            logger.error(f"Error reading source document: {e}")
            return []

    def _find_equipment_table_win32com(self, word_doc, paragraph_keyword: str = "EQUIPMENTS"):
        """
        使用win32com在Word文档中根据段落关键字查找紧跟其后的表格

        Args:
            word_doc: win32com Word文档对象
            paragraph_keyword: 段落中的关键字（如"EQUIPMENTS"）

        Returns:
            找到的表格对象，如果未找到则返回None
        """
        print(f"Using win32com to find table after paragraph with keyword '{paragraph_keyword}'")

        # 遍历文档中的所有段落
        print(f"DEBUG: Total paragraphs in document: {word_doc.Paragraphs.Count}")
        for i in range(1, word_doc.Paragraphs.Count + 1):
            paragraph = word_doc.Paragraphs(i)
            para_text = paragraph.Range.Text.strip()
            
            # 简单地查找'EQUIPMENTS'是否匹配，根据用户需求简化匹配逻辑
            pattern = re.escape('EQUIPMENTS')
            if re.search(pattern, para_text, re.IGNORECASE):
                table_positions = []
                for j in range(1, word_doc.Tables.Count + 1):
                    doc_table = word_doc.Tables(j)
                    # 记录表格在文档中的位置
                    table_positions.append((doc_table.Range.Start, doc_table))
                    print(f"DEBUG: Table {j} starts at position {doc_table.Range.Start}")

                # 按表格起始位置排序
                table_positions.sort(key=lambda x: x[0])

                # 查找紧跟在此段落后的第一个表格
                paragraph_end_pos = paragraph.Range.End
                print(f"DEBUG: Paragraph ends at position {paragraph_end_pos}")
                for pos, table in table_positions:
                    print(f"DEBUG: Checking table at position {pos}, paragraph ends at {paragraph_end_pos}")
                    if pos >= paragraph_end_pos:
                        print(f"DEBUG: Found table after paragraph at position {pos}")
                        print(f"Found table after paragraph")
                        return table

        print(f"Table with keyword '{paragraph_keyword}' not found")
        return None

    def _format_date(self, date_value):
        """将日期格式转换为 DD-MMM-YYYY 格式，例如 02-Aug-2024"""
        try:
            # 检查是否已经是datetime对象
            if isinstance(date_value, datetime):
                return date_value.strftime('%d-%b-%Y')
            # 检查是否是字符串格式的日期
            elif isinstance(date_value, str) and date_value.strip():
                # 尝试解析常见的日期格式
                for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%m-%d-%Y', '%d.%m.%Y', '%Y.%m.%d'):
                    try:
                        parsed_date = datetime.strptime(date_value.strip(), fmt)
                        return parsed_date.strftime('%d-%b-%Y')
                    except ValueError:
                        continue
                # 如果上述格式都不匹配，可能包含时间信息，尝试去除时间部分
                date_part = date_value.split()[0]  # 取日期部分
                for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%m-%d-%Y', '%d.%m.%Y', '%Y.%m.%d'):
                    try:
                        parsed_date = datetime.strptime(date_part, fmt)
                        return parsed_date.strftime('%d-%b-%Y')
                    except ValueError:
                        continue
            return str(date_value).strip() if str(date_value).strip() else date_value
        except Exception as e:
            logger.error(f"Date formatting error: {e}")
            return str(date_value).strip() if str(date_value).strip() else date_value

    def _find_matching_row_in_excel(self, df, equipment_id):
        """在Excel数据中查找匹配的设备ID行"""
        # logger.debug(f"Searching for equipment ID: {equipment_id}")
        # print(f"DEBUG: Searching for equipment ID: {equipment_id}")
        # 创建正则表达式模式，匹配Q-XXXX或L-XXXX格式
        pattern = r'(Q-\\d{4}|L-\\d{4})'
        
        for index, row in enumerate(df):
            excel_value = str(row[3]).strip()  # D列为索引3
            equipment_id_clean = equipment_id.replace('\\r\\n', '').replace('\\n', '').strip()
            
            # print(f"DEBUG: Comparing - Row {index}: equipment_id_clean='{equipment_id_clean}', excel_value='{excel_value}', lower_match={equipment_id_clean.lower() == excel_value.lower()}, pattern_match={bool(re.search(pattern, equipment_id_clean, re.IGNORECASE))}")
            
            # 完全匹配或部分匹配
            if equipment_id_clean.lower() == excel_value.lower():
                # print(f"DEBUG: Exact match found for {equipment_id} at row {index}")
                # logger.debug(f"Exact match found for {equipment_id} at row {index}")
                return index
            elif re.search(pattern, equipment_id_clean, re.IGNORECASE) and equipment_id_clean.lower() in excel_value.lower():
                print(f"DEBUG: Pattern match found for {equipment_id} at row {index}")
                logger.debug(f"Pattern match found for {equipment_id} at row {index}")
                return index
        
        print(f"DEBUG: No match found for equipment ID: {equipment_id}")
        logger.debug(f"No match found for equipment ID: {equipment_id}")
        return None

    def _update_equipment_list_in_word_with_excel_source(self, report_path: str, equipment_data: List[Dict[str, Any]] = None) -> bool:
        """
        从Excel源获取数据并更新Word文档中的设备列表
        """
        try:
            logger.info(f"Updating equipment list in Word document with Excel source: {report_path}")

            # 从配置中获取Excel文件路径
            excel_file_path = self.config["equipment_data_sources"]["excel_file_path"]
            
            # 根据项目状态动态确定源文档路径
            if hasattr(self.config_manager, 'project_path') and self.config_manager.project_path:
                # 如果有项目打开，使用项目目录下的EquipmentID.docx
                source_doc_path = os.path.join(self.config_manager.project_path, "EquipmentID.docx")
            else:
                # 如果没有项目打开，使用默认路径
                source_doc_path = self.config["equipment_data_sources"]["source_doc_path"]
            # section_keyword 不再使用，直接使用 "EQUIPMENTS" 进行匹配

            # 确保路径使用正确的反斜杠格式
            excel_file_path = os.path.normpath(excel_file_path)
            source_doc_path = os.path.normpath(source_doc_path)
            
            logger.debug(f"Using Excel file: {excel_file_path}")
            logger.debug(f"Using source document: {source_doc_path}")
            logger.debug("Looking for section keyword: EQUIPMENTS")

            # 检查必要的源文件是否存在
            if not os.path.exists(excel_file_path):
                logger.error(f"Excel file does not exist: {excel_file_path}")
                # 提供详细的错误信息，包括配置来源
                import sys
                config_source = "生产环境配置(D:\\TestFlowManager\\config\\paths.ini)" if getattr(sys, 'frozen', False) else "开发环境配置(src/app/config/paths.ini)"
                error_details = [
                    f"配置来源: {config_source}",
                    f"Excel文件路径: {excel_file_path}",
                    f"当前工作目录: {os.getcwd()}"
                ]
                
                from PyQt5.QtWidgets import QMessageBox
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("Excel文件未找到")
                msg_box.setText("无法找到设备数据源Excel文件")
                msg_box.setInformativeText("\n".join(error_details))
                msg_box.setDetailedText(
                    f"详细信息:\n"
                    f"- 配置文件路径: {self._get_actual_config_path()}\n"
                    f"- Excel文件路径: {excel_file_path}\n"
                    f"- 文件是否存在: {os.path.exists(excel_file_path)}\n"
                    f"- 当前运行模式: {'可执行文件模式' if getattr(sys, 'frozen', False) else '开发模式'}"
                )
                msg_box.exec_()
                return False
            
            if not os.path.exists(source_doc_path):
                logger.error(f"Source document does not exist: {source_doc_path}")
                # 检查是否在项目目录下查找，以确定错误信息的类型
                project_dir = os.path.dirname(source_doc_path)
                if hasattr(self.config_manager, 'project_path') and self.config_manager.project_path and project_dir == self.config_manager.project_path:
                    # 在项目目录下查找但未找到，显示项目相关错误信息
                    error_message = "项目文件夹下没有找到EquipmentID.docx"
                else:
                    # 在默认路径下查找但未找到，显示默认路径错误信息
                    error_message = "默认路径下没有找到EquipmentID.docx"
                
                # 提供详细的错误信息
                import sys
                config_source = "生产环境配置(D:\\TestFlowManager\\config\\paths.ini)" if getattr(sys, 'frozen', False) else "开发环境配置(src/app/config/paths.ini)"
                error_details = [
                    f"错误类型: {error_message}",
                    f"配置来源: {config_source}",
                    f"查找路径: {source_doc_path}",
                    f"项目路径: {getattr(self.config_manager, 'project_path', '无')}",
                    f"当前工作目录: {os.getcwd()}"
                ]
                
                # 弹出提醒信息，根据项目状态显示不同的错误信息。然后退出。
                from PyQt5.QtWidgets import QMessageBox
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("文件未找到")
                msg_box.setText(error_message)
                msg_box.setInformativeText("\n".join(error_details))
                msg_box.setDetailedText(
                    f"详细调试信息:\n"
                    f"- 配置文件实际路径: {self._get_actual_config_path()}\n"
                    f"- 源文档路径: {source_doc_path}\n"
                    f"- 文件是否存在: {os.path.exists(source_doc_path)}\n"
                    f"- 项目路径设置: {getattr(self.config_manager, 'project_path', '未设置')}\n"
                    f"- 运行模式: {'可执行文件模式' if getattr(sys, 'frozen', False) else '开发模式'}"
                )
                msg_box.exec_()
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
            print(f"DEBUG: About to call _find_equipment_table_win32com with keyword 'EQUIPMENTS'")
            target_table = self._find_equipment_table_win32com(word_doc, "EQUIPMENTS")

            if target_table is None:
                logger.warning(f"Could not find 'EQUIPMENTS' section or table!")
                print(f"DEBUG: Could not find table with keyword 'EQUIPMENTS'")
                word_doc.Close()
                word_app.Quit()
                return False
            else:
                logger.info("Successfully found equipment table using win32com")
                print(f"DEBUG: Successfully found equipment table with {target_table.Rows.Count} rows")
                logger.info(f"Table has {target_table.Rows.Count} rows initially")

            # 从Excel中读取设备列表
            logger.info(f"Reading Excel file: {excel_file_path}")
            
            file_extension = os.path.splitext(excel_file_path)[1].lower()
            
            # 使用win32com直接读取Excel文件，避免pandas初始化问题
            try:
                import win32com.client as win32_excel
                # 启动Excel应用程序
                excel_app = win32_excel.Dispatch('Excel.Application')
                excel_app.Visible = False  # 不显示Excel界面
                excel_app.DisplayAlerts = False  # 关闭警告提示
                
                # 以只读模式打开工作簿，避免密码保护问题
                workbook = excel_app.Workbooks.Open(excel_file_path, UpdateLinks=0, ReadOnly=True)
                worksheet = workbook.Sheets('All Equip.')
                
                # 获取数据范围
                used_range = worksheet.UsedRange
                rows = used_range.Rows.Count
                cols = used_range.Columns.Count
                
                # 读取数据到列表
                excel_data = []
                for row in range(1, rows + 1):
                    row_data = []
                    for col in range(1, cols + 1):
                        try:
                            cell_value = worksheet.Cells(row, col).Value
                            # 处理None值
                            if cell_value is None:
                                cell_value = ""
                            row_data.append(str(cell_value) if cell_value is not None else "")
                        except:
                            row_data.append("")
                    excel_data.append(row_data)
                
                # 关闭工作簿和Excel应用程序
                workbook.Close(SaveChanges=False)  # 确保不保存更改
                excel_app.Quit()
                
                logger.info(f"Successfully loaded Excel data with {len(excel_data)} rows and {len(excel_data[0]) if len(excel_data) > 0 else 0} columns using win32com")
                
            except Exception as e:
                logger.error(f"Error reading Excel file with win32com: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                
                # 如果win32com方法失败，尝试使用openpyxl作为备选方案（仅对xlsx文件）
                if file_extension == '.xlsx':
                    try:
                        logger.info("Trying fallback method using openpyxl...")
                        from openpyxl import load_workbook
                        # 以只读模式打开，避免密码问题
                        workbook = load_workbook(excel_file_path, read_only=True)
                        sheet = workbook['All Equip.']
                        
                        excel_data = []
                        for row in sheet.iter_rows(values_only=True):
                            processed_row = []
                            for cell in row:
                                if cell is None:
                                    processed_row.append("")
                                else:
                                    processed_row.append(str(cell))
                            excel_data.append(processed_row)
                        logger.info("Successfully loaded Excel data using openpyxl fallback method")
                    except Exception as fallback_error:
                        logger.error(f"Fallback method also failed: {fallback_error}")
                        return False
                else:
                    # 对于.xls文件，如果我们不能使用win32com，也没有其他好方法
                    logger.error(f"Cannot read {file_extension} file without win32com or pandas")
                    return False
            
            # 转换为类似DataFrame的结构（列表的列表）
            excel_df = excel_data
            logger.info(f"Loaded Excel data with {len(excel_df)} rows and {len(excel_df[0]) if len(excel_df) > 0 else 0} columns")

            # 从源文档中提取设备ID
            logger.info("Extracting equipment IDs from source document...")
            print(f"DEBUG: Extracting equipment IDs from source document: {source_doc_path}")
            equipment_ids = self._extract_equipment_ids_from_doc(source_doc_path)
            logger.info(f"Found {len(equipment_ids)} unique equipment IDs")
            print(f"DEBUG: Found {len(equipment_ids)} unique equipment IDs: {equipment_ids}")
            if equipment_ids:
                logger.debug(f"Equipment IDs: {equipment_ids[:5]}...")  # 只显示前5个

            if not equipment_ids:
                logger.warning("No equipment IDs found in source document!")
                word_doc.Close()
                word_app.Quit()
                return False

            # 将设备ID填入表格（第三列，即ID Number列）
            logger.info("Filling table with equipment IDs from source document...")
            row_start = 2  # 从第二行开始（win32com索引从1开始，所以第二行是索引2）

            for i, equipment_id in enumerate(equipment_ids):
                # 如果表格行数不够，添加新行
                if row_start + i > target_table.Rows.Count:
                    target_table.Rows.Add()
                    logger.debug(f"Added new row {target_table.Rows.Count} to accommodate equipment ID")

                # 将设备ID写入表格单元格（第3列，win32com索引从1开始，所以第3列是索引3）
                # 保留原始格式，只替换文本内容
                target_table.Cell(row_start + i, 3).Range.Text = equipment_id.replace('\\r\\n', '').replace('\\n', '').strip()
                # print(f"DEBUG: Filled equipment ID '{equipment_id}' in row {row_start + i}, column 3")
                # logger.debug(f"Filled equipment ID '{equipment_id}' in row {row_start + i}, column 3")

            # 从Excel获取数据并填充表格其他列
            print(f"\n🔄 Step 6: Filling table with equipment data from Excel...")
            col_map = self.config["equipment_table_settings"]["target_columns_mapping"]
            for row_idx in range(row_start, target_table.Rows.Count + 1):  # 从第二行开始
                # 获取第三列的设备ID（ID Number列）
                equipment_id = target_table.Cell(row_idx, 3).Range.Text.rstrip('\x07\x0B')  # 移除特殊字符
                equipment_id = equipment_id.rstrip('\r\x07').strip()  # 清理文本
                
                # if equipment_id == "":
                #     print(f"Row {row_idx}: Empty equipment ID, skipping")
                #     logger.debug(f"Row {row_idx}: Empty equipment ID, skipping")
                #     continue
                    
                # print(f"Processing row {row_idx} with equipment ID: {equipment_id}")
                # logger.debug(f"Processing row {row_idx} with equipment ID: {equipment_id}")
                
                # 在Excel中查找匹配的设备ID
                matched_row_idx = self._find_matching_row_in_excel(excel_df, equipment_id)
                
                if matched_row_idx is not None:
                    try:
                        # 填充设备信息，保留原始格式
                        # A列 -> Item列 (索引0) - win32com第一列是索引1
                        item_value = str(excel_df[matched_row_idx][0]).strip()
                        if item_value and item_value != "nan":
                            target_table.Cell(row_idx, col_map["item_col"]).Range.Text = item_value
                            # print(f"  Filled Item: {item_value}")
                            # logger.debug(f"  Filled Item: {item_value}")
                        
                        # C列 -> Manufacturer列 (索引2) - win32com第三列是索引3
                        manufacturer_value = str(excel_df[matched_row_idx][2]).strip()
                        if manufacturer_value and manufacturer_value != "nan":
                            target_table.Cell(row_idx, col_map["manufacturer_col"]).Range.Text = manufacturer_value
                            # print(f"  Filled Manufacturer: {manufacturer_value}")
                            # logger.debug(f"  Filled Manufacturer: {manufacturer_value}")
                        
                        # D列 -> ID Number列 (索引3) - 已经是设备ID，保持不变
                        
                        # E列 -> Last Cal.列 (索引4) - win32com第五列是索引5
                        last_cal_value = str(excel_df[matched_row_idx][4]).strip()
                        if last_cal_value and last_cal_value != "nan":
                            formatted_date = self._format_date(last_cal_value)
                            target_table.Cell(row_idx, col_map["last_cal_col"]).Range.Text = formatted_date
                            # print(f"  Filled Last Cal.: {formatted_date}")
                            # logger.debug(f"  Filled Last Cal.: {formatted_date}")
                        
                        # F列 -> Cal. Due列 (索引5) - win32com第六列是索引6
                        cal_due_value = str(excel_df[matched_row_idx][5]).strip()
                        if cal_due_value and cal_due_value != "nan":
                            formatted_due_date = self._format_date(cal_due_value)
                            target_table.Cell(row_idx, col_map["cal_due_col"]).Range.Text = formatted_due_date
                            # print(f"  Filled Cal. Due: {formatted_date}")
                            # logger.debug(f"  Filled Cal. Due: {formatted_date}")
                            
                    except IndexError as e:
                        print(f"Error accessing Excel data for row {matched_row_idx}: {e}")
                        logger.error(f"Error accessing Excel data for row {matched_row_idx}: {e}")
                else:
                    # 未找到匹配项，在Item列中标记
                    target_table.Cell(row_idx, col_map["item_col"]).Range.Text = "Not Found"
                    print(f"  ❌ No match found for equipment ID: {equipment_id}")
                    logger.warning(f"  No match found for equipment ID: {equipment_id}")

            # 为新增的行添加边框
            logger.info("Adding borders to new table rows...")
            for row_idx in range(row_start, target_table.Rows.Count + 1):  # 从第二行开始
                for col_idx in range(1, target_table.Columns.Count + 1):  # 遍历所有列
                    cell = target_table.Cell(row_idx, col_idx)
                    # 设置所有四个边框
                    cell.Borders(1).Visible = True  # wdBorderLeft
                    cell.Borders(2).Visible = True  # wdBorderRight
                    cell.Borders(3).Visible = True  # wdBorderTop
                    cell.Borders(4).Visible = True  # wdBorderBottom
            logger.info(f"Borders added to {target_table.Rows.Count - row_start + 1} new rows")

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
    
    def _update_equipment_list_in_word(self, report_path: str, equipment_data: List[Dict[str, Any]]) -> bool:
        """
        在Word文档中更新设备列表

        Args:
            report_path: Word文档路径
            equipment_data: 设备数据列表

        Returns:
            更新是否成功
        """
        try:
            logger.info(f"Updating equipment list in Word document: {report_path}")
            
            # 这里会实现Word文档的设备列表更新逻辑
            # 由于这是示例，我们暂时只记录日志
            from src.utils.word_utils import open_docx_document, save_document
            import pythoncom
            
            # 初始化COM库
            pythoncom.CoInitialize()
            
            try:
                # 打开文档
                doc = open_docx_document(report_path)
                
                if doc is None:
                    logger.error(f"Failed to open document: {report_path}")
                    return False
                
                # 在这里实现具体的设备列表更新逻辑
                # 搜索文档中包含特定标记的表格或段落，并更新其内容
                updated_count = 0
                
                # 示例：更新文档中的设备列表（需要根据实际文档结构来实现）
                for para in doc.Paragraphs:
                    if "Equipment List" in para.Range.Text or "设备列表" in para.Range.Text:
                        # 找到设备列表标题，接下来的部分可能是设备列表
                        logger.info(f"Found equipment list marker in paragraph: {para.Range.Text}")
                
                # 示例：在文档中查找特定的表格并更新
                for table in doc.Tables:
                    # 检查表格是否包含设备相关信息
                    if table.Cell(1, 1).Range.Text.strip() in ['Equipment', '设备', '设备列表']:
                        logger.info("Found equipment table, updating...")
                        # 更新表格内容
                        self._update_equipment_table(table, equipment_data)
                        updated_count += 1
                
                # 保存文档
                save_document(doc, report_path)
                logger.info(f"Successfully updated {updated_count} equipment tables in {report_path}")
                
                return True
            finally:
                # 释放COM资源
                pythoncom.CoUninitialize()
                
        except Exception as e:
            logger.error(f"Error updating equipment list in Word document {report_path}: {e}")
            import pythoncom
            try:
                pythoncom.CoUninitialize()
            except:
                pass
            return False
    
    def _update_equipment_list_in_excel(self, report_path: str, equipment_data: List[Dict[str, Any]]) -> bool:
        """
        在Excel文档中更新设备列表

        Args:
            report_path: Excel文档路径
            equipment_data: 设备数据列表

        Returns:
            更新是否成功
        """
        try:
            logger.info(f"Updating equipment list in Excel document: {report_path}")
            
            # 这里会实现Excel文档的设备列表更新逻辑
            from src.utils.excel_utils import open_excel_application
            import pythoncom
            
            # 初始化COM库
            pythoncom.CoInitialize()
            
            try:
                # 打开Excel应用程序
                excel_app = open_excel_application()
                
                if excel_app is None:
                    logger.error(f"Failed to open Excel application for: {report_path}")
                    return False
                
                # 打开工作簿
                workbook = excel_app.Workbooks.Open(report_path)
                
                # 查找包含设备列表的工作表
                for worksheet in workbook.Worksheets:
                    # 检查工作表名称或内容是否包含设备相关信息
                    if "Equipment" in worksheet.Name or "设备" in worksheet.Name:
                        logger.info(f"Found equipment worksheet: {worksheet.Name}")
                        # 更新工作表中的设备列表
                        self._update_equipment_worksheet(worksheet, equipment_data)
                
                # 保存并关闭
                workbook.Save()
                workbook.Close()
                logger.info(f"Successfully updated equipment list in Excel: {report_path}")
                
                return True
            finally:
                # 释放COM资源
                pythoncom.CoUninitialize()
                
        except Exception as e:
            logger.error(f"Error updating equipment list in Excel document {report_path}: {e}")
            import pythoncom
            try:
                pythoncom.CoUninitialize()
            except:
                pass
            return False
    
    def _update_equipment_table(self, table, equipment_data: List[Dict[str, Any]]) -> None:
        """
        更新Word文档中的设备表格

        Args:
            table: Word表格对象
            equipment_data: 设备数据列表
        """
        try:
            # 添加表头（如果表格为空或需要更新表头）
            if table.Rows.Count == 1:  # 只有一行，可能是空表
                # 插入表头
                headers = ["ID", "设备名称", "状态", "备注"]
                for col_idx, header in enumerate(headers, 1):
                    if col_idx <= table.Columns.Count:
                        table.Cell(1, col_idx).Range.Text = header
                    else:
                        # 如果列数不够，添加新列
                        table.Columns.Add()
                        table.Cell(1, col_idx).Range.Text = header
                
                # 添加数据行
                for idx, equip in enumerate(equipment_data, 2):
                    # 确保表格有足够的行
                    if idx > table.Rows.Count:
                        table.Rows.Add()
                    
                    # 填充数据
                    table.Cell(idx, 1).Range.Text = str(equip.get("id", ""))
                    table.Cell(idx, 2).Range.Text = str(equip.get("name", ""))
                    table.Cell(idx, 3).Range.Text = str(equip.get("status", ""))
                    table.Cell(idx, 4).Range.Text = str(equip.get("notes", ""))
            
            else:
                # 表格已有内容，查找设备列表部分并更新
                # 这里需要根据实际文档结构来实现
                for idx, equip in enumerate(equipment_data, 2):
                    # 确保表格有足够的行
                    if idx > table.Rows.Count:
                        table.Rows.Add()
                    
                    # 填充数据
                    if table.Columns.Count >= 4:
                        table.Cell(idx, 1).Range.Text = str(equip.get("id", ""))
                        table.Cell(idx, 2).Range.Text = str(equip.get("name", ""))
                        table.Cell(idx, 3).Range.Text = str(equip.get("status", ""))
                        table.Cell(idx, 4).Range.Text = str(equip.get("notes", ""))
        
        except Exception as e:
            logger.error(f"Error updating equipment table: {e}")
    
    def _update_equipment_worksheet(self, worksheet, equipment_data: List[Dict[str, Any]]) -> None:
        """
        更新Excel工作表中的设备列表

        Args:
            worksheet: Excel工作表对象
            equipment_data: 设备数据列表
        """
        try:
            # 清空现有数据（保留表头）
            # 假设设备列表从第2行开始（第1行为表头）
            # 删除现有数据行
            max_rows = 100  # 假设最多100行数据
            for row in range(3, max_rows + 1):  # 从第3行开始清除数据
                for col in range(1, 5):  # 假设有4列
                    try:
                        cell = worksheet.Cells(row, col)
                        if cell.Value is not None and str(cell.Value).strip() != "":
                            cell.Value = ""
                    except:
                        break  # 如果到达空行，停止清除
            
            # 添加新的设备数据
            headers = ["ID", "设备名称", "状态", "备注"]
            for col_idx, header in enumerate(headers, 1):
                worksheet.Cells(1, col_idx).Value = header
            
            for idx, equip in enumerate(equipment_data, 2):
                worksheet.Cells(idx, 1).Value = equip.get("id", "")
                worksheet.Cells(idx, 2).Value = equip.get("name", "")
                worksheet.Cells(idx, 3).Value = equip.get("status", "")
                worksheet.Cells(idx, 4).Value = equip.get("notes", "")
        
        except Exception as e:
            logger.error(f"Error updating equipment worksheet: {e}")
    
    def scan_for_equipment_tables(self, report_path: str) -> List[Dict[str, Any]]:
        """
        扫描报告中可能包含设备列表的表格或区域

        Args:
            report_path: 报告文件路径

        Returns:
            找到的设备表信息列表
        """
        try:
            logger.info(f"Scanning for equipment tables in: {report_path}")
            
            file_extension = os.path.splitext(report_path)[1].lower()
            equipment_tables = []
            
            if file_extension in ['.docx', '.doc']:
                from src.utils.word_utils import open_docx_document
                import pythoncom
                
                pythoncom.CoInitialize()
                
                try:
                    doc = open_docx_document(report_path)
                    if doc is None:
                        return equipment_tables
                    
                    # 搜索包含设备相关关键词的表格
                    for i, table in enumerate(doc.Tables):
                        table_info = {
                            "index": i,
                            "type": "table",
                            "position": i,
                            "headers": [],
                            "potential_equipment": False
                        }
                        
                        # 检查表头是否包含设备相关关键词
                        if table.Rows.Count > 0 and table.Columns.Count > 0:
                            first_cell_text = table.Cell(1, 1).Range.Text.strip()
                            if any(keyword in first_cell_text for keyword in 
                                   ['Equipment', '设备', '设备列表', 'Equipment List']):
                                table_info["potential_equipment"] = True
                                table_info["headers"] = [table.Cell(1, j).Range.Text.strip() 
                                                         for j in range(1, min(table.Columns.Count + 1, 6))]
                        
                        equipment_tables.append(table_info)
                
                finally:
                    pythoncom.CoUninitialize()
            
            return equipment_tables
            
        except Exception as e:
            logger.error(f"Error scanning for equipment tables in {report_path}: {e}")
            return []
    
    def _get_actual_config_path(self) -> str:
        """获取实际使用的配置文件路径"""
        try:
            from src.core.config_manager import config_manager
            # 通过反射获取实际的配置文件路径
            import sys
            if getattr(sys, 'frozen', False):
                # 可执行文件模式
                production_path = os.path.join("D:", "TestFlowManager", "config", "paths.ini")
                if os.path.exists(production_path):
                    return production_path
                else:
                    executable_dir = os.path.dirname(sys.executable)
                    return os.path.join(executable_dir, "config", "paths.ini")
            else:
                # 开发模式
                return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "config", "paths.ini")
        except Exception as e:
            return f"无法确定配置路径: {e}"
    
    def get_report_metadata(self, report_path: str) -> Dict[str, Any]:
        """
        获取报告元数据

        Args:
            report_path: 报告文件路径

        Returns:
            报告元数据字典
        """
        try:
            metadata = {
                "file_path": report_path,
                "file_name": os.path.basename(report_path),
                "file_size": os.path.getsize(report_path),
                "modified_time": datetime.fromtimestamp(os.path.getmtime(report_path)).isoformat(),
                "extension": os.path.splitext(report_path)[1],
                "equipment_tables_found": 0
            }
            
            # 扫描设备表
            equipment_tables = self.scan_for_equipment_tables(report_path)
            metadata["equipment_tables_found"] = len(equipment_tables)
            metadata["equipment_tables"] = equipment_tables
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting report metadata for {report_path}: {e}")
            return {"error": str(e)}
