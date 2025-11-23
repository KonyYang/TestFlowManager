# src/features/matrix/service/matrix_service.py
from src.core import logger
from src.features.matrix.model.matrix_data import MatrixData
from src.features.matrix.service.matrix_cell_service import MatrixCellService
from src.features.matrix.service.matrix_initializer import MatrixInitializer
from openpyxl import Workbook
from openpyxl.utils import get_column_letter


class MatrixService:
    """Matrix服务层 - Service层"""

    def __init__(self):
        self.data_model = MatrixData()
        self.cell_service = MatrixCellService()
        self.initializer = MatrixInitializer(self.data_model)
        # 临时存储合并单元格信息
        self.merged_cells_info = []
        # 存储最近导入的规格书文件路径
        self.last_imported_spec_path = None

    def add_column(self, column_name="", position=None):
        """添加新列 - Service层业务逻辑"""
        return self.data_model.add_column(column_name, position)

    def move_column(self, from_index, to_index):
        """移动列 - Service层业务逻辑"""
        return self.data_model.move_column(from_index, to_index)

    def remove_column(self, column_index):
        """删除指定列 - Service层业务逻辑"""
        return self.data_model.remove_column(column_index)

    def add_row(self, row_data=None):
        """添加新行 - Service层业务逻辑"""
        return self.data_model.add_row(row_data)

    def insert_row(self, row_index, row_data=None):
        """在指定位置插入新行 - Service层业务逻辑"""
        return self.data_model.insert_row(row_index, row_data)

    def remove_row(self, row_index):
        """删除指定行 - Service层业务逻辑"""
        return self.data_model.remove_row(row_index)

    def move_row(self, from_index, to_index):
        """移动行 - Service层业务逻辑"""
        return self.data_model.move_row(from_index, to_index)

    def copy_row(self, row_index):
        """复制行 - Service层业务逻辑"""
        return self.data_model.copy_row(row_index)

    def paste_row(self, row_index, row_data):
        """粘贴行 - Service层业务逻辑"""
        return self.data_model.paste_row(row_index, row_data)

    def copy_column(self, col_index):
        """复制列 - Service层业务逻辑"""
        return self.data_model.copy_column(col_index)

    def paste_column(self, col_index, column_data):
        """粘贴列 - Service层业务逻辑"""
        return self.data_model.paste_column(col_index, column_data)

    def get_cell_value(self, row_index, col_index):
        """获取单元格值 - Service层数据访问"""
        return self.data_model.get_cell_value(row_index, col_index)

    def set_cell_value(self, row_index, col_index, value):
        """设置单元格值 - Service层数据修改"""
        return self.data_model.set_cell_value(row_index, col_index, value)

    def find_by_content(self, search_text):
        """通过内容查找单元格 - Service层查询功能"""
        return self.data_model.find_by_content(search_text)

    def merge_or_split_cells(self, table_widget):
        """合并或拆分单元格 - Service层业务逻辑"""
        return self.cell_service.merge_or_split_cells(table_widget)
        
    def can_undo_cell_operation(self):
        """检查是否可以撤销单元格操作"""
        return self.cell_service.can_undo()
        
    def can_redo_cell_operation(self):
        """检查是否可以重做单元格操作"""
        return self.cell_service.can_redo()
        
    def undo_cell_operation(self):
        """撤销单元格操作"""
        return self.cell_service.undo()
        
    def redo_cell_operation(self):
        """重做单元格操作"""
        return self.cell_service.redo()
        
    def get_undo_cell_operation_text(self):
        """获取撤销单元格操作的文本描述"""
        return self.cell_service.undo_text()
        
    def get_redo_cell_operation_text(self):
        """获取重做单元格操作的文本描述"""
        return self.cell_service.redo_text()

    def initialize_matrix(self):
        """初始化Matrix - Service层业务逻辑"""
        return self.initializer.initialize_matrix()

    def export_to_excel(self, file_path):
        """导出到Excel - Service层持久化功能"""
        try:
            # 创建工作簿
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active

            # 先添加数据行（不包括表头）
            for row_idx, row_data in enumerate(self.data_model.rows):
                for col_idx, cell_value in enumerate(row_data):
                    ws.cell(row=row_idx + 1, column=col_idx + 1, value=cell_value)
            
            # 应用合并单元格
            logger.debug(f"准备导出 {len(self.merged_cells_info)} 个合并单元格")
            for merge_info in self.merged_cells_info:
                top_row = merge_info['top_row'] + 1  # +1 because of 1-based indexing
                left_col = merge_info['left_col'] + 1  # +1 because of 1-based indexing
                bottom_row = top_row + merge_info['row_count'] - 1
                right_col = left_col + merge_info['col_count'] - 1
                
                logger.debug(f"处理合并单元格: top_row={top_row}, left_col={left_col}, "
                           f"bottom_row={bottom_row}, right_col={right_col}")
                
                # 先保存合并区域左上角单元格的值
                top_left_value = ws.cell(row=top_row, column=left_col).value
                
                # 清空整个合并区域的值
                for row in range(top_row, bottom_row + 1):
                    for col in range(left_col, right_col + 1):
                        ws.cell(row=row, column=col, value=None)
                
                # 将原值设置回合并区域的左上角单元格
                ws.cell(row=top_row, column=left_col, value=top_left_value)
                
                # 合并单元格
                ws.merge_cells(
                    start_row=top_row, 
                    start_column=left_col, 
                    end_row=bottom_row, 
                    end_column=right_col
                )

            # 保存文件
            wb.save(file_path)
            return True
        except PermissionError:
            # 文件被其他程序占用（如Excel）
            logger.error(f"导出Excel失败: 文件被占用，可能已在Excel中打开")
            return False
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            return False

    def import_from_excel(self, file_path):
        """从Excel导入数据 - Service层持久化功能"""
        try:
            from openpyxl import load_workbook
            wb = load_workbook(file_path)
            ws = wb.active

            # 清空现有数据
            self.data_model.headers = []
            self.data_model.rows = []

            # 读取表头
            for cell in ws[1]:
                self.data_model.headers.append(cell.value if cell.value is not None else "")

            # 读取数据行
            for row in ws.iter_rows(min_row=2, values_only=True):
                self.data_model.rows.append([cell if cell is not None else "" for cell in row])

            # 确保有默认列数
            while len(self.data_model.headers) < 8:
                self.data_model.headers.append(self.data_model._column_index_to_letter(len(self.data_model.headers)))
            
            # 确保有默认行
            if len(self.data_model.rows) == 0:
                # 添加默认行
                self.data_model.rows.append([""] * len(self.data_model.headers))
                self.data_model.rows.append([""] * len(self.data_model.headers))

            return True
        except Exception as e:
            logger.error(f"导入Excel失败: {e}")
            return False

    def import_from_excel_with_sheet(self, file_path, sheet_name=None):
        """从Excel导入数据（指定工作表） - Service层持久化功能"""
        try:
            logger.info(f"开始从Excel导入数据: {file_path}，工作表: {sheet_name}")
            
            # 使用ExcelParser解析文档
            from src.features.matrix.service.document_parsers.excel_parser import ExcelParser
            parser = ExcelParser()
            result = parser.parse(file_path, sheet_name)
            data = result['data']
            merged_cells = result['merged_cells']
            
            # 如果成功提取数据，则更新数据模型
            if data is not None and len(data) > 0:
                logger.info(f"成功从Excel文档提取数据，数据行数: {len(data)}")
                if len(data) > 0:
                    logger.info(f"数据列数: {len(data[0])}")
                    logger.info(f"表头内容: {data[0][:5]}...")  # 只显示前5列
                
                # 清空现有数据
                self.data_model.headers = []
                self.data_model.rows = []
                
                # 处理表头（使用字母标识，而不是使用第一行数据作为表头）
                if len(data) > 0:
                    for i in range(len(data[0])):  # 根据数据列数创建表头
                        self.data_model.headers.append(self.data_model._column_index_to_letter(i))
                    logger.info(f"设置表头，列数: {len(self.data_model.headers)}")
                    
                # 处理数据行（所有原始数据行都作为数据行）
                if len(data) > 0:
                    self.data_model.rows = data  # 数据行就是所有提取的数据
                    logger.info(f"设置数据行，行数: {len(self.data_model.rows)}")
                
                # 确保有默认列数
                while len(self.data_model.headers) < 8:
                    self.data_model.headers.append(self.data_model._column_index_to_letter(len(self.data_model.headers)))
                
                # 确保有默认行
                if len(self.data_model.rows) == 0:
                    # 添加默认行
                    self.data_model.rows.append([""] * len(self.data_model.headers))
                    self.data_model.rows.append([""] * len(self.data_model.headers))
                    logger.info("添加默认行数据")

                # 保存合并单元格信息，以便在更新表格显示时使用
                self.merged_cells_info = []
                for merged_cell in merged_cells:
                    self.merged_cells_info.append({
                        'top_row': merged_cell['min_row'],
                        'left_col': merged_cell['min_col'],
                        'row_count': merged_cell['max_row'] - merged_cell['min_row'] + 1,
                        'col_count': merged_cell['max_col'] - merged_cell['min_col'] + 1
                    })
                    logger.debug(f"导入合并单元格信息: top_row={merged_cell['min_row']}, left_col={merged_cell['min_col']}, "
                               f"row_count={merged_cell['max_row'] - merged_cell['min_row'] + 1}, "
                               f"col_count={merged_cell['max_col'] - merged_cell['min_col'] + 1}")

                logger.info("Excel数据导入完成")
                return True
            else:
                logger.warning("未能从Excel文档提取数据，保持原有数据不变")
                return False
        except Exception as e:
            logger.error(f"导入Excel失败: {e}")
            return False

    def import_from_spec(self, file_path, page_number=None, keyword=None):
        """从Spec导入数据 - Service层持久化功能"""
        try:
            logger.info(f"开始从Spec导入数据: {file_path}")
            
            # 保存导入的规格书文件路径
            self.last_imported_spec_path = file_path
            
            # 实现Spec文件导入逻辑
            # 调用spec_extractor来处理不同格式的文件
            from src.features.matrix.service.spec_extractor import SpecExtractor
            extractor = SpecExtractor()
            # 传递页码和关键字参数
            data_result = extractor.extract_from_document(file_path, page_number, keyword)
            
            # 如果成功提取数据，则更新数据模型
            if data_result is not None:
                # 处理不同的返回格式
                if isinstance(data_result, dict) and 'data' in data_result:
                    # 包含合并单元格信息的格式
                    data = data_result['data']
                    merged_cells = data_result.get('merged_cells', [])
                else:
                    # 简单数据格式
                    data = data_result
                    merged_cells = []
                
                # 清空现有数据
                self.data_model.headers = []
                self.data_model.rows = []
                
                # 设置表头（使用字母标识，而不是使用第一行数据作为表头）
                if len(data) > 0:
                    for i in range(len(data[0])):  # 根据数据列数创建表头
                        self.data_model.headers.append(self.data_model._column_index_to_letter(i))
                    logger.info(f"设置表头，列数: {len(self.data_model.headers)}")
                
                # 设置数据行（所有原始数据行都作为数据行）
                if len(data) > 0:
                    self.data_model.rows = data  # 数据行就是所有提取的数据
                    logger.info(f"设置数据行，行数: {len(self.data_model.rows)}")
                
                # 确保有默认列数
                while len(self.data_model.headers) < 8:
                    self.data_model.headers.append(self.data_model._column_index_to_letter(len(self.data_model.headers)))
                
                # 确保有默认行
                if len(self.data_model.rows) == 0:
                    # 添加默认行
                    self.data_model.rows.append([""] * len(self.data_model.headers))
                    self.data_model.rows.append([""] * len(self.data_model.headers))
                    logger.info("添加默认行数据")

                # 保存合并单元格信息
                self.merged_cells_info = []
                for merged_cell in merged_cells:
                    self.merged_cells_info.append({
                        'top_row': merged_cell['min_row'],
                        'left_col': merged_cell['min_col'],
                        'row_count': merged_cell['max_row'] - merged_cell['min_row'] + 1,
                        'col_count': merged_cell['max_col'] - merged_cell['min_col'] + 1
                    })

                logger.info("Spec数据导入完成")
                return True
            else:
                logger.warning("未能从Spec文档提取数据，保持原有数据不变")
                return False
        except Exception as e:
            logger.error(f"导入Spec失败: {e}")
            return False
            
    def extract_test_methods_from_spec(self):
        """
        从已导入的规格书中提取测试方法标准并填充到Matrix中
        
        Returns:
            bool: 是否成功提取并填充测试方法
        """
        try:
            logger.info("开始从规格书提取测试方法标准")
            
            # 检查是否已导入规格书
            if not self.last_imported_spec_path:
                logger.warning("未找到已导入的规格书文件")
                return False
                
            logger.info(f"使用规格书文件路径: {self.last_imported_spec_path}")
            
            # 直接使用第二列作为Section列（索引为1）
            section_col_index = 1
            # Test Method列通常在第三列（索引为2）
            test_method_col_index = 2
            # Condition列通常在第四列（索引为3）
            condition_col_index = 3
            # Requirement列通常在第五列（索引为4）
            requirement_col_index = 4
            
            logger.info(f"使用第 {section_col_index + 1} 列作为'Section'列")
            logger.info(f"使用第 {test_method_col_index + 1} 列作为'Test Method'列")
            logger.info(f"使用第 {condition_col_index + 1} 列作为'Condition'列")
            logger.info(f"使用第 {requirement_col_index + 1} 列作为'Requirement'列")
            
            # 构建章节号映射 {row_index: chapter_number}
            chapter_mappings = {}
            # 跳过前两行（表头和列名行）
            for row_index in range(2, len(self.data_model.rows)):
                row = self.data_model.rows[row_index]
                # 获取章节号
                if section_col_index < len(row):
                    chapter_number = row[section_col_index]
                    if chapter_number and str(chapter_number).strip():
                        # 确保这不是列名本身
                        if str(chapter_number).strip().lower() not in ["section", "test method"]:
                            chapter_mappings[row_index] = str(chapter_number).strip()
            
            if not chapter_mappings:
                logger.warning("未找到有效的章节号")
                logger.info(f"数据行数: {len(self.data_model.rows)}")
                if len(self.data_model.rows) > 0:
                    logger.info(f"表头: {self.data_model.headers}")
                    if len(self.data_model.rows) > 0:
                        logger.info(f"第一行数据: {self.data_model.rows[0]}")
                    if len(self.data_model.rows) > 1:
                        logger.info(f"第二行数据: {self.data_model.rows[1]}")
                    # 显示几行数据用于调试
                    for i in range(2, min(5, len(self.data_model.rows))):
                        if section_col_index < len(self.data_model.rows[i]):
                            logger.info(f"第{i+1}行Section列内容: {self.data_model.rows[i][section_col_index]}")
                return False
            
            logger.info(f"找到 {len(chapter_mappings)} 个章节号需要处理")
            logger.debug(f"章节号映射: {chapter_mappings}")
            
            # 从规格书中提取测试方法
            from src.features.matrix.service.spec_extractor import SpecExtractor
            extractor = SpecExtractor()
            test_methods = extractor.extract_test_methods(self.last_imported_spec_path, chapter_mappings)
            
            logger.info(f"从规格书中提取到 {len(test_methods)} 个测试方法")
            logger.debug(f"提取的测试方法: {test_methods}")
            
            # 获取模板数据
            from src.utils.template_data import get_condition_requirement_templates, get_template_aliases
            templates = get_condition_requirement_templates()
            aliases = get_template_aliases()
            
            # 将提取的测试方法填充到Matrix中，并根据Test Item列填充Condition和Requirement
            updated_count = 0
            for row_index in range(2, len(self.data_model.rows)):  # 从第3行开始处理（跳过表头）
                if row_index < len(self.data_model.rows):
                    # 获取Test Item（第一列）
                    test_item = ""
                    if len(self.data_model.rows[row_index]) > 0:
                        test_item = self.data_model.rows[row_index][0]
                    
                    logger.debug(f"处理第{row_index}行，Test Item: '{test_item}'")
                    
                    # 处理Test Method列
                    if test_method_col_index < len(self.data_model.rows[row_index]):
                        current_test_method = self.data_model.rows[row_index][test_method_col_index]
                        logger.debug(f"第{row_index}行当前Test Method列值: '{current_test_method}'")
                        
                        # 如果这一行有提取到的测试方法，则使用提取到的
                        if row_index in test_methods and test_methods[row_index]:
                            test_method = test_methods[row_index]
                            self.data_model.rows[row_index][test_method_col_index] = test_method
                            updated_count += 1
                            logger.debug(f"更新第{row_index}行的测试方法为: {test_method}")
                        # 如果Test Item包含"Examination"且Test Method列为空，则设置默认值
                        elif test_item and "examination" in test_item.lower().strip():
                            logger.debug(f"检测到包含Examination的项目，检查Test Method列是否为空")
                            if not current_test_method or not current_test_method.strip():
                                self.data_model.rows[row_index][test_method_col_index] = "EIA-364-18"
                                updated_count += 1
                                logger.debug(f"为第{row_index}行的Examination设置默认测试方法: EIA-364-18")
                            else:
                                logger.debug(f"第{row_index}行的Test Method列已有值: '{current_test_method}'，不设置默认值")
                        else:
                            logger.debug(f"第{row_index}行不包含Examination或已有测试方法，Test Item: '{test_item}'")
                    
                    # 根据Test Item填充Condition和Requirement
                    if test_item:
                        logger.debug(f"为第{row_index}行填充Condition和Requirement模板数据")
                        self._fill_condition_requirement_templates(
                            row_index, test_item, templates, aliases,
                            condition_col_index, requirement_col_index)
                    else:
                        logger.debug(f"第{row_index}行没有Test Item，跳过模板填充")
                else:
                    logger.warning(f"无法更新第{row_index}行的测试方法，行索引或列索引超出范围")
            
            logger.info(f"成功更新 {updated_count} 行的测试方法和模板数据")
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"从规格书提取测试方法时出错: {e}", exc_info=True)
            return False

    def _fill_condition_requirement_templates(self, row_index, test_item, templates, aliases, 
                                            condition_col_index, requirement_col_index):
        """
        根据测试项目填充Condition和Requirement模板数据
        
        Args:
            row_index: 行索引
            test_item: 测试项目名称
            templates: 模板数据字典
            aliases: 别名字典
            condition_col_index: Condition列索引
            requirement_col_index: Requirement列索引
        """
        logger.debug(f"开始为第{row_index}行填充模板数据，Test Item: '{test_item}'")
        
        # 查找匹配的模板
        condition, requirement = self._find_template_match(test_item, templates, aliases)
        if condition and requirement:
            # 填充Condition列
            if condition_col_index < len(self.data_model.rows[row_index]):
                self.data_model.rows[row_index][condition_col_index] = condition
                logger.debug(f"为第{row_index}行填充Condition: '{condition}'")
            else:
                logger.warning(f"Condition列索引超出范围，无法填充第{row_index}行")
            
            # 填充Requirement列
            if requirement_col_index < len(self.data_model.rows[row_index]):
                self.data_model.rows[row_index][requirement_col_index] = requirement
                logger.debug(f"为第{row_index}行填充Requirement: '{requirement}'")
            else:
                logger.warning(f"Requirement列索引超出范围，无法填充第{row_index}行")
            
            logger.debug(f"为第{row_index}行填充模板数据完成: {test_item} -> ({condition}, {requirement})")
        else:
            logger.debug(f"未找到第{row_index}行Test Item '{test_item}' 的匹配模板")

    def _find_template_match(self, test_item, templates, aliases):
        """
        根据测试项目查找匹配的模板数据
        
        Args:
            test_item: 测试项目名称
            templates: 模板数据字典
            aliases: 别名字典
            
        Returns:
            tuple: (condition, requirement) 或 (None, None)
        """
        test_item_lower = test_item.lower().strip()
        logger.debug(f"查找模板匹配: '{test_item}' (标准化为: '{test_item_lower}')")
        
        # 直接匹配
        for key, (condition, requirement) in templates.items():
            if key.lower() == test_item_lower:
                logger.debug(f"直接匹配成功: '{test_item}' -> '{key}'")
                return condition, requirement
        
        # 别名匹配
        for main_key, alias_list in aliases.items():
            if main_key in templates:
                for alias in alias_list:
                    if alias.lower() in test_item_lower or test_item_lower in alias.lower():
                        logger.debug(f"别名匹配成功: '{test_item}' -> '{main_key}' (通过别名: '{alias}')")
                        return templates[main_key]
        
        # 模糊匹配
        for key, (condition, requirement) in templates.items():
            if key.lower() in test_item_lower or test_item_lower in key.lower():
                logger.debug(f"模糊匹配成功: '{test_item}' -> '{key}'")
                return condition, requirement
        
        logger.debug(f"未找到匹配的模板: '{test_item}'")
        return None, None

    def _process_rows(self):
        """
        处理行数据，类似于VBA中的ProcessRows函数
        合并单元格内容并处理行数据
        """
        try:
            # 这里可以添加处理行数据的逻辑
            # 比如合并单元格内容，处理特殊格式等
            # 目前我们只是确保数据格式正确
            logger.info("处理行数据完成")
        except Exception as e:
            logger.error(f"处理行数据时出错: {e}", exc_info=True)
            
    def _check_duplicate_values(self):
        """
        检查重复值，从第1列到最后一列，从第1行到倒数第二行
        类似于VBA中的CheckDuplicateValues函数
        """
        try:
            logger.info("开始检查重复值")
            # 从第1列到最后一列
            for col_index in range(len(self.data_model.headers)):
                # 用于存储已见过的值
                seen_values = set()
                # 从第1行到倒数第二行
                for row_index in range(len(self.data_model.rows) - 1):
                    if row_index < len(self.data_model.rows) and col_index < len(self.data_model.rows[row_index]):
                        cell_value = self.data_model.rows[row_index][col_index]
                        # 如果值不为空且已经见过，则标记为重复
                        if cell_value and cell_value.strip() and cell_value in seen_values:
                            logger.warning(f"在第{row_index+1}行，第{col_index+1}列发现重复值: {cell_value}")
                        elif cell_value and cell_value.strip():
                            seen_values.add(cell_value)
                            
            logger.info("重复值检查完成")
        except Exception as e:
            logger.error(f"检查重复值时出错: {e}", exc_info=True)