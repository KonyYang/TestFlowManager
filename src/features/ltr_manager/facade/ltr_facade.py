"""
LTR Facade - LTR 业务领域门面

封装 LTR 相关业务逻辑，作为 Shell 与 LTR 领域交互的统一入口。
所有 LTR 业务操作都通过此 Facade 进行。
"""
from typing import TYPE_CHECKING, Optional, Callable

from PyQt5.QtWidgets import QDialog, QMessageBox

from src.core.logger import logger

# LTR 控制器导入
from src.features.ltr_manager.controller.ltr_viewer_controller import LTRViewerController
from src.features.ltr_manager.controller.ltr_editor_controller import LTREditorController
from src.features.ltr_manager.view import LTRNumberInputDialog

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class LTRFacade:
    """
    LTR 业务领域门面。

    职责：
    - LTR 控制器生命周期管理
    - LTR 查看/编辑流程编排
    - 状态更新回调管理

    不负责：
    - COM 资源释放（由调用方或独立清理服务负责）
    - LTR 领域事件处理（由 LTRStatusCoordinator 负责）
    """

    def __init__(self, status_updater: Optional[Callable[[str], None]] = None):
        """
        初始化 LTR Facade。

        Args:
            status_updater: 状态栏更新回调函数
        """
        self._status_updater = status_updater
        self._ltr_controller: Optional[LTRViewerController] = None
        self._ltr_editor_controller: Optional[LTREditorController] = None

    @property
    def status_updater(self) -> Optional[Callable[[str], None]]:
        """获取状态更新回调"""
        return self._status_updater

    @status_updater.setter
    def status_updater(self, callback: Callable[[str], None]) -> None:
        """设置状态更新回调"""
        self._status_updater = callback

    def _update_status(self, message: str) -> None:
        """更新状态栏"""
        if self._status_updater:
            self._status_updater(message)

    def _ensure_controllers(self) -> tuple[LTRViewerController, LTREditorController]:
        """确保 LTR 控制器已初始化（延迟初始化）"""
        if self._ltr_controller is None:
            self._ltr_controller = LTRViewerController()
            self._ltr_editor_controller = LTREditorController(
                self._ltr_controller.data_model,
                self._ltr_controller.service,
            )
            logger.debug("LTRFacade: LTR controllers initialized")
        return self._ltr_controller, self._ltr_editor_controller

    def handle_view_ltr(self, parent_view: "QWidget") -> dict:
        """
        处理查看 LTR 文件事件。

        流程：
        1. 显示 DL 编号输入对话框
        2. 如果输入了 DL 编号，执行 DL 编号查询和编辑流程
        3. 如果跳过，执行默认的 LTR 查看流程

        Args:
            parent_view: 父窗口视图

        Returns:
            包含处理结果的字典:
            - success: 是否成功处理
            - ltr_data: 如果查找到了 LTR 数据，这是包含 dl_number 和 data 的字典（可选）
        """
        try:
            logger.debug("LTRFacade: Handling view LTR file request")

            # 确保控制器已初始化
            ltr_controller, ltr_editor_controller = self._ensure_controllers()

            # 显示 DL 编号输入对话框
            dialog = LTRNumberInputDialog(parent_view)
            result = dialog.exec_()

            # 如果用户点击取消，则直接返回
            if result != QDialog.Accepted:
                return False

            # 获取用户输入的 DL 编号
            dl_number = dialog.get_dl_number()

            # 如果用户输入了 DL 编号，则先验证并处理 DL 编号查询逻辑
            if dl_number:
                result = self._handle_dl_number_query(
                    ltr_controller, ltr_editor_controller, dl_number, parent_view
                )
                return result
            else:
                # 用户选择跳过，执行默认的 LTR 查看逻辑
                return {"success": self._handle_default_ltr_view(ltr_controller), "ltr_data": None}

        except Exception as e:
            logger.error(f"LTRFacade: Failed to handle view LTR request: {e}")
            self._update_status("处理 LTR 文件时发生错误")
            return False

    def _handle_dl_number_query(
        self,
        ltr_controller: LTRViewerController,
        ltr_editor_controller: LTREditorController,
        dl_number: str,
        parent_view: "QWidget",
    ) -> dict:
        """
        处理 DL 编号查询流程。

        Args:
            ltr_controller: LTR 查看控制器
            ltr_editor_controller: LTR 编辑控制器
            dl_number: DL 编号
            parent_view: 父窗口视图

        Returns:
            包含处理结果的字典:
            - success: 是否成功
            - ltr_data: LTR 数据字典（如果找到）
        """
        # 调用 LTR 控制器处理 DL 编号查询
        result = ltr_controller.handle_view_dl_number(dl_number)

        if result["success"]:
            # 成功找到 DL 编号，使用 LTR 编辑器控制器显示编辑对话框并处理更新
            ltr_data = {
                "dl_number": dl_number,
                "data": result["data"],
            }

            # 使用 LTR 编辑器控制器打开编辑对话框并处理更新
            update_success = ltr_editor_controller.open_editor_and_update(
                ltr_data, parent_view
            )

            if update_success:
                logger.info(f"LTRFacade: 成功更新 DL 编号 {dl_number} 的数据")
            elif update_success is False:
                logger.info(f"LTRFacade: 用户取消了 DL 编号 {dl_number} 的更新操作")

            self._update_status(f"已定位到 DL 编号: {dl_number}")
            logger.info(f"LTRFacade: Successfully found and positioned to DL number: {dl_number}")
            return {"success": True, "ltr_data": ltr_data}
        else:
            # 查询失败
            self._handle_dl_number_not_found(
                result, dl_number, ltr_controller, parent_view
            )
            # 重新显示 DL 编号输入对话框
            return self.handle_view_ltr(parent_view)

    def _handle_dl_number_not_found(
        self,
        result: dict,
        dl_number: str,
        ltr_controller: LTRViewerController,
        parent_view: "QWidget",
    ) -> None:
        """
        处理 DL 编号未找到的情况。

        Args:
            result: 查询结果
            dl_number: DL 编号
            ltr_controller: LTR 查看控制器
            parent_view: 父窗口视图
        """
        # 关闭 Excel 应用程序
        from src.utils.excel_utils import release_excel_app

        release_excel_app()
        QMessageBox.warning(
            parent_view,
            "查找结果",
            f"未找到 DL 编号: {dl_number}\n错误信息: {result.get('error', '未知错误')}",
        )
        self._update_status(f"未找到 DL 编号: {dl_number}")

    def _handle_default_ltr_view(
        self,
        ltr_controller: LTRViewerController,
    ) -> bool:
        """
        处理默认的 LTR 查看流程。

        Args:
            ltr_controller: LTR 查看控制器

        Returns:
            是否成功
        """
        success = ltr_controller.handle_view_ltr()

        if success:
            file_path = ltr_controller.get_ltr_file_path()
            self._update_status(f"已处理 LTR 文件: {file_path}")
            logger.info(f"LTRFacade: LTR file processed successfully: {file_path}")
        else:
            file_path = ltr_controller.get_ltr_file_path()
            self._update_status(f"处理 LTR 文件失败: {file_path}")
            logger.error(f"LTRFacade: Failed to process LTR file: {file_path}")

        return success

    def cleanup(self) -> None:
        """
        清理 LTR Facade 资源。

        注意：这不会关闭 Excel/Word 等 COM 资源，
        COM 资源释放应由 Application 退出时统一处理。
        """
        self._ltr_controller = None
        self._ltr_editor_controller = None
        logger.debug("LTRFacade: Cleanup completed")
