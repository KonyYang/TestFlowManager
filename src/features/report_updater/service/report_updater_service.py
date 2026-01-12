"""
报告更新模块服务层
处理报告更新的具体业务逻辑
"""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.core.logger import logger


class ReportUpdaterService:
    """报告更新服务类"""
    
    def __init__(self):
        """初始化报告更新服务"""
        logger.info("ReportUpdaterService initialized")
    
    def update_equipment_list(self, report_path: str, equipment_data: List[Dict[str, Any]]) -> bool:
        """
        更新报告中的设备列表

        Args:
            report_path: 报告文件路径
            equipment_data: 设备数据列表

        Returns:
            更新是否成功
        """
        try:
            logger.info(f"Starting equipment list update for report: {report_path}")
            logger.info(f"Equipment data size: {len(equipment_data)}")
            
            # 根据文件类型选择相应的处理方式
            file_extension = os.path.splitext(report_path)[1].lower()
            
            if file_extension in ['.docx', '.doc']:
                return self._update_equipment_list_in_word(report_path, equipment_data)
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