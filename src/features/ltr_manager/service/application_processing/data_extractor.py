"""
LTR数据提取模块
负责从Word文档中提取申请单数据
"""

import os
import logging
from typing import Dict, Any, Optional

from src.core.logger import logger
from src.utils.word_utils import (
    open_word_file,
    extract_field_value_from_table,
    find_paragraph_with_text,
    get_table_cell_text
)

class LTRApplicationDataExtractor:
    """
    LTR申请单数据提取类
    负责从Word文档中提取申请单数据
    """

    def __init__(self):
        pass

    def extract_application_data(self, doc_filepath: str) -> Dict[str, Any]:
        """
        从Word文档中提取申请单数据

        Args:
            doc_filepath: Word文档路径

        Returns:
            dict: 提取的数据或错误信息
        """
        logger.info(f"开始处理申请文件: {doc_filepath}")
        extracted_data = {}

        # 检查文件是否存在
        if not os.path.exists(doc_filepath):
            logger.error(f"文件未找到: {doc_filepath}")
            return {"error": f"File not found: {os.path.basename(doc_filepath)}"}

        # 使用COM接口打开Word文档
        doc = open_word_file(doc_filepath, read_only=True)
        if not doc:
            logger.error(f"无法打开文档: {doc_filepath}")
            return {"error": "无法打开Word文档"}

        try:
            # 提取主要字段
            fields = {
                'requested_by': ('Requested By:', False),
                'location': ('Mfg. Site:', False),
                'phone': ('Phone #:', False),
                'email_requestor': ('Email:', False),
                'date_lab_received_samples': ('Date Lab Received Samples:', False),
                'estimated_completion_date': ('Estimated Completion Date:', False),
                'sub_contract': ('Can testing be subcontracted?', False),
                'test_type': ('Test Type', True),
                'project_type': ('Project Type', True),
            }

            # 提取字段值
            for key, (label, next_row) in fields.items():
                value = extract_field_value_from_table(doc, label, next_row)
                extracted_data[key] = value
                logger.debug(f"提取字段 {key}: {value}")

            # 提取测试样品信息
            sample_info_dict = self._extract_test_sample_info(doc)
            extracted_data['sample_information'] = sample_info_dict['sample_info_str']
            extracted_data['product_name'] = sample_info_dict['product_name']              # 产品名称
            extracted_data['part_number'] = sample_info_dict['part_number']                # 料号
            extracted_data['lot_info'] = sample_info_dict['lot_info']                    # 批次
            extracted_data['base_material'] = sample_info_dict['base_material']          # 基材
            extracted_data['contact_plating'] = sample_info_dict['contact_plating']       # 接触镀层
            extracted_data['contact_lubricant'] = sample_info_dict['contact_lubricant']   # 润滑油
            extracted_data['housing_material'] = sample_info_dict['housing_material']    # 塑材
            logger.debug(f"提取样品信息: {sample_info_dict}")

            # 提取测试要求信息
            testing_info = self._extract_requested_testing_info(doc)
            extracted_data['tests_to_be_performed'] = testing_info.get('tests_to_be_performed', '')
            extracted_data['applicable_specifications'] = testing_info.get('applicable_specifications', '')
            logger.debug(f"提取测试要求信息: {testing_info}")

            # 填充其他字段
            for field in ['failed_item', 'sample_deposition',
                          'test_fee', 'remarks_po', 'start_test_date', 'finish_test_date',
                          'report_date']:
                extracted_data[field] = ""
                
            # 为project_leader设置默认值
            from src.core.config_manager import config_manager
            extracted_data['project_leader'] = config_manager.get_default("project_leader", "")

            # 添加文件路径字段
            extracted_data['file_path'] = doc_filepath

            logger.info(f"成功处理申请文件，提取到的数据: {extracted_data}")
            return extracted_data

        except Exception as e:
            logger.error(f"处理申请单文件时出错: {e}", exc_info=True)
            return {
                "error": f"处理申请单文件时出错: {str(e)}",
                "partial_data": extracted_data
            }
        finally:
            # 关闭文档
            try:
                doc.Close(SaveChanges=False)
            except Exception as e:
                logger.warning(f"关闭文档失败: {e}")

    def _extract_requested_testing_info(self, doc) -> Dict[str, str]:
        """
        提取测试描述信息

        Args:
            doc: Word文档对象

        Returns:
            dict: 包含测试信息的字典
        """
        logger.debug("开始提取请求的测试信息...")
        result = {"tests_to_be_performed": "", "applicable_specifications": ""}

        try:
            # 查找包含指定文本的段落
            para = find_paragraph_with_text(doc, "Description of Requested Testing")
            if para:
                # 获取下一个段落
                next_range = para.Range.Next(4)  # wdParagraph = 4

                if next_range.Tables.Count > 0:
                    table = next_range.Tables(1)

                    for i in range(2, table.Rows.Count + 1):  # 跳过表头
                        try:
                            # 提取第一列
                            first_col = get_table_cell_text(table, i, 1)

                            # 提取第二列
                            second_col = get_table_cell_text(table, i, 2)

                            # 空行判断（两列都为空）
                            if not first_col and not second_col:
                                break

                            # 添加到结果（用逗号拼接）
                            if first_col:
                                if result["tests_to_be_performed"]:
                                    result["tests_to_be_performed"] += ","
                                result["tests_to_be_performed"] += first_col

                            if second_col:
                                if result["applicable_specifications"]:
                                    result["applicable_specifications"] += ","
                                result["applicable_specifications"] += second_col

                            logger.debug(f"处理测试表格行 {i}: 测试项='{first_col}', 规范='{second_col}'")
                        except Exception as e:
                            logger.error(f"处理行 {i} 时出错: {e}")
        except Exception as e:
            logger.error(f"提取测试信息时出错: {e}")

        logger.debug(f"完成测试信息提取: {result}")
        return result

    def _extract_test_sample_info(self, doc) -> Dict[str, str]:
        """
        提取测试样品信息

        Args:
            doc: Word文档对象

        Returns:
            dict: 包含样品详细信息的字典
        """
        logger.debug("开始提取测试样品信息...")
        sample_info = []
        product_name = []
        part_number = []
        batch_info = []
        substrate_info = []
        plating_info = []
        lubricant_info = []
        plastic_info = []
        prev_first_col = ""

        try:
            # 查找包含指定文本的段落
            para = find_paragraph_with_text(doc, "Test Sample Information")
            if para:
                # 获取下一个段落
                next_range = para.Range.Next(4)  # wdParagraph = 4

                if next_range.Tables.Count > 0:
                    table = next_range.Tables(1)

                    for i in range(2, table.Rows.Count + 1):  # 跳过表头
                        try:
                            # 提取第一列（产品名称）
                            try:
                                first_col = get_table_cell_text(table, i, 1)
                            except Exception:
                                first_col = prev_first_col

                            # 提取第二列（料号）
                            try:
                                second_col = get_table_cell_text(table, i, 2)
                            except Exception:
                                second_col = ""

                            # 提取第三列（批次）
                            try:
                                third_col = get_table_cell_text(table, i, 3)
                            except Exception:
                                third_col = ""

                            # 提取第四列（基材）
                            try:
                                fourth_col = get_table_cell_text(table, i, 4)
                            except Exception:
                                fourth_col = ""

                            # 提取第五列（镀层）
                            try:
                                fifth_col = get_table_cell_text(table, i, 5)
                            except Exception:
                                fifth_col = ""

                            # 提取第六列（润滑油）
                            try:
                                sixth_col = get_table_cell_text(table, i, 6)
                            except Exception:
                                sixth_col = ""

                            # 提取第七列（塑材）
                            try:
                                seventh_col = get_table_cell_text(table, i, 7)
                            except Exception:
                                seventh_col = ""

                            prev_first_col = first_col

                            # 空行判断 - 如果前两列都为空则跳出
                            if not first_col and not second_col:
                                break

                            if first_col or second_col:
                                # 格式化包含所有列的信息
                                sample_info.append(f"{first_col}:{second_col}")
                                # 收集各列信息
                                if first_col:
                                    product_name.append(first_col)
                                if second_col:
                                    part_number.append(second_col)
                                if third_col:
                                    batch_info.append(third_col)
                                if fourth_col:
                                    substrate_info.append(fourth_col)
                                if fifth_col:
                                    plating_info.append(fifth_col)
                                if sixth_col:
                                    lubricant_info.append(sixth_col)
                                if seventh_col:
                                    plastic_info.append(seventh_col)
                                
                                logger.debug(f"处理样品表格行 {i}: 产品='{first_col}', 料号='{second_col}', 批次='{third_col}', 基材='{fourth_col}', 镀层='{fifth_col}', 润滑油='{sixth_col}', 塑材='{seventh_col}'")

                        except Exception as e:
                            logger.error(f"处理行 {i} 时出错: {e}")
        except Exception as e:
            logger.error(f"提取样品信息时出错: {e}")

        # 返回包含所有信息的字典
        result = {
            'sample_info_str': ";".join(sample_info),  # 保持原有格式
            'product_name': ";".join(product_name),         # 产品名称
            'part_number': ";".join(part_number),         # 料号
            'lot_info': ";".join(batch_info),               # 批次信息
            'base_material': ";".join(substrate_info),      # 基材信息
            'contact_plating': ";".join(plating_info),      # 接触镀层信息
            'contact_lubricant': ";".join(lubricant_info),  # 润滑油信息
            'housing_material': ";".join(plastic_info)       # 塑材信息
        }
        
        logger.debug(f"完成样品信息提取: {result}")
        return result
