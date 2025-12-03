"""
Matrix测试方法管理器
处理Matrix数据的测试方法相关业务逻辑
"""

from src.core import logger
from src.utils.standard_version_updater import update_test_method_versions
from src.features.matrix.service.defaults.test_method_defaults import TestMethodDefaults


class MatrixTestMethodManager:
    """Matrix测试方法管理器"""
    
    def __init__(self, data_model, template_filler):
        self.data_model = data_model
        self.template_filler = template_filler

    def update_standard_versions(self):
        """
        更新测试方法的标准版本号
        
        Returns:
            dict: 更新结果，包含是否成功更新以及更新详情
        """
        try:
            logger.info("开始更新测试方法标准版本号")
            
            # 调用标准版本更新工具
            result = update_test_method_versions(self.data_model.rows)
            
            if result["updated_count"] > 0:
                logger.info(f"成功更新 {result['updated_count']} 个测试方法的版本号")
                return {"success": True, "updated_count": result["updated_count"], "details": result["details"]}
            else:
                logger.info("未找到需要更新的测试方法版本号")
                return {"success": False, "updated_count": 0, "details": []}
                
        except Exception as e:
            logger.error(f"更新标准版本号时出错: {e}", exc_info=True)
            return {"success": False, "updated_count": 0, "details": [], "error": str(e)}

    def extract_test_methods_from_spec(self, last_imported_spec_path):
        """
        从已导入的规格书中提取测试方法标准并填充到Matrix中
        
        Returns:
            bool: 是否成功提取并填充测试方法
        """
        try:
            logger.info("开始从规格书提取测试方法标准")
            
            # 检查是否已导入规格书
            if not last_imported_spec_path:
                logger.info("未找到已导入的规格书文件，将继续执行模板填充功能")
                # 注意：这里不再直接返回False，而是继续执行模板填充部分
            
            logger.info(f"使用规格书文件路径: {last_imported_spec_path}")
            
            # 检查表头结构是否正确
            if len(self.data_model.rows) > 0:
                header_row = self.data_model.rows[0]
                # 检查第3、4、5列（索引为2、3、4）是否为"Test Method"、"Condition"、"Requirement"
                if (len(header_row) <= 2 or header_row[2] != "Test Method" or 
                    len(header_row) <= 3 or header_row[3] != "Condition" or 
                    len(header_row) <= 4 or header_row[4] != "Requirement"):
                    logger.warning("表头结构不正确，第3、4、5列应分别为'Test Method'、'Condition'、'Requirement'")
                    return False
            
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
            # 跳过第一行（表头），从第二行开始处理数据行（索引为1）
            for row_index in range(1, len(self.data_model.rows)):
                row = self.data_model.rows[row_index]
                # 检查是否遇到sample行，如果是则停止处理
                first_col_value = row[0] if len(row) > 0 else ""
                if first_col_value and str(first_col_value).strip().lower().startswith("sample"):
                    logger.info(f"遇到Sample行（第{row_index}行），停止提取测试方法")
                    break
                    
                # 获取章节号
                if section_col_index < len(row):
                    chapter_number = row[section_col_index]
                    if chapter_number and str(chapter_number).strip():
                        # 确保这不是列名本身
                        if str(chapter_number).strip().lower() not in ["section", "test method"]:
                            chapter_mappings[row_index] = str(chapter_number).strip()
            
            # 初始化测试方法字典
            test_methods = {}
            
            # 只有在有导入的规格书路径时才尝试提取测试方法
            if last_imported_spec_path:
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
                        for i in range(1, min(5, len(self.data_model.rows))):
                            if section_col_index < len(self.data_model.rows[i]):
                                logger.info(f"第{i+1}行Section列内容: {self.data_model.rows[i][section_col_index]}")
                    # 即使没有章节号也继续执行模板填充功能
                else:
                    logger.info(f"找到 {len(chapter_mappings)} 个章节号需要处理")
                    logger.debug(f"章节号映射: {chapter_mappings}")
                    
                    # 从规格书中提取测试方法
                    from src.features.matrix.service.spec.spec_extractor import SpecExtractor
                    extractor = SpecExtractor()
                    test_methods = extractor.extract_test_methods(last_imported_spec_path, chapter_mappings)
                    
                    logger.info(f"从规格书中提取到 {len(test_methods)} 个测试方法")
                    logger.debug(f"提取的测试方法: {test_methods}")
            else:
                logger.info("没有导入规格书文件，跳过测试方法提取")
            
            # 将提取的测试方法填充到Matrix中，并根据Test Item列填充Condition和Requirement
            updated_count = 0
            for row_index in range(1, len(self.data_model.rows)):  # 从第2行开始处理（跳过表头）
                # 检查是否遇到sample行，如果是则停止处理
                if row_index < len(self.data_model.rows):
                    first_col_value = self.data_model.rows[row_index][0] if len(self.data_model.rows[row_index]) > 0 else ""
                    if first_col_value and str(first_col_value).strip().lower().startswith("sample"):
                        logger.info(f"遇到Sample行（第{row_index}行），停止填充测试方法和模板")
                        break
                        
                if row_index < len(self.data_model.rows):
                    # 获取Test Item（第一列）
                    test_item = ""
                    if len(self.data_model.rows[row_index]) > 0:
                        test_item = self.data_model.rows[row_index][0]
                    
                    logger.debug(f"处理第{row_index}行，Test Item: '{test_item}'")
                    
                    # 处理Test Method列（仅在有导入规格书且有提取到测试方法时才更新）
                    if last_imported_spec_path and test_methods and test_method_col_index < len(self.data_model.rows[row_index]):
                        current_test_method = self.data_model.rows[row_index][test_method_col_index]
                        logger.debug(f"第{row_index}行当前Test Method列值: '{current_test_method}'")
                        
                        # 如果这一行有提取到的测试方法，则使用提取到的
                        if row_index in test_methods and test_methods[row_index]:
                            test_method = test_methods[row_index]
                            self.data_model.rows[row_index][test_method_col_index] = test_method
                            updated_count += 1
                            logger.debug(f"更新第{row_index}行的测试方法为: {test_method}")
                        # 检查是否应该应用默认测试方法
                        elif TestMethodDefaults.should_apply_default(test_item, current_test_method):
                            default_method = TestMethodDefaults.get_default_test_method(test_item)
                            self.data_model.rows[row_index][test_method_col_index] = default_method
                            updated_count += 1
                            logger.debug(f"为第{row_index}行的{test_item}设置默认测试方法: {default_method}")
                        else:
                            logger.debug(f"第{row_index}行不包含需要设置默认值的测试项或已有测试方法，Test Item: '{test_item}'")
                    # 如果没有导入规格书，但仍需处理需要默认测试方法的测试项
                    elif not last_imported_spec_path and test_item and test_method_col_index < len(self.data_model.rows[row_index]):
                        current_test_method = self.data_model.rows[row_index][test_method_col_index]
                        logger.debug(f"第{row_index}行当前Test Method列值: '{current_test_method}'")
                        # 检查是否应该应用默认测试方法
                        if TestMethodDefaults.should_apply_default(test_item, current_test_method):
                            default_method = TestMethodDefaults.get_default_test_method(test_item)
                            self.data_model.rows[row_index][test_method_col_index] = default_method
                            updated_count += 1
                            logger.debug(f"为第{row_index}行的{test_item}设置默认测试方法: {default_method}")
                        else:
                            logger.debug(f"第{row_index}行不包含需要设置默认值的测试项或已有测试方法，Test Item: '{test_item}'")
                    
                    # 根据Test Item填充Condition和Requirement（这部分总是执行）
                    if test_item:
                        logger.debug(f"为第{row_index}行填充Condition和Requirement模板数据")
                        self.template_filler.fill_condition_requirement_templates(
                            self.data_model, row_index, test_item,
                            condition_col_index, requirement_col_index)
                    else:
                        logger.debug(f"第{row_index}行没有Test Item，跳过模板填充")
                else:
                    logger.warning(f"无法更新第{row_index}行的测试方法，行索引或列索引超出范围")
            
            logger.info(f"成功更新 {updated_count} 行的测试方法和模板数据")
            # 即使没有更新任何测试方法，也返回True，因为我们完成了模板填充
            return True
            
        except Exception as e:
            logger.error(f"从规格书提取测试方法时出错: {e}", exc_info=True)
            return False

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