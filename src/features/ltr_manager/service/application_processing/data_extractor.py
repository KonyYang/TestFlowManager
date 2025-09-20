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
        logger.info(f"Processing application file: {doc_filepath}")
        extracted_data = {}

        # 检查文件是否存在
        if not os.path.exists(doc_filepath):
            logger.error(f"File not found: {doc_filepath}")
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

            # 提取测试样品信息
            sample_info = self._extract_test_sample_info(doc)
            extracted_data['sample_information'] = sample_info

            # 提取测试要求信息
            testing_info = self._extract_requested_testing_info(doc)
            extracted_data['tests_to_be_performed'] = testing_info.get('tests_to_be_performed', '')
            extracted_data['applicable_specifications'] = testing_info.get('applicable_specifications', '')

            # 填充其他字段
            for field in ['project_leader', 'failed_item', 'sample_deposition',
                          'test_fee', 'remarks_po', 'start_test_date', 'finish_test_date',
                          'report_date']:
                extracted_data[field] = ""

            # 添加文件路径字段
            extracted_data['file_path'] = doc_filepath

            logger.info("Successfully processed application file")
            return extracted_data

        except Exception as e:
            logger.error(f"Error processing application file: {e}", exc_info=True)
            return {
                "error": f"处理申请单文件时出错: {str(e)}",
                "partial_data": extracted_data
            }
        finally:
            # 关闭文档
            try:
                doc.Close(SaveChanges=False)
            except Exception as e:
                logger.warning(f"Failed to close document: {e}")

    def _extract_requested_testing_info(self, doc) -> Dict[str, str]:
        """
        提取测试描述信息

        Args:
            doc: Word文档对象

        Returns:
            dict: 包含测试信息的字典
        """
        logger.debug("Extracting requested testing info...")
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

                        except Exception as e:
                            logger.error(f"Error processing row {i}: {e}")
        except Exception as e:
            logger.error(f"Error extracting testing info: {e}")

        return result

    def _extract_test_sample_info(self, doc) -> str:
        """
        提取测试样品信息

        Args:
            doc: Word文档对象

        Returns:
            str: 格式化的样品信息
        """
        logger.debug("Extracting test sample info...")
        sample_info = []
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

                            prev_first_col = first_col

                            # 空行判断
                            if not first_col and not second_col:
                                break

                            if first_col or second_col:
                                sample_info.append(f"{first_col}:{second_col}")

                        except Exception as e:
                            logger.error(f"Error processing row {i}: {e}")
        except Exception as e:
            logger.error(f"Error extracting sample info: {e}")

        formatted_result = ";".join(sample_info)
        return formatted_result
