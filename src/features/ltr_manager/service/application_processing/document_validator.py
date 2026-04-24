"""
LTR申请单验证模块
负责验证Word文档是否为有效的申请单以及版本号提取
"""

import os
import re
from typing import Tuple, Optional, Dict, Any

from src.core.logger import logger
from src.infrastructure.office.facade import OfficeFacade

class LTRApplicationFormValidator:
    """
    LTR申请单验证类
    负责验证Word文档是否为有效的申请单以及版本号提取
    """

    def __init__(self, office_facade: OfficeFacade | None = None):
        self.target_header_text = "Laboratory Testing Request"
        self.target_footer_rev_pattern = r"Rev\s*([A-Za-z0-9]+)"
        self._office_facade = office_facade or OfficeFacade()

    def validate_application_form(self, doc_filepath: str) -> Dict[str, Any]:
        """
        校验 Word 文件是否为测试申请单，并在页脚提取版本号。

        Args:
            doc_filepath (str): Word 文件的完整路径 (.doc, .docx)。

        Returns:
            dict: 包含验证结果和版本号的字典
        """
        try:
            is_valid, version_number = self._validate_docx_application_form(doc_filepath)

            if is_valid:
                return {
                    "is_valid": True,
                    "version": version_number or ""
                }
            else:
                return {
                    "is_valid": False,
                    "error": "文档不包含足够的申请单特征信息"
                }
        except Exception as e:
            logger.error(f"验证申请单时出错: {e}")
            return {
                "is_valid": False,
                "error": f"验证申请单时出错: {str(e)}"
            }

    def _validate_docx_application_form(self, doc_filepath: str) -> Tuple[bool, Optional[str]]:
        """
        校验 Word 文件是否为测试申请单，并在页脚提取版本号。

        Args:
            doc_filepath (str): Word 文件的完整路径 (.doc, .docx)。

        Returns:
            tuple: (is_valid, version_number)
                   is_valid (bool): True 如果在首页页眉表格中找到 "**Laboratory Testing Request**"，False 否则。
                   version_number (str | None): 提取到的版本号字符串 (例如 "H" 或 "G" 或 "A2")，如果在首页页脚的段落或表格中找到 Rev 并成功提取，则返回该版本号，否则为 None。
        """
        if not os.path.exists(doc_filepath):
            logger.error(f"Error: File not found at path: {doc_filepath}")
            return False, None

        try:
            def _validate_document(doc):
                is_valid = False
                extracted_version = None

                if not doc.Sections:
                    logger.warning(f"Document: {os.path.basename(doc_filepath)} has no sections. Cannot check headers/footers.")
                    return False, None

                first_section = doc.Sections(1)  # Word COM中索引从1开始

                # --- Check Header Table in the first section ---
                logger.debug("Checking headers in the first section for validation text.")
                found_header_valid_text = False

                headers_to_check = []
                # 添加主页面页眉和首页页眉
                try:
                    if first_section.Headers(1).Exists:  # wdHeaderFooterPrimary
                        headers_to_check.append(first_section.Headers(1))
                    if first_section.Headers(2).Exists:  # wdHeaderFooterFirstPage
                        headers_to_check.append(first_section.Headers(2))
                except Exception as e:
                    logger.warning(f"无法访问页眉: {e}")

                for header in headers_to_check:
                    if header:
                        for table in header.Range.Tables:
                            for row in table.Rows:
                                for cell in row.Cells:
                                    cell_text = cell.Range.Text.strip()
                                    logger.debug(f"DEBUG: Header Table Cell Text (First Section): '{cell_text}'")
                                    if self.target_header_text in cell_text:
                                        found_header_valid_text = True
                                        logger.debug(
                                            f"Document: {os.path.basename(doc_filepath)} - Found '{self.target_header_text}' in header table cell of first section.")
                                        break
                                if found_header_valid_text:
                                    break
                            if found_header_valid_text:
                                break
                        if found_header_valid_text:
                            break

                is_valid = found_header_valid_text

                if not is_valid:
                    logger.info(
                        f"Document: {os.path.basename(doc_filepath)} - Header validation failed in first section. '{self.target_header_text}' not found in header tables. NOT considered a valid application form.")

                # --- Attempt to extract version from Footer Paragraphs first, then Tables ---
                logger.debug("Checking footers in the first section for version text (Paragraphs first, then Tables).")

                footers_to_check = []
                try:
                    if first_section.Footers(1).Exists:  # wdHeaderFooterPrimary
                        footers_to_check.append(first_section.Footers(1))
                    if first_section.Footers(2).Exists:  # wdHeaderFooterFirstPage
                        footers_to_check.append(first_section.Footers(2))
                except Exception as e:
                    logger.warning(f"无法访问页脚: {e}")

                found_footer_rev = False  # Flag to know if "Rev" pattern was found at all
                for footer in footers_to_check:
                    if footer:
                        # Check in paragraphs first
                        for paragraph in footer.Range.Paragraphs:
                            paragraph_text = paragraph.Range.Text.strip()
                            logger.debug(f"DEBUG: Footer Paragraph Text (First Section): '{paragraph_text}'")
                            match = re.search(self.target_footer_rev_pattern, paragraph_text)
                            if match:
                                found_footer_rev = True
                                extracted_version = match.group(1).strip()
                                logger.debug(
                                    f"Document: {os.path.basename(doc_filepath)} - Found 'Rev' and extracted version '{extracted_version}' from footer PARAGRAPH.")
                                # Found in paragraph, we can stop checking paragraphs and tables for this footer type
                                break
                        # If not found in paragraphs of this specific footer type, check tables
                        if not found_footer_rev:
                            for table in footer.Range.Tables:
                                for row in table.Rows:
                                    for cell in row.Cells:
                                        cell_text = cell.Range.Text.strip()
                                        logger.debug(f"DEBUG: Footer Table Cell Text (First Section): '{cell_text}'")
                                        match = re.search(self.target_footer_rev_pattern, cell_text)
                                        if match:
                                            found_footer_rev = True
                                            extracted_version = match.group(1).strip()
                                            logger.debug(
                                                f"Document: {os.path.basename(doc_filepath)} - Found 'Rev' and extracted version '{extracted_version}' from footer TABLE cell.")
                                            # Found in table, we can stop checking tables for this footer type
                                            break
                                    if found_footer_rev:
                                        break  # Breaks row search
                                if found_footer_rev:
                                    break  # Breaks table search

                    # Break from footer type loop if found in either paragraphs or tables of this footer type
                    if found_footer_rev:
                        break

                if not found_footer_rev:
                    logger.info(
                        f"Document: {os.path.basename(doc_filepath)} - 'Rev' text pattern not found in footer paragraphs or tables of the first section.")

                # Final logging based on the results
                if is_valid:
                    logger.info(
                        f"Document: {os.path.basename(doc_filepath)} - Validated as application form (Header OK in first section). Version found: {extracted_version}")
                else:
                    logger.info(
                        f"Document: {os.path.basename(doc_filepath)} - NOT validated as application form (Header missing in first section). Version found (if any): {extracted_version}")

                return is_valid, extracted_version
            
            # 完全托付给 OfficeFacade 管理生命周期
            result = self._office_facade.with_word_document(
                doc_filepath,
                _validate_document,
                read_only=True,
                save=False,
            )
            
            return result

        except Exception as e:
            logger.error(f"An unexpected error occurred while processing Docx file {doc_filepath}: {e}", exc_info=True)
            return False, None
