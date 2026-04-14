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
from src.core.config_manager import config_manager
from src.core.logger import logger
from src.core.output_paths import OutputPathResolver
from src.core.project_context import ProjectContext
from src.core.project_document_context import ProjectDocumentContext
from src.features.report_wizard.service.header_modifier import HeaderModifier
from src.utils.word_utils import open_docx_document, save_docx_document, get_shared_word_app
from src.features.report_wizard.model.header_data import HeaderData
from src.features.report_wizard.service.test_spec_tables_service import TestSpecTablesService


class ReportGenerationService:
    """
    报告生成服务类
    提供报告生成相关的业务逻辑服务
    """

    def __init__(self):
        """初始化报告生成服务"""
        self.template_dir = config_manager.get_template_dir()
        self.default_output_dir = OutputPathResolver.get_default_output_dir()
    
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

    def _find_template_file(self) -> Optional[str]:
        """
        查找以"E-3707"开头的.docx模板文件
        
        Returns:
            模板文件路径，如果未找到则返回None
        """
        try:
            if not os.path.exists(self.template_dir):
                logger.error(f"模板目录不存在: {self.template_dir}")
                return None

            # 查找以"E-3707"开头的.docx文件
            template_files = [f for f in os.listdir(self.template_dir) 
                            if os.path.isfile(os.path.join(self.template_dir, f)) and 
                            f.startswith("E-3707") and 
                            f.endswith('.docx')]
            
            if template_files:
                # 返回第一个找到的模板文件
                template_path = os.path.join(self.template_dir, template_files[0])
                logger.info(f"找到模板文件: {template_path}")
                return template_path
            else:
                logger.warning(f"未找到以'E-3707'开头的.docx模板文件在目录: {self.template_dir}")
                return None
        except Exception as e:
            logger.error(f"查找模板文件时出错: {e}")
            return None

    def validate_template_exists(self) -> bool:
        """
        验证模板文件是否存在
        
        Returns:
            bool: 模板文件是否存在
        """
        template_path = self._find_template_file()
        if not template_path:
            logger.error(f"未找到以'E-3707'开头的模板文件")
            return False
        self.template_path = template_path  # 设置找到的模板路径
        return True

    def _resolve_output_dir(
        self,
        output_dir: Optional[str] = None,
        project_context: Optional[ProjectContext] = None,
    ) -> str:
        if output_dir:
            return output_dir

        if project_context and os.path.exists(project_context.project_path):
            # 报告应输出到项目工作空间目录(与费用表、客户反馈表同级)
            # 而不是 Submitted Material 子目录
            resolved_dir = OutputPathResolver.resolve_project_workspace_dir(
                project_context,
                create=True,
            )
            if resolved_dir != OutputPathResolver.get_default_output_dir():
                logger.info(f"使用项目输出目录: {resolved_dir}")
            else:
                logger.info("没有解析到项目工作空间目录，回退全局默认输出目录")
            return resolved_dir

        logger.info("没有项目上下文，使用默认输出目录")
        return self.default_output_dir

    def _load_project_json_data(
        self,
        project_context: Optional[ProjectContext] = None,
    ) -> Optional[Dict[str, Any]]:
        if project_context is None:
            return None

        document_context = ProjectDocumentContext.from_project_context(project_context)
        if document_context.project_data:
            return document_context.project_data
        return None

    def create_report_from_template(
        self,
        header_data: HeaderData,
        output_dir: Optional[str] = None,
        project_context: Optional[ProjectContext] = None,
    ) -> str:
        """
        基于模板创建报告文件
        
        Args:
            header_data: 页眉数据
            output_dir: 输出目录，如果为None则使用默认目录
            project_context: 项目上下文，用于确定保存位置
            
        Returns:
            str: 生成的报告文件路径
        """
        try:
            logger.info(f"开始创建报告，页眉数据: {header_data}")
            
            # 验证模板文件 - 现在会动态查找
            if not self.validate_template_exists():
                raise FileNotFoundError(f"未找到以'E-3707'开头的模板文件")

            output_dir = self._resolve_output_dir(
                output_dir=output_dir,
                project_context=project_context,
            )
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

            # 确保目标文件未被占用，等待并重试
            max_retries = 5
            retry_delay = 1  # 秒
            for attempt in range(max_retries):
                try:
                    # 检查目标文件是否存在并尝试访问
                    if os.path.exists(output_path):
                        # 尝试重命名文件以检查是否被占用
                        temp_path = output_path + ".tmp_check"
                        os.rename(output_path, temp_path)
                        os.rename(temp_path, output_path)  # 恢复原名
                    
                    # 如果到达这里，说明文件未被占用，可以安全复制
                    shutil.copy2(template_path_normalized, output_path)
                    logger.info(f"模板已从 {self.template_path} 复制到: {output_path}")
                    break  # 成功复制，跳出循环
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"文件访问被拒绝，等待 {retry_delay} 秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        logger.error(f"复制模板文件失败，已达到最大重试次数: {e}")
                        raise

            # 创建页眉修改器实例
            # 使用规范化路径
            header_modifier = HeaderModifier(output_path)
            try:
                # 使用win32com打开文档
                header_modifier.word_app = get_shared_word_app()
                if header_modifier.word_app is None:
                    logger.error("无法获取Word应用程序实例")
                    return False
                header_modifier.word_app.Visible = False
                header_modifier.word_app.DisplayAlerts = False
                
                # 打开文档进行修改
                header_modifier.win_document = header_modifier.word_app.Documents.Open(os.path.normpath(output_path))

                # 准备页眉数据字典
                header_dict = {
                    "report_no": header_data.report_no,
                    "version": header_data.version,
                    "date": header_data.date,
                    "tester": header_data.tester,
                    "report_title": header_data.report_title,
                    "requested_by": header_data.requested_by,
                    "test_period": header_data.test_period,
                    "completion_date": header_data.report_date,
                    "date_lab_received_samples": header_data.date_lab_received_samples
                }

                # ----------------------------------
                # ✅ 使用 win32com 修改所有内容
                # ----------------------------------
                logger.info("开始执行 win32com 修改...")

                # 修改首页页眉 (使用win32com修改)
                success1 = header_modifier.modify_header(header_dict)
                if success1:
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
                # 修改修订记录表格中的日期 (使用win32com修改)
                success3 = header_modifier.modify_revision_record_date_win32com(header_dict)
                if success3:
                    logger.info("修订记录表格日期已成功修改")
                else:
                    logger.error("修订记录表格日期修改失败")

                # 修改正文 (使用win32com修改)，根据是否有项目数据决定调用哪个方法
                project_data = self._load_project_json_data(project_context)
                if project_data:
                    project_path_display = project_context.project_path if project_context else "unknown"
                    logger.info(f"项目已打开: {project_path_display}，检查JSON文件...")
                    success4 = header_modifier.update_document_content(project_data)
                else:
                    logger.info("项目未打开，使用传统方式调用modify_sample_received_date")
                    # 没有项目数据时，使用传统方式
                    success4 = header_modifier._modify_sample_received_date_fallback(output_path)

                if success4:
                    logger.info("样品接收日期已成功修改")
                else:
                    logger.warning("样品接收日期修改失败，这可能是正常的，如果文档中没有相关段落")

                # 填充测试样品信息表格
                try:
                    # 创建TestSpecTablesService实例来填充测试样品信息表格
                    test_spec_service = TestSpecTablesService()

                    # 从项目数据中提取测试样品信息
                    project_data = self._load_project_json_data(project_context)

                    if project_data:
                        logger.info("开始填充测试样品信息表格...")
                        # 传递Word应用程序实例和文档实例，确保它们存在
                        word_app_to_pass = header_modifier.word_app
                        word_doc_to_pass = header_modifier.win_document
                        sample_info_result = test_spec_service.fill_test_sample_info_table_from_json(
                            document_path=output_path,
                            json_data=project_data,
                            word_app_instance=word_app_to_pass,
                            word_doc_instance=word_doc_to_pass  # 传递Word文档实例以避免重复打开文档
                        )

                        if sample_info_result:
                            logger.info("测试样品信息表格填充完成")
                        else:
                            logger.error("测试样品信息表格填充失败")
                    else:
                        logger.info("未找到项目数据，跳过测试样品信息表格填充")
                except Exception as e:
                    logger.error(f"填充测试样品信息表格时出错: {e}")
                    import traceback
                    logger.error(f"错误堆栈: {traceback.format_exc()}")

                # ----------------------------------
                # ✅ 第二步：保存所有修改内容
                # ----------------------------------
                logger.info("开始执行最终保存...")
                try:
                    header_modifier.win_document.Save()
                    logger.info(f"✅ 文档已通过 win32com 成功保存至: {output_path}")
                except pythoncom.com_error as save_error:
                    logger.error(f"保存文档时出错: {save_error}")
                    # 检查COM对象是否仍然可用
                    try:
                        # 检查文档对象是否仍然有效
                        doc_name = header_modifier.win_document.Name  # 尝试访问文档属性来确认连接
                        header_modifier.win_document.Save()
                        logger.info(f"✅ 重新连接后保存文档成功")
                    except pythoncom.com_error as reconnect_error:
                        logger.error(f"重新连接并保存也失败: {reconnect_error}")
                        raise save_error

                # 关闭文档
                header_modifier.win_document.Close(SaveChanges=False)

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

                # 确保Word应用程序实例在操作完成后正确释放
                # 只有在创建了本地实例的情况下才释放（但在这个修改过的版本中我们使用的是共享实例）
                try:
                    # 不需要显式释放共享实例，因为它是全局管理的
                    # 如果需要确保COM资源释放，可以调用CoUninitialize
                    pass
                except Exception as e:
                    logger.error(f"释放Word实例时出错: {e}")

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

    def load_project_data(self, project_context: ProjectContext) -> Optional[HeaderData]:
        """
        从项目上下文加载项目数据
        
        Args:
            project_context: 项目上下文，用于获取 JSON
            
        Returns:
            HeaderData: 从项目中加载的页眉数据，如果失败则返回None
        """
        try:
            project_data = self._load_project_json_data(project_context=project_context)
            if not project_data:
                context_path = project_context.project_path if project_context else "unknown"
                logger.warning(f"在项目路径中未找到JSON数据: {context_path}")
                return None

            header_data = HeaderData.from_json(project_data)
            logger.info(f"成功从项目上下文加载项目数据: {project_context.project_path}")
            return header_data
                
        except Exception as e:
            logger.error(f"加载项目数据失败: {e}")
            return None

    def get_generated_report_path(
        self,
        header_data: HeaderData,
        output_dir: Optional[str] = None,
        project_context: Optional[ProjectContext] = None,
    ) -> str:
        """
        获取将要生成的报告文件路径（不实际生成文件）
        
        Args:
            header_data: 页眉数据
            output_dir: 输出目录，如果为None则使用默认目录
            project_context: 项目上下文，用于确定保存位置
            
        Returns:
            str: 将要生成的报告文件路径
        """
        try:
            output_dir = self._resolve_output_dir(
                output_dir=output_dir,
                project_context=project_context,
            )
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
