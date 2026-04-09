"""
Test Spec Tables服务模块
提供填充Test Description、Test Method和Test Result表格的业务逻辑服务
"""

from typing import Dict, Any, Callable, Optional
from src.core.logger import logger
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from src.features.report_wizard.service.test_result_service import TestResultService
from .utils.sample_data_extractor import SampleDataExtractor
from .test_sample_info_service import TestSampleInfoService


class TestSpecTablesService:
    """
    Test Spec Tables服务类
    提供填充Test Description、Test Method和Test Result表格的业务逻辑服务
    """

    def __init__(self):
        """初始化Test Spec Tables服务"""
        self.test_result_service = TestResultService()
        self.test_sample_info_service = TestSampleInfoService()
        pass
    
    def _safe_callback_call(self, callback, *args):
        """
        安全调用回调函数或Qt信号
        
        Args:
            callback: 回调函数或Qt信号
            *args: 传递给回调的参数
            
        Returns:
            调用结果，如果调用失败则返回None
        """
        if callback is None:
            return None
            
        try:
            # 检查是否是Qt信号
            # Qt信号对象通常有emit方法
            if hasattr(callback, 'emit'):
                # 这是一个Qt信号，使用emit方法调用
                return callback.emit(*args)
            else:
                # 这是一个普通函数，直接调用
                return callback(*args)
        except Exception as e:
            logger.error(f"回调调用失败: {e}")
            return None

    def fill_all_test_spec_tables(
        self, 
        document_path: str, 
        matrix_data_structure: MatrixDataStructure,
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        填充Test Description、Test Method和Test Result表格
        
        Args:
            document_path: Word文档路径
            matrix_data_structure: Matrix数据结构
            progress_callback: 进度回调函数
            status_callback: 状态回调函数
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"开始填充Test Description、Test Method和Test Result表格，文档路径: {document_path}")
        word_app = None
        word_doc = None
        try:
            if status_callback:
                self._safe_callback_call(status_callback, "正在打开文档...")
            
            # 检查文档是否存在
            import os
            if not os.path.exists(document_path):
                logger.error(f"文档不存在: {document_path}")
                if status_callback:
                    self._safe_callback_call(status_callback, f"错误: 文档不存在 - {document_path}")
                return False
            
            # 使用win32com打开Word文档
            import win32com.client
            word_app = win32com.client.Dispatch("Word.Application")
            word_app.Visible = False  # 隐藏Word窗口
            word_app.DisplayAlerts = False  # 关闭警告提示
            
            word_doc = word_app.Documents.Open(document_path)
            logger.info(f"成功打开文档，包含 {word_doc.Paragraphs.Count} 个段落和 {word_doc.Tables.Count} 个表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 10)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在查找TEST DESCRIPTION段落...")
            
            # 使用win32com方式查找并填充Test Description表格
            # 通过查找TEST DESCRIPTION表格并填充
            from .utils.table_handler import TableHandler
            description_table = TableHandler.find_table_by_paragraph_win32com(word_doc, "TEST DESCRIPTION")
            if description_table:
                logger.info("找到TEST DESCRIPTION表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "正在填充Test Description表格...")
                
                # 将查找到的表格对象直接传递给_fill_description_table_win32com方法，避免重复查找
                self._fill_description_table_win32com(description_table, document_path, word_app)
            else:
                logger.warning("未找到TEST DESCRIPTION表格")
                if status_callback:
                    status_callback("警告: 未找到TEST DESCRIPTION表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 60)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在查找TEST METHODS/REQUIREMENTS段落...")
            
            # 查找并填充Test Method表格
            from .utils.table_handler import TableHandler
            method_table = TableHandler.find_table_by_paragraph_win32com(word_doc, "TEST METHODS/REQUIREMENTS")
            if method_table:
                logger.info("找到TEST METHODS/REQUIREMENTS表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "正在填充Test Method表格...")
                
                # 使用win32com填充Test Method表格
                self._fill_method_table_win32com(method_table, document_path, word_app)
            else:
                logger.warning("未找到TEST METHODS/REQUIREMENTS表格")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: 未找到TEST METHODS/REQUIREMENTS表格")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 90)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在保存文档...")
            
            # 注意：暂不保存文档，等待后续Test Result处理完成后统一保存
            # word_doc.Save()
            logger.info(f"Test Description和Test Method表格填充完成，等待Test Result处理完成")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 100)
            
            if status_callback:
                self._safe_callback_call(status_callback, "处理完成！表格已成功填充。")
            
            logger.info(f"Test Description、Test Method和Test Result表格填充完成")
            
            # 现在使用相同的matrix_data_structure生成Test Result表格
            if status_callback:
                self._safe_callback_call(status_callback, "正在生成Test Result表格...")
            
            # 使用TestResultService生成Test Result表格，传递Word应用程序实例和文档实例以避免重新打开文档
            # 设置should_save_doc=False，因为我们稍后会统一保存
            result = self.test_result_service.generate_test_result_with_structure(
                matrix_structure=matrix_data_structure,
                document_path=document_path,
                progress_callback=progress_callback,
                status_callback=status_callback,
                word_app_instance=word_app,
                word_doc_instance=word_doc,
                should_save_doc=False
            )
            
            if result:
                logger.info("Test Result表格生成完成")
            else:
                logger.error("Test Result表格生成失败")
            
            # 现在填充测试样品信息表格
            # 从matrix_data_structure或相关数据源中提取测试样品信息
            try:
                # 从JSON数据中提取测试样品信息
                sample_data = []
                # 尝试从matrix_data_structure中获取数据，如果没有则从其他地方获取
                if hasattr(matrix_data_structure, 'header_data'):
                    # 从header_data中提取测试样品信息
                    header_data = matrix_data_structure.header_data if hasattr(matrix_data_structure, 'header_data') else {}
                    sample_data = SampleDataExtractor.extract_sample_info_from_json(header_data)
                else:
                    # 如果matrix_data_structure没有header_data，尝试从其他途径获取
                    # 这里假设我们从某个全局数据源或上下文获取JSON数据
                    # 暂时创建示例数据
                    pass
                
                if sample_data:
                    logger.info(f"开始填充测试样品信息表格，共 {len(sample_data)} 条数据")
                    # 使用TestSampleInfoService填充测试样品信息表格
                    sample_result = self.test_sample_info_service.fill_test_sample_info_table(
                        document_path=document_path,
                        sample_data=sample_data,
                        word_app_instance=word_app,
                        word_doc_instance=word_doc  # 传递文档实例以避免重复打开
                    )
                    
                    if sample_result:
                        logger.info("测试样品信息表格填充完成")
                    else:
                        logger.error("测试样品信息表格填充失败")
                else:
                    logger.info("没有找到测试样品信息数据，跳过填充")
            except Exception as e:
                logger.error(f"填充测试样品信息表格时出错: {e}")
                import traceback
                logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            # 在所有处理完成后，不保存文档，由调用者负责保存
            # if word_doc:
            #     word_doc.Save()
            #     logger.info(f"文档最终保存: {document_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"填充Test Description和Test Method表格时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            if status_callback:
                self._safe_callback_call(status_callback, f"错误: {str(e)}")
            return False
        finally:
            # 确保Word应用和文档被正确关闭
            # 仅在我们创建了实例时才关闭它们，如果是由外部传入的实例，则不应关闭
            try:
                # 只有当word_doc_instance为None时，表示是我们创建的实例，才需要关闭
                if word_doc:
                    word_doc.Close()
            except:
                pass
            try:
                # 只有当word_app_instance为None时，表示是我们创建的实例，才需要关闭
                if word_app:
                    word_app.Quit()
            except:
                pass

    def _fill_description_table_win32com(self, target_table, document_path: str, word_app_instance=None) -> None:
        """
        使用win32com填充Test Description表格
        
        根据要求：动态获取Matrix页面表格中的首列和第6列及之后的组别列，
        行截止到"Time"所在行的上一行，列截止于"Notes"所在列的前一列。
        表格列数根据组别列数量动态调整，第一列为Test Item，其余列为各组别数据。
        
        Args:
            target_table: Word表格对象（win32com对象）
            document_path: Word文档路径
            word_app_instance: Word应用程序实例，如果为None则创建新的实例
        """
        logger.info("开始填充Test Description表格")
        
        # 从MatrixService获取表头信息
        from src.features.matrix.service.matrix_service import MatrixService
        matrix_service = MatrixService.shared()
        
        # 获取表头行
        header_row = matrix_service.data_model.headers if hasattr(matrix_service.data_model, 'headers') else []
        
        logger.info(f"Matrix表头: {header_row}")
        
        # 确定列范围：从第6列（索引5）开始，到"Notes"列的前一列结束（不包含Notes列）
        start_col_index = 5  # 第6列开始（固定）
        end_col_index = len(header_row) - 1  # 默认为最后一列
        
        for i, col_header in enumerate(header_row):
            if col_header.lower() == "notes":
                end_col_index = i - 1  # 截止到"Notes"列的前一列（不包含Notes列）
                logger.info(f"找到Notes列在索引 {i}，所以截止到索引 {end_col_index}")
                break
        
        # 获取组别列数量（注意：这里计算的是需要填充的列数，不包含Notes列）
        group_columns_count = max(0, end_col_index - start_col_index)
        if group_columns_count < 0:
            group_columns_count = 0
        
        # 为了避免表格过宽，限制最大组别列数
        max_group_columns = 15  # 限制最大组别列数为15，这样总列数最多为16（1列Test Item + 15组别列）
        if group_columns_count > max_group_columns:
            group_columns_count = max_group_columns
            logger.warning(f"组别列数量超过最大限制，调整为 {max_group_columns} 列")
        
        logger.info(f"组别列数量: {group_columns_count}, 起始列索引: {start_col_index}, 结束列索引: {end_col_index}")
        
        # 总列数 = 首列(Test Item) + 组别列数量
        target_cols = 1 + group_columns_count  # 1为Test Item列，其余为组别列
        
        # 从MatrixService获取数据行，直到"Time"行的上一行
        data_rows = matrix_service.data_model.rows if hasattr(matrix_service.data_model, 'rows') else []
        rows_to_process = []
        
        time_row_found = False
        for row in data_rows:
            if len(row) > 0 and row[0].lower().startswith("time"):
                time_row_found = True
                logger.info(f"找到Time行: {row[0]}")
                break
            rows_to_process.append(row)

        logger.info(f"处理 {len(rows_to_process)} 行数据，包含标题行")
        
        # 如果word_app_instance存在，直接使用，否则创建新的实例
        if word_app_instance is None:
            logger.warning("警告: Word应用程序实例为空，无法继续填充表格")
            return
        
        # 直接使用传入的Word应用程序实例
        word_app = word_app_instance
        word_app.Visible = False  # 确保Word应用程序不可见
        word_app.DisplayAlerts = False  # 关闭警告提示
        
        # 检查是否成功找到表格
        if not target_table:
            logger.warning("未找到TEST DESCRIPTION表格")
            return
        
        # 调整表格行数以匹配数据行数
        current_rows = target_table.Rows.Count
        required_rows = len(rows_to_process)
        logger.info(f"当前表格行数: {current_rows}, 需要行数: {required_rows}")
        
        if required_rows > current_rows:
            # 添加新行，同时保持原有格式
            for _ in range(required_rows - current_rows):
                target_table.Rows.Add()
            logger.info(f"添加了 {required_rows - current_rows} 行")
        elif required_rows < current_rows:
            # 删除多余行，但至少保留1行
            for _ in range(current_rows - required_rows):
                if target_table.Rows.Count > required_rows and required_rows > 0:
                    target_table.Rows(target_table.Rows.Count).Delete()
            logger.info(f"删除了 {current_rows - required_rows} 行")
    
        # 调整表格列数以匹配组别列数量+1（第一列为Test Item）
        logger.info(f"当前表格列数: {target_table.Columns.Count}, 需要列数: {target_cols}")
        
        current_cols = target_table.Columns.Count
        if current_cols < target_cols:
            # 检查是否会超过Word表格的合理列数限制（Word最大允许63列，但为了页面显示效果，我们限制在合理范围内）
            cols_to_add = target_cols - current_cols
            if cols_to_add > 0:
                # 为了避免表格过宽，限制最大列数不超过20列
                max_allowed_cols = 20
                if target_table.Columns.Count + cols_to_add > max_allowed_cols:
                    cols_to_add = max_allowed_cols - target_table.Columns.Count
                    logger.warning(f"需要的列数超过最大限制，调整为添加 {cols_to_add} 列，总共 {max_allowed_cols} 列")
                
                if cols_to_add > 0:
                    # 在添加新列前，先调整现有列的宽度，为新列留出空间
                    # 将所有现有列的宽度设置为较小值，以避免表格过宽
                    try:
                        # 尝试将现有列的宽度设置为较小值（0.2英寸），以便为新列腾出空间
                        for i in range(1, target_table.Columns.Count + 1):
                            try:
                                target_table.Columns(i).SetWidth(18.0, 1)  # 18磅约等于0.25英寸
                            except:
                                pass  # 如果设置宽度失败，继续处理
                    except:
                        pass  # 如果整体设置失败，继续添加列
                    
                    # 添加新列，同时保持原有格式
                    for _ in range(cols_to_add):
                        try:
                            target_table.Columns.Add()
                        except Exception as e:
                            logger.warning(f"添加列时出错，可能已达到最大列数限制: {e}")
                            break
                    logger.info(f"添加了 {cols_to_add} 列")
                    # 添加列后立即重新应用表格格式，确保表格适应窗口
                    from .utils.table_handler import TableHandler
                    TableHandler.apply_table_formatting(target_table)
        elif current_cols > target_cols:
            for _ in range(current_cols - target_cols):
                if target_table.Columns.Count > target_cols:
                    target_table.Columns(target_table.Columns.Count).Delete()
            logger.info(f"删除了 {current_cols - target_cols} 列")
            # 删除列后也需要重新应用表格格式
            from .utils.table_handler import TableHandler
            TableHandler.apply_table_formatting(target_table)
        
        logger.info(f"最终表格尺寸 - 行数: {target_table.Rows.Count}, 列数: {target_table.Columns.Count}")
        
        # 填充数据（包含标题行）
        for i, row_data in enumerate(rows_to_process):
            actual_row_index = i  # 从0开始
            if actual_row_index < target_table.Rows.Count:
                row = target_table.Rows(actual_row_index + 1)  # Win32COM索引从1开始
                
                # 第一列：Test Item（来自Matrix的第一列）
                if len(row_data) > 0:
                    test_item = row_data[0] if row_data[0] else ""
                    if test_item:
                        row.Cells(1).Range.Text = str(test_item).rstrip('\x07')  # 移除段落标记
                        # logger.debug(f"第{actual_row_index+1}行第1列填充: {test_item}")
                
                # 其余列：各组别列内容（从第6列开始到Notes列前一列）
                for j in range(group_columns_count):
                    col_index = start_col_index + j  # 固定从索引5（第6列）开始
                    if col_index < len(row_data) and row_data[col_index]:
                        cell_content = str(row_data[col_index]).rstrip('\x07')  # 移除段落标记
                        # 确保单元格存在
                        if j + 2 <= row.Cells.Count:
                            row.Cells(j + 2).Range.Text = cell_content  # Win32COM索引从1开始，第一列是索引1
                            # logger.debug(f"第{actual_row_index+1}行第{j+2}列填充: {cell_content}")
                
                # 保持原有的单元格格式，而不是强制设置格式
                # 只对内容进行处理，保留原始表格样式
                actual_cols = min(target_cols, row.Cells.Count)
                for j in range(actual_cols):
                    # 确保单元格存在
                    if j + 1 <= row.Cells.Count:
                        # 保留原有格式，只做必要的格式调整
                        # 保持原有的字体、对齐方式等格式
                        try:
                            # 保持原有的格式，仅在必要时设置
                            pass
                        except:
                            logger.warning(f"无法保留第{actual_row_index+1}行第{j+1}列的格式")
        
        # 最后再应用一次表格格式设置，确保整体格式正确
        from .utils.table_handler import TableHandler
        TableHandler.apply_table_formatting(target_table)

        # 查找并设置"Sample size"行的背景色为浅蓝色
        try:
            for i in range(1, target_table.Rows.Count + 1):
                row = target_table.Rows(i)
                first_cell = row.Cells(1)
                cell_text = first_cell.Range.Text.strip().lower()
                if cell_text.startswith("sample"):
                    # 找到Sample行，设置背景色为浅蓝色 (RGB 135,206,235) -> BGR 0xEBCE87
                    for j in range(1, row.Cells.Count + 1):
                        cell = row.Cells(j)
                        # 设置单元格背景色为浅蓝色 (RGB 135,206,235) - 在BGR格式中为 0xEBCE87
                        cell.Shading.BackgroundPatternColor = 0xEBCE87
                    logger.info(f"已为Sample size行({i})设置浅蓝色背景")
                    break
        except Exception as e:
            logger.warning(f"设置Sample size行背景色时出错: {e}")

        # 注意：不要在这里保存文档，因为主方法会处理保存

    def fill_test_sample_info_table_from_json(
        self,
        document_path: str,
        json_data: Dict[str, Any],
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        word_app_instance=None,
        word_doc_instance=None
    ) -> bool:
        """
        从JSON数据填充测试样品信息表格
        
        Args:
            document_path: Word文档路径
            json_data: JSON数据字典
            progress_callback: 进度回调函数
            status_callback: 状态回调函数
            word_app_instance: Word应用程序实例（可选）
            word_doc_instance: Word文档实例（可选）
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"开始从JSON数据填充测试样品信息表格，文档路径: {document_path}")
        
        try:
            if status_callback:
                self._safe_callback_call(status_callback, "正在提取测试样品信息...")
            
            # 从JSON数据中提取测试样品信息
            sample_data = SampleDataExtractor.extract_sample_info_from_json(json_data)
            
            if not sample_data:
                logger.warning("未从JSON数据中提取到测试样品信息")
                if status_callback:
                    self._safe_callback_call(status_callback, "警告: 未找到测试样品信息数据")
                return True  # 不算错误，只是没有数据填充
            
            if status_callback:
                self._safe_callback_call(status_callback, f"提取到 {len(sample_data)} 条测试样品信息")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 50)
            
            if status_callback:
                self._safe_callback_call(status_callback, "正在填充测试样品信息表格...")
            
            # 使用TestSampleInfoService填充测试样品信息表格
            result = self.test_sample_info_service.fill_test_sample_info_table(
                document_path=document_path,
                sample_data=sample_data,
                word_app_instance=word_app_instance,
                word_doc_instance=word_doc_instance  # 传递Word文档实例以避免重复打开文档
            )
            
            # 注意：fill_test_sample_info_table不会保存文档，保存由调用者处理
            
            if result:
                logger.info("测试样品信息表格填充完成")
                if status_callback:
                    self._safe_callback_call(status_callback, "测试样品信息表格填充完成")
            else:
                logger.error("测试样品信息表格填充失败")
                if status_callback:
                    self._safe_callback_call(status_callback, "错误: 测试样品信息表格填充失败")
            
            if progress_callback:
                self._safe_callback_call(progress_callback, 100)
            
            return result
            
        except Exception as e:
            logger.error(f"填充测试样品信息表格时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            if status_callback:
                self._safe_callback_call(status_callback, f"错误: {str(e)}")
            return False

    def _fill_method_table_win32com(self, target_table, document_path: str, word_app_instance=None) -> None:
        """
        使用win32com填充Test Method表格

        根据要求：动态获取Matrix页面表格中的第0,2,3,4列，
        行截止到"Sample size"所在行的上一行。
        表格列数为固定的3列，第一列为Test Item，第二列为Test Method，第三列为Condition。
        
        Args:
            target_table: Word表格对象（win32com对象）
            document_path: Word文档路径
            word_app_instance: Word应用程序实例，如果为None则创建新的实例
        """
        logger.info("开始使用win32com填充Test Method表格")
        
        # 从MatrixService获取当前数据
        from src.features.matrix.service.matrix_service import MatrixService
        matrix_service = MatrixService.shared()
        
        # 获取表头行
        header_row = matrix_service.data_model.headers if hasattr(matrix_service.data_model, 'headers') else []
        
        logger.info(f"Matrix表头: {header_row}")
        
        # 确定列范围：第0,2,3,4列
        col_indices = [0, 2, 3, 4]  # 对应第1,3,4,5列
        
        logger.info(f"填充列索引: {col_indices}")
        
        # 固定目标列数为3（Test Item, Test Method, Condition）
        target_cols = 3
        
        # 获取数据行，直到"Sample size"行的上一行
        data_rows = matrix_service.data_model.rows if hasattr(matrix_service.data_model, 'rows') else []
        rows_to_process = []
        
        sample_row_found = False
        for row in data_rows:
            if len(row) > 0:
                # 检查首列是否以"Sample"开头（统一与 TEST DESCRIPTION 表格的判断逻辑）
                first_cell_value = str(row[0]).strip() if row[0] else ""
                if first_cell_value.lower().startswith("sample"):
                    sample_row_found = True
                    logger.info(f"找到Sample行: {row[0]}")
                    break
            rows_to_process.append(row)

        logger.info(f"处理 {len(rows_to_process)} 行数据，包含标题行")
        
        # 如果word_app_instance存在，直接使用，否则创建新的实例
        if word_app_instance is None:
            logger.warning("警告: Word应用程序实例为空，无法继续填充表格")
            return
        
        # 直接使用传入的Word应用程序实例
        word_app = word_app_instance
        word_app.Visible = False  # 确保Word应用程序不可见
        word_app.DisplayAlerts = False  # 关闭警告提示
        
        # 检查是否成功找到表格
        if not target_table:
            logger.warning("未找到TEST METHODS/REQUIREMENTS表格")
            return
        
        # 调整表格行数以匹配数据行数
        current_rows = target_table.Rows.Count
        required_rows = len(rows_to_process)
        logger.info(f"当前表格行数: {current_rows}, 需要行数: {required_rows}")
        
        if required_rows > current_rows:
            # 添加新行，同时保持原有格式
            for _ in range(required_rows - current_rows):
                target_table.Rows.Add()
            logger.info(f"添加了 {required_rows - current_rows} 行")
        elif required_rows < current_rows:
            # 删除多余行，但至少保留1行
            for _ in range(current_rows - required_rows):
                if target_table.Rows.Count > required_rows and required_rows > 0:
                    target_table.Rows(target_table.Rows.Count).Delete()
            logger.info(f"删除了 {current_rows - required_rows} 行")

        # 填充数据（包含标题行）
        for i, row_data in enumerate(rows_to_process):
            actual_row_index = i  # 从0开始
            if actual_row_index < target_table.Rows.Count:
                row = target_table.Rows(actual_row_index + 1)  # Win32COM索引从1开始
                
                # 第一列：Test Item（来自Matrix的第1列，索引0）
                if len(row_data) > col_indices[0] and row_data[col_indices[0]]:
                    test_item = row_data[col_indices[0]] if row_data[col_indices[0]] else ""
                    if test_item:
                        row.Cells(1).Range.Text = str(test_item).rstrip('\x07')  # 移除段落标记
                        # logger.debug(f"第{actual_row_index+1}行第1列填充: {test_item}")
                
                # 第二列：Test Method（来自Matrix的第3列，索引2）
                if len(row_data) > col_indices[1] and row_data[col_indices[1]]:
                    test_method = row_data[col_indices[1]] if row_data[col_indices[1]] else ""
                    if test_method:
                        row.Cells(2).Range.Text = str(test_method).rstrip('\x07')  # 移除段落标记
                        # logger.debug(f"第{actual_row_index+1}行第2列填充: {test_method}")
                
                # 第三列：Condition（来自Matrix的第4列，索引3）
                if len(row_data) > col_indices[2] and row_data[col_indices[2]]:
                    condition = row_data[col_indices[2]] if row_data[col_indices[2]] else ""
                    if condition:
                        row.Cells(3).Range.Text = str(condition).rstrip('\x07')  # 移除段落标记
                        # logger.debug(f"第{actual_row_index+1}行第3列填充: {condition}")

                # 第四列：Requirements（来自Matrix的第5列，索引4）
                if len(row_data) > col_indices[3] and row_data[col_indices[3]]:
                    requirements = row_data[col_indices[3]] if row_data[col_indices[3]] else ""
                    if requirements:
                        row.Cells(4).Range.Text = str(requirements).rstrip('\x07')  # 移除段落标记
                        # logger.debug(f"第{actual_row_index+1}行第4列填充: {requirements}")
                
                # 保持原有的单元格格式，而不是强制设置格式
                # 只对内容进行处理，保留原始表格样式
                actual_cols = min(target_cols, row.Cells.Count)
                for j in range(actual_cols):
                    # 确保单元格存在
                    if j + 1 <= row.Cells.Count:
                        # 保留原有格式，只做必要的格式调整
                        # 保持原有的字体、对齐方式等格式
                        try:
                            # 保持原有的格式，仅在必要时设置
                            pass
                        except:
                            logger.warning(f"无法保留第{actual_row_index+1}行第{j+1}列的格式")
        
        # 最后再应用一次表格格式设置，确保整体格式正确
        from .utils.table_handler import TableHandler
        TableHandler.apply_table_formatting(target_table)

        # 注意：不要在这里保存文档，因为主方法会处理保存
