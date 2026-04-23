"""
测试样品信息表格填充服务模块
提供填充Word文档中第一个表格（测试样品信息）的业务逻辑服务
"""

from typing import Dict, Any, List, Optional
from src.core.logger import logger
from src.infrastructure.office.facade import OfficeFacade


class TestSampleInfoService:
    """
    测试样品信息表格填充服务类
    提供填充Word文档中第一个表格（测试样品信息）的业务逻辑服务
    表格有7列，对应JSON中的测试样品信息7列内容
    """

    def __init__(self):
        """初始化测试样品信息表格填充服务"""
        pass

    def fill_test_sample_info_table(
        self,
        document_path: str,
        sample_data: List[Dict[str, Any]],
        word_app_instance=None,
        word_doc_instance=None
    ) -> bool:
        """
        填充Word文档中第一个表格的测试样品信息
        
        Args:
            document_path: Word文档路径
            sample_data: 测试样品信息数据列表
            word_app_instance: Word应用程序实例，如果为None则创建新的实例
            word_doc_instance: Word文档实例，如果提供则直接使用该实例，否则根据document_path打开文档
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"开始填充测试样品信息表格，文档路径: {document_path}, 数据条数: {len(sample_data)}")
        
        word_app = None
        word_doc = None
        
        # 通过 OfficeFacade 创建 Word session（仅在自己创建时才需要）
        office_facade = None
        word_session = None
        handle = None
        owns_word_doc = False
        
        try:
            # 如果提供了文档实例，则直接使用
            if word_doc_instance is not None:
                word_doc = word_doc_instance
                word_app = word_doc.Application  # 从文档实例获取应用程序
                logger.info("使用传入的Word文档实例")
            else:
                # 如果word_app_instance存在，直接使用，否则创建新的实例
                if word_app_instance is None:
                    logger.info("创建新的Word应用程序实例")
                    # 通过 OfficeFacade 创建 Word session
                    office_facade = OfficeFacade()
                    word_session = office_facade.create_session("word")
                    handle = word_session.acquire()
                    
                    word_app = handle.application
                    if word_app is None:
                        logger.error("无法从 OfficeFacade session 获取 Word 应用程序实例")
                        return False
                    
                    word_app.Visible = False  # 确保Word应用程序不可见
                    word_app.DisplayAlerts = False  # 关闭警告提示
                else:
                    word_app = word_app_instance
                    logger.info("使用传入的Word应用程序实例")
                
                # 打开文档
                word_doc = word_app.Documents.Open(document_path)
                owns_word_doc = True
                logger.info(f"成功打开文档，包含 {word_doc.Paragraphs.Count} 个段落和 {word_doc.Tables.Count} 个表格")
            
            # 检查文档中是否有表格
            if word_doc.Tables.Count == 0:
                logger.error("文档中未找到任何表格")
                return False
            
            # 获取第一个表格
            target_table = word_doc.Tables(1)
            logger.info(f"找到第一个表格，当前行数: {target_table.Rows.Count}, 列数: {target_table.Columns.Count}")
            
            # 确保表格有7列
            current_cols = target_table.Columns.Count
            if current_cols < 7:
                # 添加缺失的列
                cols_to_add = 7 - current_cols
                for _ in range(cols_to_add):
                    target_table.Columns.Add()
                logger.info(f"添加了 {cols_to_add} 列，现在共有 {target_table.Columns.Count} 列")
            elif current_cols > 7:
                # 删除多余的列
                cols_to_delete = current_cols - 7
                for _ in range(cols_to_delete):
                    if target_table.Columns.Count > 7:
                        target_table.Columns(target_table.Columns.Count).Delete()
                logger.info(f"删除了 {cols_to_delete} 列，现在共有 {target_table.Columns.Count} 列")
            
            # 确保表格有足够行数（标题行 + 数据行）
            required_rows = len(sample_data) + 1  # +1 为标题行
            current_rows = target_table.Rows.Count
            
            if required_rows > current_rows:
                # 添加新行
                rows_to_add = required_rows - current_rows
                for _ in range(rows_to_add):
                    target_table.Rows.Add()
                logger.info(f"添加了 {rows_to_add} 行，现在共有 {target_table.Rows.Count} 行")
            elif required_rows < current_rows:
                # 删除多余的行（保留标题行和数据行）
                rows_to_delete = current_rows - required_rows
                for _ in range(rows_to_delete):
                    if target_table.Rows.Count > required_rows:
                        target_table.Rows(target_table.Rows.Count).Delete()
                logger.info(f"删除了 {rows_to_delete} 行，现在共有 {target_table.Rows.Count} 行")
            
            # 填充标题行（第1行）
            self._fill_header_row(target_table.Rows(1))
            
            # 填充数据行（从第2行开始）
            for i, sample_row in enumerate(sample_data):
                row_index = i + 2  # 从第2行开始（标题行为第1行）
                self._fill_data_row(target_table.Rows(row_index), sample_row)
            
            logger.info("测试样品信息表格填充完成")
            
            # 应用表格格式
            from .utils.table_handler import TableHandler
            TableHandler.apply_table_formatting(target_table)
            
            # 不在这里保存文档，由调用者负责保存
            return True
            
        except Exception as e:
            logger.error(f"填充测试样品信息表格时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return False
        finally:
            try:
                if owns_word_doc and word_doc is not None:
                    word_doc.Close(SaveChanges=False)
            except Exception as e:
                logger.error(f"关闭测试样品信息文档时出错: {e}")

            # 仅在我们创建了 session 的情况下才释放
            try:
                if word_session is not None:
                    word_session.release()
            except Exception as e:
                logger.error(f"释放 Word session 时出错: {e}")

    def _fill_header_row(self, header_row):
        """
        填充标题行
        
        Args:
            header_row: 表格标题行对象
        """
        logger.info("填充标题行")
        
        # 定义标题内容（7列）
        headers = [
            "Product Name",      # 产品名称
            "Part Number",       # 料号
            "Lot Info",          # 批次
            "Base Material",     # 基材
            "Contact Plating",   # 接触镀层
            "Contact Lubricant", # 润滑油
            "Housing Material"   # 塑材
        ]
        
        # 填充每个标题单元格
        for i, header_text in enumerate(headers):
            col_index = i + 1  # Win32COM索引从1开始
            try:
                cell = header_row.Cells(col_index)
                cell.Range.Text = str(header_text).rstrip('\x07')  # 移除段落标记
                logger.debug(f"标题行第{col_index}列填充: {header_text}")
            except Exception as e:
                logger.warning(f"填充标题行第{col_index}列时出错: {e}")

    def _fill_data_row(self, data_row, sample_data: Dict[str, Any]):
        """
        填充数据行
        
        Args:
            data_row: 表格数据行对象
            sample_data: 测试样品信息数据字典
        """
        logger.info(f"填充数据行: {sample_data}")
        
        # 定义数据字段映射（按列顺序）
        field_mapping = [
            "product_name",        # 第1列：产品名称
            "part_number",         # 第2列：料号
            "lot_info",            # 第3列：批次
            "base_material",       # 第4列：基材
            "contact_plating",     # 第5列：接触镀层
            "contact_lubricant",   # 第6列：润滑油
            "housing_material"     # 第7列：塑材
        ]
        
        # 填充每个数据单元格
        for i, field_name in enumerate(field_mapping):
            col_index = i + 1  # Win32COM索引从1开始
            try:
                cell = data_row.Cells(col_index)
                value = sample_data.get(field_name, "")
                if value:
                    cell.Range.Text = str(value).rstrip('\x07')  # 移除段落标记
                    logger.debug(f"数据行第{col_index}列填充: {value}")
                else:
                    cell.Range.Text = "".rstrip('\x07')  # 清空单元格
            except Exception as e:
                logger.warning(f"填充数据行第{col_index}列时出错: {e}")
