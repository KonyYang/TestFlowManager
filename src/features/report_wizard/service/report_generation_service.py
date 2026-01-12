"""
报告生成服务模块
提供报告生成相关的业务逻辑服务
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pythoncom
from src.core.logger import logger
from src.features.report_wizard.service.header_modifier import HeaderModifier
from src.utils.word_utils import open_docx_document, save_docx_document
from src.features.report_wizard.model.header_data import HeaderData


class ReportGenerationService:
    """
    报告生成服务类
    提供报告生成相关的业务逻辑服务
    """

    def __init__(self):
        """初始化报告生成服务"""
        self.template_path = r"D:\TestFlowManager\Template\E-3707_H Laboratory Test Report_241216.docx"
        self.default_output_dir = r"D:\outfile"
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        import re
        # 替换Windows文件名中的非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(illegal_chars, '_', filename)
        return sanitized

    def validate_template_exists(self) -> bool:
        """
        验证模板文件是否存在
        
        Returns:
            bool: 模板文件是否存在
        """
        if not os.path.exists(self.template_path):
            logger.error(f"模板文件不存在: {self.template_path}")
            return False
        return True

    def create_report_from_template(self, header_data: HeaderData, output_dir: Optional[str] = None, project_path: Optional[str] = None) -> str:
        """
        基于模板创建报告文件
        
        Args:
            header_data: 页眉数据
            output_dir: 输出目录，如果为None则使用默认目录
            project_path: 项目路径，用于确定保存位置
            
        Returns:
            str: 生成的报告文件路径
        """
        try:
            logger.info(f"开始创建报告，页眉数据: {header_data}")
            
            # 验证模板文件
            if not self.validate_template_exists():
                raise FileNotFoundError(f"模板文件不存在: {self.template_path}")

            # 确定输出目录
            logger.info(f"项目路径(project_path): {project_path}")
            logger.info(f"项目路径是否存在: {project_path and os.path.exists(project_path) if project_path else False}")
            logger.info(f"传入的输出目录(output_dir): {output_dir}")
            
            if project_path and os.path.exists(project_path):
                # 从项目路径中提取DL编号作为子文件夹名称
                import json
                from pathlib import Path
                
                # 查找项目中的JSON文件以获取DL编号
                json_files = list(Path(project_path).glob("*.json"))
                logger.info(f"在项目路径中找到的JSON文件: {json_files}")
                
                if json_files:
                    json_file_path = json_files[0]
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                        dl_number = project_data.get("DL", "")
                        logger.info(f"从JSON文件中获取的DL编号: {dl_number}")
                        
                        if dl_number:
                            # 在项目路径下查找以DL编号开头的子文件夹
                            matching_folders = [f for f in os.listdir(project_path) 
                                              if os.path.isdir(os.path.join(project_path, f)) 
                                              and f.startswith(dl_number)]
                            
                            if matching_folders:
                                # 如果找到匹配的文件夹，使用第一个
                                output_dir = os.path.join(project_path, matching_folders[0])
                                logger.info(f"找到以DL编号开头的文件夹: {output_dir}")
                            else:
                                # 如果没找到匹配的文件夹，使用项目文件夹本身
                                logger.info(f"未找到以DL编号开头的文件夹，使用项目路径本身: {project_path}")
                                output_dir = project_path
                        else:
                            # 如果JSON中没有DL字段，使用项目路径本身
                            logger.info(f"JSON中未找到DL字段，使用项目路径本身: {project_path}")
                            output_dir = project_path
                else:
                    # 如果找不到JSON文件，使用项目路径本身
                    logger.info(f"项目路径中未找到JSON文件，使用项目路径本身")
                    output_dir = project_path
            else:
                # 如果没有项目路径，使用默认输出目录
                logger.info(f"没有项目路径，使用默认输出目录")
                output_dir = self.default_output_dir if output_dir is None else output_dir
            
            logger.info(f"最终确定的输出目录: {output_dir}")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            # 生成输出文件名
            # 根据要求，格式为：报告编号 报告标题 Report_Rev_版本号
            if header_data.report_no and header_data.report_title:
                # 获取版本号，如果没有则默认为A
                version = header_data.version if header_data.version else "A"
                # 替换版本号中的"Rev."前缀（如果存在）
                version_clean = version.replace("Rev.", "").strip()
                filename = f"{header_data.report_no} {header_data.report_title} Report_Rev_{version_clean}.docx"
                # 清理文件名中的非法字符
                filename = self._sanitize_filename(filename)
            elif header_data.report_no:
                # 如果只有报告编号
                version = header_data.version if header_data.version else "A"
                version_clean = version.replace("Rev.", "").strip()
                filename = f"{header_data.report_no} Report_Rev_{version_clean}.docx"
                filename = self._sanitize_filename(filename)
            else:
                # 如果没有报告编号，使用时间戳
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Test_Report_{timestamp}.docx"
            
            output_path = os.path.join(output_dir, filename)
            
            # 规范化路径以避免斜杠问题
            output_path = os.path.normpath(output_path)
            template_path_normalized = os.path.normpath(self.template_path)

            # 复制模板到输出位置
            shutil.copy2(template_path_normalized, output_path)
            logger.info(f"模板已从 {self.template_path} 复制到: {output_path}")

            # 创建页眉修改器实例
            # 使用规范化路径
            header_modifier = HeaderModifier(output_path)
            try:
                # 打开文档进行修改
                header_modifier.doc = open_docx_document(output_path)
                
                # 准备页眉数据字典
                header_dict = {
                    "report_no": header_data.report_no,
                    "version": header_data.version,
                    "date": header_data.date,
                    "tester": header_data.tester,
                    "report_title": header_data.report_title,
                    "requested_by": header_data.requested_by,
                    "test_period": header_data.test_period,
                    "completion_date": header_data.report_date
                }
                
                # ----------------------------------
                # ✅ 第一步：使用 python-docx 填充文档内容（如正文表格等）
                # ----------------------------------
                logger.info("开始执行 python-docx 修改...")
                
                # 修改修订记录表格中的日期 (使用python-docx修改)
                success3 = header_modifier.modify_revision_record_date(header_dict, doc=header_modifier.doc)
                if success3:
                    logger.info("修订记录表格日期已成功修改")
                else:
                    logger.error("修订记录表格日期修改失败")
                
                # 修改正文中样品接收日期 (使用python-docx修改)
                # 添加date_lab_received_samples字段到header_dict
                header_dict["date_lab_received_samples"] = header_data.date_lab_received_samples
                success4 = header_modifier.modify_sample_received_date(header_dict, doc=header_modifier.doc)
                if success4:
                    logger.info("样品接收日期已成功修改")
                else:
                    logger.warning("样品接收日期修改失败，这可能是正常的，如果文档中没有相关段落")
                
                # ✅ 确保 python-docx 修改已保存，为 win32com 操作提供最新输入
                try:
                    save_docx_document(header_modifier.doc, output_path)  # 保存当前修改，确保 win32com 可读取
                    logger.info("✅ python-docx 修改已保存")
                except Exception as e:
                    logger.error(f"保存 python-docx 修改失败: {e}")
                    return False

                # ----------------------------------
                # ✅ 第二步：使用 win32com 进行页眉页脚操作
                # ----------------------------------
                logger.info("开始执行 win32com 修改...")
                
                # 修改首页页眉 (使用win32com修改)
                success = header_modifier.modify_header(header_dict)
                if success:
                    logger.info("首页页眉信息已成功修改")
                else:
                    logger.error("首页页眉信息修改失败")
                    return False

                # 修改第二节页眉 (使用win32com修改)
                success2 = header_modifier.modify_second_header(header_dict)
                if success2:
                    logger.info("第二节页眉信息已成功修改")
                else:
                    logger.error("第二节页眉信息修改失败")
                    return False

                # ----------------------------------
                # ✅ 第三步：保存所有修改内容
                # ----------------------------------
                logger.info("开始执行最终保存...")

                # 使用win32com打开文档并保存
                word_app = header_modifier.word_app
                if word_app is None:
                    from src.utils.word_utils import get_shared_word_app
                    word_app = get_shared_word_app()
                    if word_app is None:
                        logger.error("无法获取Word应用程序实例")
                        return False

                # 确保Word应用程序不可见
                word_app.Visible = False
                word_app.DisplayAlerts = False

                # 使用win32com打开最终文档并保存
                # 规范化路径以避免斜杠问题
                normalized_path = os.path.normpath(output_path)
                win_doc = word_app.Documents.Open(normalized_path)

                # 保存文档
                win_doc.Save()
                logger.info(f"✅ 文档已通过 win32com 成功保存至: {output_path}")

                # 关闭文档
                win_doc.Close(SaveChanges=False)

                logger.info("✅ 页眉修改步骤已完成，文档已保存")

            except Exception as e:
                logger.error(f"❌ 文档修改失败: {e}", exc_info=True)
                return False
            finally:
                # 尝试清理header_modifier资源
                try:
                    if header_modifier:
                        header_modifier.cleanup()
                except:
                    pass  # 如果清理失败，则跳过
                
                # 确保Word应用程序在操作完成后正确关闭
                try:
                    if 'word_app' in locals() and word_app is not None:
                        # 关闭所有文档
                        for doc in word_app.Documents:
                            try:
                                doc.Close(SaveChanges=False)
                            except:
                                pass
                        # 退出Word应用
                        word_app.Quit()
                        logger.debug("Word application quit after report generation")
                except Exception as e:
                    logger.error(f"关闭Word应用程序时出错: {e}")
                
            pythoncom.CoUninitialize()

            return output_path

        except Exception as e:
            logger.error(f"创建报告失败: {e}")
            raise

    def __del__(self):
        """
        析构函数，确保Word应用程序资源被正确释放
        """
        try:
            # 通常不需要在此服务中直接管理Word应用实例
            # 因为使用的是共享实例，由word_utils模块统一管理
            logger.debug("ReportGenerationService: 已初始化清理")
        except Exception as e:
            logger.error(f"在析构函数中清理资源时出错: {e}")

    def load_project_data(self, project_path: str) -> Optional[HeaderData]:
        """
        从项目路径加载项目数据
        
        Args:
            project_path: 项目路径
            
        Returns:
            HeaderData: 从项目中加载的页眉数据，如果失败则返回None
        """
        try:
            # 查找项目中的JSON文件
            project_dir = Path(project_path)
            json_files = list(project_dir.glob("*.json"))
            
            if not json_files:
                logger.warning(f"在项目路径中未找到JSON文件: {project_path}")
                return None
            
            # 使用第一个找到的JSON文件
            json_file = json_files[0]
            with open(json_file, 'r', encoding='utf-8') as f:
                import json
                json_data = json.load(f)
                
                # 从JSON数据创建HeaderData对象
                header_data = HeaderData.from_json(json_data)
                logger.info(f"成功从 {json_file} 加载项目数据")
                return header_data
                
        except Exception as e:
            logger.error(f"加载项目数据失败: {e}")
            return None

    def get_generated_report_path(self, header_data: HeaderData, output_dir: Optional[str] = None, project_path: Optional[str] = None) -> str:
        """
        获取将要生成的报告文件路径（不实际生成文件）
        
        Args:
            header_data: 页眉数据
            output_dir: 输出目录，如果为None则使用默认目录
            project_path: 项目路径，用于确定保存位置
            
        Returns:
            str: 将要生成的报告文件路径
        """
        try:
            # 确定输出目录
            logger.info(f"项目路径(project_path): {project_path}")
            logger.info(f"项目路径是否存在: {project_path and os.path.exists(project_path) if project_path else False}")
            logger.info(f"传入的输出目录(output_dir): {output_dir}")
            
            if project_path and os.path.exists(project_path):
                # 从项目路径中提取DL编号作为子文件夹名称
                import json
                from pathlib import Path
                
                # 查找项目中的JSON文件以获取DL编号
                json_files = list(Path(project_path).glob("*.json"))
                logger.info(f"在项目路径中找到的JSON文件: {json_files}")
                
                if json_files:
                    json_file_path = json_files[0]
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                        dl_number = project_data.get("DL", "")
                        logger.info(f"从JSON文件中获取的DL编号: {dl_number}")
                        
                        if dl_number:
                            # 在项目路径下查找以DL编号开头的子文件夹
                            matching_folders = [f for f in os.listdir(project_path) 
                                              if os.path.isdir(os.path.join(project_path, f)) 
                                              and f.startswith(dl_number)]
                            
                            if matching_folders:
                                # 如果找到匹配的文件夹，使用第一个
                                output_dir = os.path.join(project_path, matching_folders[0])
                                logger.info(f"找到以DL编号开头的文件夹: {output_dir}")
                            else:
                                # 如果没找到匹配的文件夹，使用项目文件夹本身
                                logger.info(f"未找到以DL编号开头的文件夹，使用项目路径本身: {project_path}")
                                output_dir = project_path
                        else:
                            # 如果JSON中没有DL字段，使用项目路径本身
                            logger.info(f"JSON中未找到DL字段，使用项目路径本身: {project_path}")
                            output_dir = project_path
                else:
                    # 如果找不到JSON文件，使用项目路径本身
                    logger.info(f"项目路径中未找到JSON文件，使用项目路径本身")
                    output_dir = project_path
            else:
                # 如果没有项目路径，使用默认输出目录
                logger.info(f"没有项目路径，使用默认输出目录")
                output_dir = self.default_output_dir if output_dir is None else output_dir
            
            logger.info(f"最终确定的输出目录: {output_dir}")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            # 生成输出文件名
            # 根据要求，格式为：报告编号 报告标题 Report_Rev_版本号
            if header_data.report_no and header_data.report_title:
                # 获取版本号，如果没有则默认为A
                version = header_data.version if header_data.version else "A"
                # 替换版本号中的"Rev."前缀（如果存在）
                version_clean = version.replace("Rev.", "").strip()
                filename = f"{header_data.report_no} {header_data.report_title} Report_Rev_{version_clean}.docx"
                # 清理文件名中的非法字符
                filename = self._sanitize_filename(filename)
            elif header_data.report_no:
                # 如果只有报告编号
                version = header_data.version if header_data.version else "A"
                version_clean = version.replace("Rev.", "").strip()
                filename = f"{header_data.report_no} Report_Rev_{version_clean}.docx"
                filename = self._sanitize_filename(filename)
            else:
                # 如果没有报告编号，使用时间戳
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Test_Report_{timestamp}.docx"
            
            output_path = os.path.join(output_dir, filename)
            
            # 规范化路径以避免斜杠问题
            output_path = os.path.normpath(output_path)
            return output_path

        except Exception as e:
            logger.error(f"获取报告路径失败: {e}")
            raise