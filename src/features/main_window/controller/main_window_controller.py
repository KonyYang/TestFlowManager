"""
主窗口控制器模块
处理主窗口的业务逻辑和事件
"""
import os
import json
from typing import List, Optional
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QFileDialog
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

        # 订阅事件
        event_dispatcher.subscribe("ltr.processing.started", self._on_ltr_processing_started)
        event_dispatcher.subscribe("ltr.processing.completed", self._on_ltr_processing_completed)
        event_dispatcher.subscribe("ltr.processing.failed", self._on_ltr_processing_failed)
        event_dispatcher.subscribe("state.changed", self._on_state_changed)
        event_dispatcher.subscribe("ltr.application.confirmed", self._on_ltr_application_confirmed)
        event_dispatcher.subscribe("ltr.application.processed", self._on_ltr_application_processed)

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

        if status == "success":
            self.service.update_status(f"LTR申请单处理完成: {dl_number}")
        else:
            self.service.update_status(f"LTR申请单处理失败: {dl_number}")

    def _on_state_changed(self, data):
        """处理状态变更事件"""
        key = data.get("key")
        new_value = data.get("new_value")

        # 根据不同的状态键进行相应处理
        if key == "current_project":
            self.service.update_status(f"当前项目: {new_value}")
        elif key == "application_status":
            self.service.update_status(new_value)

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

            # TODO: 实际的文件打开逻辑
            logger.info(f"File opened successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to open file '{file_path}': {e}")
            self.service.update_status(f"打开文件失败: {file_path}")
            return False

    def handle_save_file(self, file_path: str) -> bool:
        """
        处理保存文件事件

        Args:
            file_path: 文件路径

        Returns:
            是否处理成功
        """
        try:
            logger.debug(f"Handling save file request: {file_path}")

            # TODO: 实际的文件保存逻辑
            logger.info(f"File saved successfully: {file_path}")

            # 更新状态
            self.service.update_status(f"文件已保存: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save file '{file_path}': {e}")
            self.service.update_status(f"保存文件失败: {file_path}")
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

            if success:
                self.service.update_status("已创建新项目")
                logger.info("New project created successfully")
            else:
                self.service.update_status("创建新项目失败")
                logger.error("Failed to create new project")

            return success
        except Exception as e:
            logger.error(f"Failed to create new project: {e}")
            self.service.update_status("创建新项目失败")
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
            if not json_files:
                QMessageBox.warning(
                    self.view,
                    "无效项目",
                    "所选文件夹不包含有效的项目文件（缺少JSON文件）"
                )
                return False

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

            # 创建项目创建控制器并设置项目路径
            from src.features.project_creator.controller.project_creator_controller import ProjectCreatorController
            project_creator = ProjectCreatorController(self.view)
            project_creator.set_project_path(project_path)
            
            # 设置Matrix控制器中的LTR编号
            if dl_number:
                project_creator.matrix_project_controller.matrix_controller.set_ltr_number(dl_number)
            
            # 保存当前项目路径到状态
            state_manager.set_state("current_project", project_path)

            # 显示Matrix编辑器
            success = project_creator.open_matrix_editor()

            if success:
                self.service.update_status(f"已打开项目: {os.path.basename(project_path)}")
                logger.info(f"Project opened successfully: {project_path}")
            else:
                self.service.update_status(f"打开项目失败: {os.path.basename(project_path)}")
                logger.error(f"Failed to open project: {project_path}")

            return success
        except Exception as e:
            logger.error(f"Failed to open project: {e}")
            self.service.update_status("打开项目失败")
            QMessageBox.critical(self.view, "错误", f"打开项目失败: {str(e)}")
            return False

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