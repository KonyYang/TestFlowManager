# src/features/test_record_generator/controller/test_record_controller.py
"""
Test Record生成控制器
控制Test Record生成功能的业务流程
"""

from src.features.test_record_generator.service.test_record_service import TestRecordService
from src.core.logger import logger
from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
from PyQt5.QtWidgets import QMessageBox, QFileDialog
import os
import re


class TestRecordController:
    """
    Test Record生成控制器
    """

    def __init__(self, matrix_service=None):
        self.service = TestRecordService()
        self.matrix_service = matrix_service  # 关联的Matrix服务

    def _get_default_output_path(self, dl_number, project_data_file_path):
        """
        根据项目路径和DL编号生成默认输出路径
        
        Args:
            dl_number: DL编号
            project_data_file_path: 项目数据文件路径
            
        Returns:
            默认输出路径
        """
        try:
            # 如果有项目数据文件路径，则基于该项目路径构建输出路径
            if project_data_file_path and os.path.exists(project_data_file_path):
                # 获取项目根目录（DL编号所在的文件夹）
                project_root_dir = os.path.dirname(project_data_file_path)
                
                # 查找项目根目录下以DL编号开头的子文件夹
                dl_subfolder_path = None
                if os.path.exists(project_root_dir):
                    # 列出项目根目录中的所有文件夹，并按名称排序确保一致性
                    items = sorted(os.listdir(project_root_dir))
                    for item in items:
                        item_path = os.path.join(project_root_dir, item)
                        # 检查是否为目录且以DL编号开头
                        if os.path.isdir(item_path) and item.startswith(dl_number):
                            dl_subfolder_path = item_path
                            break
                
                # 如果没找到匹配的文件夹，则使用项目根目录
                if not dl_subfolder_path:
                    dl_subfolder_path = project_root_dir
                
                # 在DL编号文件夹下查找Submitted Material子文件夹
                submitted_material_path = os.path.join(dl_subfolder_path, "Submitted Material")
                # 标准化路径分隔符
                submitted_material_path = os.path.normpath(submitted_material_path)
                
                # 检查Submitted Material文件夹是否存在，如果不存在则创建
                if not os.path.exists(submitted_material_path):
                    try:
                        os.makedirs(submitted_material_path)
                        logger.info(f"创建Submitted Material文件夹: {submitted_material_path}")
                    except Exception as e:
                        logger.error(f"创建Submitted Material文件夹失败: {e}")
                        # 如果创建失败，使用DL编号文件夹作为替代
                        submitted_material_path = dl_subfolder_path
                
                # 在Submitted Material文件夹中生成文件
                output_filename = f"{dl_number} Test Record.docx"
                output_path = os.path.join(submitted_material_path, output_filename)
                logger.debug(f"构造的默认输出路径: {output_path}")
                return os.path.normpath(output_path)  # 标准化路径分隔符
            
            # 如果没有项目数据文件路径，则使用默认路径
            return r"D:\outfile\testrecord.docx"
        except Exception as e:
            logger.error(f"生成默认输出路径时出错: {e}")
            return r"D:\outfile\testrecord.docx"

    def generate_test_record(self, parent=None):
        """
        生成Test Record文档
        
        Args:
            parent: 父窗口
            
        Returns:
            是否成功生成
        """
        try:
            # 获取Matrix数据
            if self.matrix_service:
                matrix_data = self.matrix_service.data_model.rows
                logger.debug(f"获取到Matrix数据，共 {len(matrix_data)} 行")
                
                # 创建MatrixDataStructure实例来解析数据
                matrix_structure = MatrixDataStructure()
                
                # 尝试获取DL编号和项目数据文件路径
                dl_number = "DL-UNKNOWN"
                project_data_file_path = None
                
                # 从Matrix服务获取项目数据文件路径
                if hasattr(self.matrix_service, 'project_data_file_path') and self.matrix_service.project_data_file_path:
                    project_data_file_path = self.matrix_service.project_data_file_path
                    logger.debug(f"从Matrix服务获取到项目数据文件路径: {project_data_file_path}")
                    
                    # 从项目数据文件中提取DL编号
                    if os.path.exists(project_data_file_path):
                        try:
                            import json
                            with open(project_data_file_path, 'r', encoding='utf-8') as f:
                                project_data = json.load(f)
                                dl_number = project_data.get("DL", dl_number)
                                logger.debug(f"从项目数据文件中提取到DL编号: {dl_number}")
                        except Exception as e:
                            logger.error(f"读取项目数据文件时出错: {e}")
                else:
                    # 如果Matrix服务中没有项目数据文件路径，尝试从状态管理器获取
                    from src.core.state_manager import state_manager
                    current_project = state_manager.get_state("current_project")
                    logger.debug(f"从状态管理器获取到当前项目路径: {current_project}")
                    
                    if current_project and os.path.exists(current_project):
                        # 在当前项目路径中查找JSON文件
                        try:
                            json_files = [f for f in os.listdir(current_project) if f.endswith('.json')]
                            if json_files:
                                project_data_file_path = os.path.join(current_project, json_files[0])
                                logger.debug(f"在当前项目路径中找到JSON文件: {project_data_file_path}")
                                
                                # 从项目数据文件中提取DL编号
                                if os.path.exists(project_data_file_path):
                                    try:
                                        import json
                                        with open(project_data_file_path, 'r', encoding='utf-8') as f:
                                            project_data = json.load(f)
                                            dl_number = project_data.get("DL", dl_number)
                                            logger.debug(f"从项目数据文件中提取到DL编号: {dl_number}")
                                    except Exception as e:
                                        logger.error(f"读取项目数据文件时出错: {e}")
                            else:
                                # 如果当前目录没有找到JSON文件，则在父目录查找
                                parent_path = os.path.dirname(current_project)
                                logger.debug(f"在父目录中查找JSON文件: {parent_path}")
                                
                                if os.path.exists(parent_path):
                                    json_files = [f for f in os.listdir(parent_path) if f.endswith('.json')]
                                    logger.debug(f"在父目录 {parent_path} 中找到的JSON文件: {json_files}")
                                    
                                    if json_files:
                                        # 使用父目录中的JSON文件
                                        project_data_file_path = os.path.join(parent_path, json_files[0])
                                        logger.debug(f"构造的项目数据文件路径: {project_data_file_path}")
                                        
                                        # 从项目数据文件中提取DL编号
                                        if os.path.exists(project_data_file_path):
                                            try:
                                                import json
                                                with open(project_data_file_path, 'r', encoding='utf-8') as f:
                                                    project_data = json.load(f)
                                                    dl_number = project_data.get("DL", dl_number)
                                                    logger.debug(f"从项目数据文件中提取到DL编号: {dl_number}")
                                            except Exception as e:
                                                logger.error(f"读取项目数据文件时出错: {e}")
                        except Exception as e:
                            logger.error(f"查找项目中的JSON文件时出错: {e}")
                
                matrix_structure.dl_number = dl_number
                matrix_structure.project_data_file_path = project_data_file_path
                logger.debug(f"设置DL编号: {dl_number}")
                logger.debug(f"设置项目数据文件路径: {project_data_file_path}")
                
                # 根据项目路径和DL编号生成默认输出路径
                default_output_path = self._get_default_output_path(dl_number, project_data_file_path)
                logger.debug(f"默认输出路径: {default_output_path}")
                
                # 检查默认路径是否有效
                default_dir = os.path.dirname(default_output_path)
                if not os.path.exists(default_dir):
                    # 如果默认路径无效，显示警告并让用户选择路径
                    msg_box = QMessageBox(parent)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("路径问题")
                    msg_box.setText(f"无法找到正确的项目文件夹，无法自动保存Test Record文档。\n\n默认路径: {default_output_path}\n\n请手动选择保存位置。")
                    msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    result = msg_box.exec_()
                    
                    if result == QMessageBox.Cancel:
                        logger.info("用户取消了Test Record生成操作")
                        return False
                    
                    # 让用户选择保存路径
                    output_path, _ = QFileDialog.getSaveFileName(
                        parent, 
                        "保存Test Record文档", 
                        f"{dl_number} Test Record.docx", 
                        "Word文档 (*.docx)"
                    )
                    
                    if not output_path:
                        logger.info("用户未选择保存路径，取消Test Record生成操作")
                        return False
                else:
                    # 使用默认路径
                    output_path = default_output_path
                
                # 标准化路径分隔符
                output_path = os.path.normpath(output_path)
                
                # 确保输出目录存在
                output_dir = os.path.dirname(output_path)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                warnings = matrix_structure.parse_matrix_to_structure(matrix_data)
                
                # 记录解析结果
                group_count = len(matrix_structure.group_steps)
                logger.debug(f"解析完成，共找到 {group_count} 个组别")
                
                # 如果有警告信息，显示给用户并阻止继续
                if warnings:
                    warning_text = "\n".join(warnings)
                    logger.warning(f"Matrix数据验证警告:\n{warning_text}")
                    
                    # 显示警告对话框，只用一个确认按钮
                    if parent:
                        msg_box = QMessageBox(parent)
                        msg_box.setIcon(QMessageBox.Warning)
                        msg_box.setWindowTitle("数据验证警告")
                        msg_box.setText(f"发现以下数据问题：\n\n{warning_text}")
                        msg_box.setStandardButtons(QMessageBox.Ok)
                        msg_box.exec_()
                        
                        logger.debug("用户已确认警告信息，返回Matrix编辑界面")
                        return False  # 阻止继续生成Test Record
                
                logger.debug("Matrix数据结构已更新")
                
                # 调用服务生成文档，传入已解析的数据结构
                logger.debug("开始调用Test Record服务生成文档")
                success = self.service.generate_test_record_with_structure(matrix_structure, output_path)
                
                if success:
                    logger.info("Test Record文档生成成功")
                    # 显示成功消息
                    if parent:
                        QMessageBox.information(parent, "成功", f"Test Record文档已成功生成并保存到:\n{output_path}")
                else:
                    logger.error("Test Record文档生成失败")
                    
                return success
            else:
                logger.error("Matrix service not available")
                return False
                
        except Exception as e:
            logger.error(f"Error in test record generation controller: {e}")
            return False