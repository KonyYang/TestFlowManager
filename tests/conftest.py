"""
Pytest配置文件
提供测试固件（fixtures）和配置
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock


# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session")
def qapp_args():
    """Qt应用程序参数"""
    return []


@pytest.fixture
def mock_controller():
    """模拟主窗口控制器"""
    controller = Mock()
    controller.handle_view_ltr = Mock(return_value=True)
    controller.handle_new_file = Mock(return_value=True)
    controller.handle_open_project = Mock(return_value=True)
    controller.get_status = Mock(return_value="就绪")
    controller.handle_about = Mock()
    controller.shutdown = Mock()
    return controller


@pytest.fixture
def mock_matrix_controller():
    """模拟Matrix控制器"""
    controller = Mock()
    controller.handle_export_matrix_to_excel = Mock(return_value=True)
    controller.handle_export_llcr = Mock(return_value=True)
    controller.handle_export_cr = Mock(return_value=True)
    
    # 模拟service
    service = Mock()
    service.set_cell_value = Mock()
    controller.service = service
    
    return controller


@pytest.fixture
def mock_report_wizard_controller():
    """模拟报告向导控制器"""
    controller = Mock()
    controller.set_project_path = Mock()
    controller.set_matrix_service = Mock()
    controller.show_wizard = Mock()
    return controller


@pytest.fixture
def mock_report_updater_controller():
    """模拟报告更新控制器"""
    controller = Mock()
    controller.set_project_path = Mock()
    controller.show_report_updater_dialog = Mock()
    return controller


@pytest.fixture
def mock_customer_report_controller():
    """模拟客户报告控制器"""
    controller = Mock()
    controller.handle_generate_customer_report = Mock(return_value=True)
    return controller


@pytest.fixture
def mock_document_parser_controller():
    """模拟文档解析控制器"""
    controller = Mock()
    controller.show_body_content_editor = Mock()
    return controller


@pytest.fixture(autouse=True)
def mock_file_encryption_controller(monkeypatch):
    """自动模拟文件加密控制器"""
    mock_controller_class = Mock()
    mock_controller = Mock()
    mock_controller.show_folder_selection = Mock(return_value=None)
    mock_controller.start_encryption_task = Mock()
    mock_controller_class.return_value = mock_controller
    
    monkeypatch.setattr(
        'src.features.file_encryption.controller.file_encryption_controller.FileEncryptionController',
        mock_controller_class
    )


@pytest.fixture
def temp_project_dir(tmp_path):
    """临时项目目录"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return str(project_dir)


@pytest.fixture
def sample_matrix_data():
    """示例Matrix数据"""
    return {
        "headers": ["测试项", "窗口1", "窗口2", "窗口3"],
        "data": [
            ["测试1", "Y", "N", "Y"],
            ["测试2", "N", "Y", "Y"],
            ["测试3", "Y", "Y", "N"],
        ]
    }


@pytest.fixture
def matrix_table_widget(qtbot):
    """Matrix表格组件"""
    from PyQt5.QtWidgets import QTableWidget
    from PyQt5.QtCore import Qt
    
    table = QTableWidget()
    table.setRowCount(3)
    table.setColumnCount(4)
    table.setHorizontalHeaderLabels(["测试项", "窗口1", "窗口2", "窗口3"])
    
    # 添加一些测试数据
    for row in range(3):
        for col in range(4):
            table.setItem(row, col, Mock())
    
    return table


@pytest.fixture
def main_window(mock_controller, mock_matrix_controller):
    """主窗口固件（带模拟控制器）"""
    from src.features.main_window.view.main_window_ui import MainWindow
    
    # 创建窗口时使用模拟控制器
    window = MainWindow()
    window.controller = mock_controller
    
    # 模拟Matrix控制器
    window.matrix_controller = mock_matrix_controller
    
    yield window
    
    # 清理
    if window:
        window.close()


@pytest.fixture
def matrix_integration(main_window):
    """Matrix集成固件"""
    from src.features.main_window.view.integration.matrix_integration import MatrixIntegration
    
    integration = MatrixIntegration(main_window)
    return integration


@pytest.fixture
def event_handlers(main_window):
    """事件处理器固件"""
    from src.features.main_window.view.handlers.event_handlers import EventHandlers
    
    handlers = EventHandlers(main_window)
    return handlers


def pytest_configure(config):
    """pytest配置钩子"""
    # 注册自定义标记
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "gui: GUI测试（需要显示）")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "skip_in_ci: CI环境中跳过")


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    # 为测试添加标记
    for item in items:
        # 根据文件路径自动添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # 为GUI测试添加标记
        if "test_gui" in item.name or "main_window" in item.name:
            item.add_marker(pytest.mark.gui)
