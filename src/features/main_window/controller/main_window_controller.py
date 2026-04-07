"""
主窗口控制器模块
处理主窗口的业务逻辑和事件
"""
import os
import json
from typing import List, Optional
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QFileDialog
from PyQt5.QtCore import QTimer
from src.core.logger import logger
from src.core.event_dispatcher import event_dispatcher
from src.features.ltr_manager.controller.ltr_editor_controller import LTREditorController
from src.features.main_window.model.main_window_data import MainWindowData
from src.features.main_window.service.main_window_service import MainWindowService
from src.features.ltr_manager.controller.ltr_viewer_controller import LTRViewerController
from src.features.main_window.view.dialogs.dl_input_dialog import DLInputDialog
from src.features.project_creator.controller import ProjectCreatorController
# 添加状态管理器
from src.core.state_manager import state_manager
# 添加Matrix相关导入
from src.features.matrix.controller.matrix_project_controller import MatrixProjectController


class MainWindowController:
    """
    主窗口控制器类
    处理主窗口的业务逻辑和事件
    """

    def __init__(self, view: QWidget):
        """
        初始化主窗口控制器

        Args:
            view: 主窗口视图实例
        """
        self.view = view
        self.data_model = MainWindowData()
        self.service = MainWindowService(self.data_model)

        # 初始化状态
        self.service.update_status("就绪")
        self.ltr_controller = LTRViewerController()
        # 使用LTR控制器的服务实例初始化LTR编辑器控制器
        self.ltr_editor_controller = LTREditorController(
            self.ltr_controller.data_model,
            self.ltr_controller.service
        )
        
        # 初始化Matrix项目控制器
        self.matrix_project_controller = MatrixProjectController(view)
        
        # 初始化当前项目路径
        self._current_project_path = None

        # 订阅事件
        event_dispatcher.subscribe("ltr.processing.started", self._on_ltr_processing_started)
        event_dispatcher.subscribe("ltr.processing.completed", self._on_ltr_processing_completed)
        event_dispatcher.subscribe("ltr.processing.failed", self._on_ltr_processing_failed)
        event_dispatcher.subscribe("state.changed", self._on_state_changed)
        event_dispatcher.subscribe("ltr.application.confirmed", self._on_ltr_application_confirmed)
        event_dispatcher.subscribe("ltr.application.processed", self._on_ltr_application_processed)
        event_dispatcher.subscribe("project.opened", self._on_project_opened)

    # 添加事件处理方法
    def _on_ltr_processing_started(self, data):
        """处理LTR处理开始事件"""
        file_path = data.get("file_path", "未知文件")
        self.service.update_status(f"正在处理LTR申请单: {os.path.basename(file_path)}")

    def _on_ltr_processing_completed(self, data):
        """处理LTR处理完成事件"""
        file_path = data.get("file_path", "未知文件")
        self.service.update_status(f"LTR申请单处理完成: {os.path.basename(file_path)}")

    def _on_ltr_processing_failed(self, data):
        """处理LTR处理失败事件"""
        file_path = data.get("file_path", "未知文件")
        error = data.get("error", "未知错误")
        self.service.update_status(f"LTR申请单处理失败: {os.path.basename(file_path)}")

    def _on_ltr_application_confirmed(self, data):
        """处理LTR申请单确认事件"""
        dl_number = data.get("dl_number")
        self.service.update_status(f"确认LTR申请单: {dl_number}")

    def _on_ltr_application_processed(self, data):
        """处理LTR申请单处理完成事件"""
        dl_number = data.get("dl_number")
        status = data.get("status")

        logger.debug(f"_on_ltr_application_processed in MainWindowController called with dl_number={dl_number}, status={status}")

        if status == "success":
            self.service.update_status(f"LTR申请单处理完成: {dl_number}")
            # 更新窗口标题显示项目信息
            logger.debug(f"Setting main window title in MainWindowController to: TestFlow Manager - 项目: {dl_number}")
            self.view.setWindowTitle(f"TestFlow Manager - 项目: {dl_number}")
            logger.debug(f"Main window title after setting in MainWindowController: {self.view.windowTitle()}")
            # 设置LTR编号到Matrix控制器
            if self.matrix_project_controller and self.matrix_project_controller.matrix_controller:
                self.matrix_project_controller.matrix_controller.set_ltr_number(dl_number)
                logger.debug(f"Set LTR number {dl_number} to Matrix controller")
        else:
            self.service.update_status(f"LTR申请单处理失败: {dl_number}")

    def _on_project_opened(self, data):
        """处理项目打开事件"""
        project_path = data.get("project_path")
        dl_number = data.get("dl_number")
        
        logger.debug(f"_on_project_opened called with project_path={project_path}, dl_number={dl_number}")
        
        if project_path and dl_number:
            # 更新状态
            self.service.update_status(f"当前项目: {dl_number}")
            
            # 更新窗口标题显示项目信息
            self.view.setWindowTitle(f"TestFlow Manager - 项目: {dl_number}")
            
            # 更新顶栏DL编号显示
            if hasattr(self.view, 'update_dl_number_display'):
                self.view.update_dl_number_display(dl_number)
            
            # 保存当前项目路径到控制器属性
            self._current_project_path = project_path
            
            # 设置LTR编号到Matrix控制器
            if self.matrix_project_controller and self.matrix_project_controller.matrix_controller:
                self.matrix_project_controller.matrix_controller.set_ltr_number(dl_number)
                logger.debug(f"Set LTR number {dl_number} to Matrix controller")
                
            # 触发Matrix自动导入功能
            QTimer.singleShot(0, self._trigger_matrix_auto_import)
            
            logger.info(f"Project opened successfully: {project_path} with DL number: {dl_number}")
            
            # 确保报告更新控制器的项目路径也被更新
            # 通过视图访问报告更新控制器并更新项目路径
            if hasattr(self.view, 'report_updater_controller'):
                self.view.report_updater_controller.set_project_path(project_path)

    def _on_state_changed(self, data):
        """处理状态变更事件"""
        key = data.get("key")
        new_value = data.get("new_value")

        # 根据不同的状态键进行相应处理
        if key == "current_project":
            self.service.update_status(f"当前项目: {new_value}")
            # 更新窗口标题显示项目信息
            if new_value:
                project_name = os.path.basename(new_value) if new_value else '无'
                self.view.setWindowTitle(f"TestFlow Manager - 项目: {project_name}")
                
            # 触发Matrix自动导入功能
            QTimer.singleShot(0, self._trigger_matrix_auto_import)
        elif key == "application_status":
            self.service.update_status(new_value)

    def _trigger_matrix_auto_import(self):
        """触发Matrix编辑器自动导入项目中的matrix.xlsx文件并更新显示"""
        try:
            # 调用主窗口的Matrix自动导入方法
            if hasattr(self.view, 'matrix_import_export_manager') and self.view.matrix_import_export_manager:
                self.view._matrix_auto_import_from_project()
                logger.debug("Triggered auto import of matrix.xlsx in MainWindow")
                
                # 延迟更新表格显示，确保数据已加载
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(50, self._update_matrix_display)
                
                # 切换回 Matrix 页面（索引为 0）
                QTimer.singleShot(100, self._switch_to_matrix_page)
        except Exception as e:
            logger.error(f"Failed to trigger matrix auto import: {e}")
    
    def _update_matrix_display(self):
        """更新 Matrix 表格显示"""
        try:
            if hasattr(self.view, '_matrix_update_table'):
                self.view._matrix_update_table()
                logger.debug("Successfully updated Matrix table display")
        except Exception as e:
            logger.error(f"Failed to update Matrix display: {e}")
    
    def _switch_to_matrix_page(self):
        """切换到 Matrix 编辑器页面"""
        try:
            # Matrix 编辑器是第一个页面，索引为 0
            if hasattr(self.view, '_nav_list') and self.view._nav_list:
                self.view._nav_list.setCurrentRow(0)
                logger.debug("Switched to Matrix editor page (index 0)")
        except Exception as e:
            logger.error(f"Failed to switch to Matrix page: {e}")

    def initialize(self) -> bool:
        """
        初始化控制器

        Returns:
            初始化是否成功
        """
        try:
            logger.info("Initializing MainWindowController")

            # 加载应用程序状态
            self.service.load_application_state()

            # 加载最近文件列表
            recent_files = self.service.load_recent_files()
            logger.info(f"Loaded {len(recent_files)} recent files")

            logger.info("MainWindowController initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MainWindowController: {e}")
            return False

    def handle_view_ltr(self) -> bool:
        """
        处理查看LTR文件事件

        Returns:
            是否成功打开LTR文件
        """
        try:
            logger.debug("Handling view LTR file request from main window")

            # 显示DL编号输入对话框
            dialog = DLInputDialog(self.view)
            result = dialog.exec_()

            # 如果用户点击取消，则直接返回
            if result != QDialog.Accepted:
                return False

            # 获取用户输入的DL编号
            dl_number = dialog.get_dl_number()

            # 如果用户输入了DL编号，则先验证并处理DL编号查询逻辑
            if dl_number:
                # 调用LTR控制器处理DL编号查询
                result = self.ltr_controller.handle_view_dl_number(dl_number)

                if result["success"]:
                    # 成功找到DL编号，使用LTR编辑器控制器显示编辑对话框并处理更新
                    # 准备数据
                    ltr_data = {
                        'dl_number': dl_number,
                        'data': result['data']
                    }

                    # 使用LTR编辑器控制器打开编辑对话框并处理更新
                    update_success = self.ltr_editor_controller.open_editor_and_update(ltr_data, self.view)

                    if update_success:
                        logger.info(f"成功更新DL编号 {dl_number} 的数据")
                    elif update_success is False:
                        logger.info(f"用户取消了DL编号 {dl_number} 的更新操作")

                    self.service.update_status(f"已定位到DL编号: {dl_number}")
                    logger.info(f"Successfully found and positioned to DL number: {dl_number}")
                    success = True  # 设置成功标志
                else:
                    # 关闭Excel应用程序，因为handle_view_dl_number已经打开了它
                    from src.utils.excel_utils import release_excel_app
                    release_excel_app()
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self.view,
                        "查找结果",
                        f"未找到DL编号: {dl_number}\n错误信息: {result.get('error', '未知错误')}"
                    )
                    self.service.update_status(f"未找到DL编号: {dl_number}")
                    # 重新显示DL编号输入对话框
                    return self.handle_view_ltr()
            else:
                # 用户选择跳过，执行默认的LTR查看逻辑
                success = self.ltr_controller.handle_view_ltr()

            if success:
                if not dl_number:  # 只有在非DL编号查询时才更新状态
                    file_path = self.ltr_controller.get_ltr_file_path()
                    self.service.update_status(f"已处理LTR文件: {file_path}")
                    logger.info(f"LTR file processed successfully from main window: {file_path}")
            else:
                file_path = self.ltr_controller.get_ltr_file_path()
                self.service.update_status(f"处理LTR文件失败: {file_path}")
                logger.error(f"Failed to process LTR file from main window: {file_path}")

            return success
        except Exception as e:
            logger.error(f"Failed to handle view LTR request from main window: {e}")
            self.service.update_status("处理LTR文件时发生错误")
            return False


    def handle_open_file(self, file_path: str) -> bool:
        """
        处理打开文件事件

        Args:
            file_path: 文件路径

        Returns:
            是否处理成功
        """
        try:
            logger.debug(f"Handling open file request: {file_path}")

            # 添加到最近文件列表
            self.service.add_recent_file(file_path)

            # 更新状态
            self.service.update_status(f"已打开文件: {file_path}")

            logger.info(f"File opened successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to open file '{file_path}': {e}")
            self.service.update_status(f"打开文件失败: {file_path}")
            return False

    def handle_new_file(self) -> bool:
        """
        处理新建文件事件

        Returns:
            是否处理成功
        """
        try:
            logger.debug("Handling new file request")

            # 创建项目创建控制器并处理新建项目请求
            project_creator = ProjectCreatorController(self.view)
            success = project_creator.handle_create_new_project()
            
            # 清理资源
            project_creator.cleanup()
            
            logger.debug(f"New file handling completed, success: {success}")
            return success
        except Exception as e:
            logger.error(f"Failed to handle new file request: {e}")
            self.service.update_status("新建项目失败")
            return False

    def handle_open_project(self) -> bool:
        """
        处理打开项目事件

        Returns:
            是否处理成功
        """
        try:
            logger.debug("Handling open project request")

            # 获取默认项目路径
            from src.core.config_manager import config_manager
            default_project_path = config_manager.get("paths.default_project_path", "")
            
            # 确保路径存在，如果不存在则使用空字符串（系统默认路径）
            if not os.path.exists(default_project_path):
                default_project_path = ""

            # 显示文件夹选择对话框
            project_path = QFileDialog.getExistingDirectory(
                self.view,
                "选择项目文件夹",
                default_project_path,  # 使用配置的默认路径作为初始目录
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )

            if not project_path:  # 用户取消了选择
                return False

            # 检查项目文件夹是否包含必要的文件
            json_files = [f for f in os.listdir(project_path) if f.endswith('.json')]
            
            # 如果没有找到JSON文件，则创建一个新的空白JSON文件
            if not json_files:
                logger.info(f"在项目路径 {project_path} 中未找到JSON文件，开始创建新的application_data.json文件")
                # 查找项目文件夹名称作为DL编号
                dl_number = os.path.basename(project_path)
                logger.info(f"使用文件夹名称作为DL编号: {dl_number}")
                
                # 创建空白的application_data.json文件
                json_file_path = os.path.join(project_path, "application_data.json")
                
                # 尝试从"Submitted Material"文件夹中查找包含"test request"关键字的.docx文件
                # 首先查找以DL编号开头的子文件夹
                dl_subfolder_path = None
                # 对目录列表进行排序，确保每次遍历顺序一致
                items = sorted(os.listdir(project_path))
                for item in items:
                    item_path = os.path.join(project_path, item)
                    if os.path.isdir(item_path) and item.startswith(dl_number):
                        dl_subfolder_path = item_path
                        break
                
                # 如果找到了以DL编号开头的子文件夹，则在其中查找Submitted Material文件夹
                submitted_material_path = None
                if dl_subfolder_path:
                    submitted_material_path = os.path.join(dl_subfolder_path, "Submitted Material")
                    # 标准化路径分隔符
                    submitted_material_path = os.path.normpath(submitted_material_path)
                
                # 注意：即使没有找到submitted_material_path，我们也继续执行后续逻辑
                # 不再回退到项目根目录查找
                
                test_request_data = {}
                
                if submitted_material_path:
                    logger.info(f"检查Submitted Material文件夹: {submitted_material_path}")
                    if os.path.exists(submitted_material_path):
                        logger.info(f"Submitted Material文件夹存在，开始搜索包含'test request'关键字的.docx文件")
                        # 查找包含"test request"关键字的.docx文件
                        # 改进搜索逻辑以匹配更多格式，如"E-3718_H_Laboratory_Test_Request_CPHD 10MM(.docx"
                        docx_files = []
                        for f in os.listdir(submitted_material_path):
                            if f.lower().endswith('.docx'):
                                # 检查文件名是否包含测试请求相关关键词
                                fname_lower = f.lower()
                                if 'test' in fname_lower and ('request' in fname_lower or 'test' in fname_lower):
                                    docx_files.append(f)
                                elif 'e-3718' in fname_lower and 'request' in fname_lower:
                                    docx_files.append(f)
                
                        if docx_files:
                            logger.info(f"找到 {len(docx_files)} 个匹配的.docx文件: {docx_files}")
                            # 从第一个匹配的文件中提取信息
                            # 使用 os.path.join 确保路径格式正确
                            docx_file_path = os.path.join(submitted_material_path, docx_files[0])
                            # 标准化路径分隔符
                            docx_file_path = os.path.normpath(docx_file_path)
                            logger.info(f"从文件中提取信息: {docx_file_path}")
                            test_request_data = self._extract_info_from_test_request(docx_file_path)
                            logger.info(f"提取到的数据: {test_request_data}")
                        else:
                            logger.info("在Submitted Material文件夹中未找到包含'test request'关键字的.docx文件")
                    else:
                        logger.info(f"Submitted Material文件夹不存在: {submitted_material_path}")
                else:
                    logger.info(f"未找到以DL编号'{dl_number}'开头的子文件夹，跳过查找Submitted Material文件夹并继续后续逻辑")
                
                # 加载完整的字段配置
                from src.features.ltr_manager.utils.field_config_loader import LTRFieldConfigLoader
                config_loader = LTRFieldConfigLoader()
                field_mapping = config_loader.load_application_field_mapping()
                
                # 创建完整字段的数据结构
                application_data = {}
                
                # 为每个字段设置默认值或从提取的数据中获取值
                for field in field_mapping:
                    key = field['key']
                    # 特殊处理DL字段
                    if key == "DL":
                        application_data[key] = dl_number
                    # 从提取的数据中获取值，如果没有则设为空字符串
                    elif key in test_request_data:
                        application_data[key] = test_request_data[key]
                    else:
                        # 默认值处理
                        if key == "project_leader":
                            # 从配置中获取默认的project_leader
                            from src.core.config_manager import config_manager
                            application_data[key] = config_manager.get("defaults.project_leader", "")
                        elif key == "sub_contract":
                            application_data[key] = "Yes"
                        elif key == "test_result":
                            application_data[key] = "In progress"
                        elif key == "test_type":
                            application_data[key] = "Partial Qualification"
                        elif key == "lab_performing_the_tests":
                            application_data[key] = "Dongguan"
                        elif key == "condition_of_samples_when_received":
                            application_data[key] = "Acceptable"
                        elif key == "project_type":
                            application_data[key] = "NPD"
                        else:
                            # 其他字段默认为空字符串
                            application_data[key] = ""
                
                # 设置状态为new
                application_data["status"] = "new"
                application_data["error"] = ""
                
                # 如果有选中的文件路径，也加入进去
                if 'selected_filename' in test_request_data:
                    application_data['selected_filename'] = test_request_data['selected_filename']
                else:
                    application_data['selected_filename'] = ""
                
                # 确保file_path字段存在
                application_data['file_path'] = test_request_data.get('file_path', '')
                
                # 保存空白JSON文件
                try:
                    with open(json_file_path, 'w', encoding='utf-8') as f:
                        json.dump(application_data, f, ensure_ascii=False, indent=4)
                    logger.info(f"Created new application_data.json file: {json_file_path}")
                except Exception as e:
                    logger.error(f"Failed to create application_data.json: {e}")
                    QMessageBox.warning(
                        self.view,
                        "创建文件失败",
                        f"无法创建项目数据文件: {str(e)}"
                    )
                    return False
                
                # 弹出更新基本信息对话框（使用专门的对话框）
                logger.info("显示基本信息对话框供用户确认和编辑")
                self._show_basic_info_dialog(application_data, json_file_path)
                
                # 重新加载JSON文件列表
                json_files = ["application_data.json"]

            # 读取JSON文件以获取项目信息（特别是DL编号）
            dl_number = None
            try:
                json_file_path = os.path.join(project_path, json_files[0])
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                    # 尝试从项目数据中获取DL编号
                    dl_number = project_data.get('DL', None)
                    if not dl_number:
                        # 如果DL字段不存在，尝试从文件名中提取
                        dl_number = os.path.basename(project_path)
            except Exception as e:
                logger.warning(f"读取项目JSON文件时出错: {e}")
                # 如果无法读取JSON文件，使用文件夹名称作为DL编号
                dl_number = os.path.basename(project_path)

            # 保存当前项目路径到状态
            state_manager.set_state("current_project", project_path)
            
            # 保存当前项目路径到控制器属性
            self._current_project_path = project_path
            
            # 通知其他组件项目已打开
            event_dispatcher.dispatch("project.opened", {
                "project_path": project_path,
                "dl_number": dl_number
            })
            
            # 设置LTR编号到Matrix控制器
            if dl_number:
                self.matrix_project_controller.matrix_controller.set_ltr_number(dl_number)
                logger.debug(f"Set LTR number {dl_number} to Matrix controller")
            
            # 更新顶栏DL编号显示
            if hasattr(self.view, 'update_dl_number_display'):
                self.view.update_dl_number_display(dl_number)
            
            # 更新窗口标题显示项目信息
            self.view.setWindowTitle(f"TestFlow Manager - 项目: {dl_number}")

            self.service.update_status(f"已打开项目: {os.path.basename(project_path)}")
            logger.info(f"Project opened successfully: {project_path}")

            # 触发Matrix自动导入功能
            QTimer.singleShot(0, self._trigger_matrix_auto_import)

            return True
        except Exception as e:
            logger.error(f"Failed to open project: {e}")
            self.service.update_status("打开项目失败")
            QMessageBox.critical(self.view, "错误", f"打开项目失败: {str(e)}")
            return False

    def _extract_info_from_test_request(self, docx_file_path: str) -> dict:
        """
        从测试申请文档中提取信息
        
        Args:
            docx_file_path: .docx文件路径
            
        Returns:
            提取的信息字典
        """
        try:
            logger.info(f"开始从测试申请文档中提取信息: {docx_file_path}")
            # 使用现有的LTRApplicationDataExtractor来提取信息
            # 这样可以复用现有功能并保持代码一致性
            from src.features.ltr_manager.service.application_processing.data_extractor import LTRApplicationDataExtractor
            extractor = LTRApplicationDataExtractor()
            extracted_data = extractor.extract_application_data(docx_file_path)
            
            # 检查是否有错误
            if "error" in extracted_data:
                logger.error(f"Failed to extract info from test request document: {extracted_data['error']}")
                return {}
            
            # 移除不需要的字段
            extracted_data.pop('file_path', None)
            
            logger.info(f"成功从测试申请文档中提取数据: {extracted_data}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Failed to extract info from test request document: {e}")
            return {}

    def _show_basic_info_dialog(self, project_data: dict, json_file_path: str):
        """
        显示项目基本信息对话框用于更新项目信息
        
        Args:
            project_data: 项目数据
            json_file_path: JSON文件路径
        """
        try:
            logger.info("开始显示项目基本信息对话框")
            # 使用项目基本信息对话框来更新项目信息
            from src.features.main_window.view.basic_info_dialog import BasicInfoDialog
            
            # 创建并显示对话框
            dialog = BasicInfoDialog(project_data, self.view)
            result = dialog.exec_()
            
            # 如果用户确认了更改，保存到JSON文件
            if result == BasicInfoDialog.Accepted:
                modified_data = dialog.get_modified_data()
                logger.info(f"用户确认了修改，准备保存数据到: {json_file_path}")
                
                # 保存到JSON文件
                try:
                    with open(json_file_path, 'w', encoding='utf-8') as f:
                        json.dump(modified_data, f, ensure_ascii=False, indent=4)
                    logger.info(f"Updated application_data.json: {json_file_path}")
                except Exception as e:
                    logger.error(f"Failed to update application_data.json: {e}")
                    QMessageBox.warning(self.view, "保存失败", f"无法保存数据: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to show basic info dialog: {e}")
            QMessageBox.warning(self.view, "错误", f"无法显示更新对话框: {str(e)}")

    def handle_about(self) -> None:
        """处理关于事件

        Returns:
            None
        """
        try:
            # 从Service获取应用信息
            app_info = self.service.get_application_info()

            # 显示关于对话框
            QMessageBox.about(
                self.view,
                f"关于 {app_info['name']}",
                f"""<h2>{app_info['name']}</h2>
            <p><b>版本:</b> {app_info['version']}</p>
            <p><b>作者:</b> {app_info['author']}</p>
            <p>这是一个用于管理测试流程的工具，专注于处理测试申请单、邮件通信和相关文档管理。</p>"""
            )
        except Exception as e:
            logger.error(f"Failed to show about dialog: {e}")

    def get_recent_files(self) -> List[str]:
        """
        获取最近打开的文件列表

        Returns:
            文件路径列表
        """
        return self.service.load_recent_files()

    def clear_recent_files(self) -> None:
        """清空最近打开的文件列表"""
        self.service.clear_recent_files()

    def get_status(self) -> str:
        """
        获取当前状态

        Returns:
            当前状态信息
        """
        return self.service.get_status()

    def shutdown(self) -> None:
        """关闭控制器"""
        try:
            logger.info("Shutting down MainWindowController")

            # 在关闭前自动导出Matrix数据
            if self.view and hasattr(self.view, 'matrix_controller'):
                self.view.matrix_controller.auto_export_matrix_data_on_shutdown()
            
            # 保存应用程序状态
            self.service.save_application_state()
            
            # 确保所有COM对象被释放
            try:
                from src.utils import word_utils, excel_utils
                word_utils.release_word_app()
                excel_utils.release_excel_app()
            except:
                pass

            logger.info("MainWindowController shut down successfully")
        except Exception as e:
            logger.error(f"Error during MainWindowController shutdown: {e}")

