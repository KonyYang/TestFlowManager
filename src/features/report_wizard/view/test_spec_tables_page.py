"""
Test Spec Tables页面视图组件
提供测试规格表格填写的向导页面
"""
import os

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QGroupBox
)
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot
from src.core.logger import logger
from src.features.report_wizard.service.test_spec_tables_service import TestSpecTablesService

class TestSpecTablesWorker(QThread):
    """处理Test Spec Tables的后台工作线程"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, document_path, matrix_service=None):
        super().__init__()
        self.document_path = document_path
        self.matrix_service = matrix_service
        self.matrix_data_structure = None
        
        # 从Matrix服务获取或创建数据结构
        if self.matrix_service:
            self.matrix_data_structure = self._create_matrix_data_structure_from_service(self.matrix_service)
            logger.info(f"TestSpecTablesWorker初始化: document_path={document_path}, matrix_service is not None: {matrix_service is not None}, matrix_data_structure is not None: {self.matrix_data_structure is not None}")
        else:
            logger.info(f"TestSpecTablesWorker初始化: document_path={document_path}, matrix_service is not None: {matrix_service is not None}, 无法获取matrix_data_structure")
    
    def _create_matrix_data_structure_from_service(self, matrix_service):
        """从Matrix服务创建数据结构"""
        try:
            # 检查matrix_service是否是MatrixService实例或MatrixController实例
            if hasattr(matrix_service, 'data_model') and hasattr(matrix_service.data_model, 'rows'):
                # MatrixService或MatrixController实例
                matrix_data = matrix_service.data_model.rows
                logger.info(f"Worker: 从Matrix服务获取到 {len(matrix_data)} 行数据")
                
                # 创建MatrixDataStructure实例并解析数据
                from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
                matrix_structure = MatrixDataStructure()
                
                # 尝试获取DL编号和项目数据文件路径
                dl_number = "DL-UNKNOWN"
                project_data_file_path = None
                
                # 从Matrix服务获取项目数据文件路径
                if hasattr(matrix_service, 'project_data_file_path') and matrix_service.project_data_file_path:
                    project_data_file_path = matrix_service.project_data_file_path
                    logger.debug(f"Worker: 从Matrix服务获取到项目数据文件路径: {project_data_file_path}")
                    
                    # 从项目数据文件中提取DL编号
                    if project_data_file_path and os.path.exists(project_data_file_path):
                        try:
                            import json
                            with open(project_data_file_path, 'r', encoding='utf-8') as f:
                                project_data = json.load(f)
                                dl_number = project_data.get("DL", dl_number)
                                logger.debug(f"Worker: 从项目数据文件中提取到DL编号: {dl_number}")
                        except Exception as e:
                            logger.error(f"Worker: 读取项目数据文件时出错: {e}")
                
                matrix_structure.dl_number = dl_number
                matrix_structure.project_data_file_path = project_data_file_path
                logger.debug(f"Worker: 设置DL编号: {dl_number}")
                logger.debug(f"Worker: 设置项目数据文件路径: {project_data_file_path}")
                
                # 解析Matrix数据为结构化数据
                warnings = matrix_structure.parse_matrix_to_structure(matrix_data)
                
                # 记录解析结果
                group_count = len(matrix_structure.group_steps)
                logger.info(f"Worker: Matrix数据解析完成，共找到 {group_count} 个组别")
                
                # 添加数据结构内容的详细日志
                logger.debug(f"Worker: Matrix数据结构详情 - DL编号: {matrix_structure.dl_number}")
                logger.debug(f"Worker: Matrix数据结构详情 - 项目数据文件路径: {matrix_structure.project_data_file_path}")
                logger.debug(f"Worker: Matrix数据结构详情 - 组别列表: {list(matrix_structure.group_steps.keys())}")
                
                # 显示每个组别的步骤数量
                for group_name, steps in matrix_structure.group_steps.items():
                    logger.debug(f"Worker: 组别 '{group_name}' 包含 {len(steps)} 个步骤")
                    # 如果步骤数量不多，显示前几个步骤的详细信息
                    if len(steps) > 0:
                        for i, step in enumerate(steps[:3]):  # 只显示前3个步骤作为示例
                            logger.debug(f"Worker:   步骤 {i+1}: {step}")
                        if len(steps) > 3:
                            logger.debug(f"Worker:   ... 还有 {len(steps) - 3} 个步骤")
                
                # 显示LLCR和CR需求
                if matrix_structure.llcr_requirements:
                    logger.debug(f"Worker: LLCR需求: {matrix_structure.llcr_requirements}")
                if matrix_structure.cr_requirements:
                    logger.debug(f"Worker: CR需求: {matrix_structure.cr_requirements}")
                
                if warnings:
                    logger.warning(f"Worker: Matrix数据验证警告: {warnings}")
                
                return matrix_structure
            elif hasattr(matrix_service, 'data_structure'):
                # 如果matrix_service直接有data_structure属性，直接使用
                logger.info("Worker: 直接从Matrix服务的data_structure属性获取数据结构")
                return matrix_service.data_structure
            else:
                logger.error("Worker: Matrix服务没有可用的数据模型或数据结构")
                return None
                
        except Exception as e:
            logger.error(f"Worker: 创建Matrix数据结构时出错: {e}")
            import traceback
            logger.error(f"Worker: 错误堆栈: {traceback.format_exc()}")
            return None
    
    def run(self):
        """执行Test Spec Tables填充操作"""
        logger.info(f"开始执行Test Spec Tables填充: {self.document_path}, matrix_data_structure is not None: {self.matrix_data_structure is not None}")
        
        try:
            # 创建服务实例
            service = TestSpecTablesService()
            
            # 执行填充操作 - 使用从Matrix服务获取的数据结构
            success = service.fill_all_test_spec_tables(
                self.document_path,
                self.matrix_data_structure,  # 使用从Matrix服务获取的数据结构
                self.progress_updated,
                self.status_updated
            )
            
            logger.info(f"Test Spec Tables填充完成: {success}")
            self.finished.emit(success)
        except Exception as e:
            logger.error(f"执行Test Spec Tables填充时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.status_updated.emit(f"错误: {str(e)}")
            self.finished.emit(False)


class TestSpecTablesPage(QFrame):
    """
    Test Spec Tables页面视图组件
    提供测试规格表格填写的向导页面
    """
    
    # 自定义信号
    content_updated = pyqtSignal(str)  # 传递更新的文档路径
    # 导航信号
    # previous_clicked = pyqtSignal()  # 已禁用上一步功能
    # next_clicked = pyqtSignal()
    finish_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    
    def __init__(self, parent=None, document_path=None, matrix_service=None):
        """初始化Test Spec Tables页面"""
        super().__init__(parent)
        self.document_path = document_path
        self.matrix_service = matrix_service  # 接收Matrix服务或Matrix控制器
        self.matrix_data_structure = None  # 从Matrix服务中获取数据结构
        
        # 如果Matrix服务存在，立即解析数据并创建数据结构
        if self.matrix_service:
            logger.info("Matrix服务已设置，准备解析数据结构")
            self._create_matrix_data_structure()
        else:
            logger.info("Matrix服务未设置，等待外部设置")
            
        self.worker = None
        self.init_ui()
        
        logger.info(f"TestSpecTablesPage初始化完成: document_path={self.document_path}, matrix_service is not None: {self.matrix_service is not None}, matrix_data_structure is not None: {self.matrix_data_structure is not None}")
        
        # 检查必要参数是否已设置 - 只有当两个条件都满足时才开始处理
        if self.document_path and self.matrix_data_structure is not None:
            logger.info("文档路径和Matrix数据结构均已设置，开始处理")
            self.start_processing()
        elif self.document_path:
            logger.info("文档路径已设置，等待Matrix数据结构...")
            self.status_label.setText("等待Matrix数据结构...")
        elif self.matrix_data_structure is not None:
            logger.info("Matrix数据结构已设置，等待文档路径...")
            self.status_label.setText("等待文档路径设置...")
        else:
            logger.info("等待文档路径和Matrix数据结构设置...")
            self.status_label.setText("等待文档路径设置...")

    def _create_matrix_data_structure(self):
        """从Matrix服务创建数据结构"""
        try:
            # 检查matrix_service是否是MatrixService实例或MatrixController实例
            if hasattr(self.matrix_service, 'data_model') and hasattr(self.matrix_service.data_model, 'rows'):
                # MatrixService或MatrixController实例
                matrix_data = self.matrix_service.data_model.rows
                logger.info(f"从Matrix服务获取到 {len(matrix_data)} 行数据")
                
                # 创建MatrixDataStructure实例并解析数据
                from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
                self.matrix_data_structure = MatrixDataStructure()
                
                # 尝试获取DL编号和项目数据文件路径
                dl_number = "DL-UNKNOWN"
                project_data_file_path = None
                
                # 从Matrix服务获取项目数据文件路径
                if hasattr(self.matrix_service, 'project_data_file_path') and self.matrix_service.project_data_file_path:
                    project_data_file_path = self.matrix_service.project_data_file_path
                    logger.debug(f"从Matrix服务获取到项目数据文件路径: {project_data_file_path}")
                    
                    # 从项目数据文件中提取DL编号
                    if project_data_file_path and os.path.exists(project_data_file_path):
                        try:
                            import json
                            with open(project_data_file_path, 'r', encoding='utf-8') as f:
                                project_data = json.load(f)
                                dl_number = project_data.get("DL", dl_number)
                                logger.debug(f"从项目数据文件中提取到DL编号: {dl_number}")
                        except Exception as e:
                            logger.error(f"读取项目数据文件时出错: {e}")
                
                self.matrix_data_structure.dl_number = dl_number
                self.matrix_data_structure.project_data_file_path = project_data_file_path
                logger.debug(f"设置DL编号: {dl_number}")
                logger.debug(f"设置项目数据文件路径: {project_data_file_path}")
                
                # 解析Matrix数据为结构化数据
                warnings = self.matrix_data_structure.parse_matrix_to_structure(matrix_data)
                
                # 记录解析结果
                group_count = len(self.matrix_data_structure.group_steps)
                logger.info(f"Matrix数据解析完成，共找到 {group_count} 个组别")
                
                # 添加数据结构内容的详细日志
                logger.debug(f"Matrix数据结构详情 - DL编号: {self.matrix_data_structure.dl_number}")
                logger.debug(f"Matrix数据结构详情 - 项目数据文件路径: {self.matrix_data_structure.project_data_file_path}")
                logger.debug(f"Matrix数据结构详情 - 组别列表: {list(self.matrix_data_structure.group_steps.keys())}")
                
                # 显示每个组别的步骤数量
                for group_name, steps in self.matrix_data_structure.group_steps.items():
                    logger.debug(f"组别 '{group_name}' 包含 {len(steps)} 个步骤")
                    # 如果步骤数量不多，显示前几个步骤的详细信息
                    if len(steps) > 0:
                        for i, step in enumerate(steps[:3]):  # 只显示前3个步骤作为示例
                            logger.debug(f"  步骤 {i+1}: {step}")
                        if len(steps) > 3:
                            logger.debug(f"  ... 还有 {len(steps) - 3} 个步骤")
                
                # 显示LLCR和CR需求
                if self.matrix_data_structure.llcr_requirements:
                    logger.debug(f"LLCR需求: {self.matrix_data_structure.llcr_requirements}")
                if self.matrix_data_structure.cr_requirements:
                    logger.debug(f"CR需求: {self.matrix_data_structure.cr_requirements}")
                
                if warnings:
                    logger.warning(f"Matrix数据验证警告: {warnings}")
                
            elif hasattr(self.matrix_service, 'data_structure'):
                # 如果matrix_service直接有data_structure属性，直接使用
                self.matrix_data_structure = self.matrix_service.data_structure
                logger.info("直接从Matrix服务的data_structure属性获取数据结构")
            else:
                logger.error("Matrix服务没有可用的数据模型或数据结构")
                self.matrix_data_structure = None
                
        except Exception as e:
            logger.error(f"创建Matrix数据结构时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            self.matrix_data_structure = None

    def set_document_path(self, document_path):
        """设置要处理的文档路径"""
        logger.info(f"设置文档路径: {document_path}")
        self.document_path = document_path
        # 如果文档路径和Matrix数据结构都已设置，并且进度为0（未开始处理），则开始处理
        if self.document_path and self.matrix_data_structure is not None and self.progress_bar.value() == 0:
            logger.info("文档路径和Matrix数据结构均已设置，开始处理")
            self.start_processing()
        else:
            logger.info(f"文档路径已设置，但等待Matrix数据结构或处理已开始 - 路径: {bool(self.document_path)}, Matrix: {self.matrix_data_structure is not None}, 进度: {self.progress_bar.value()}")
            if self.document_path and self.matrix_data_structure is None:
                self.status_label.setText("等待Matrix数据结构...")

    def set_matrix_service(self, matrix_service):
        """设置Matrix服务"""
        logger.info(f"设置Matrix服务: {matrix_service is not None}")
        if matrix_service:
            logger.info(f"Matrix服务类型: {type(matrix_service)}")
        self.matrix_service = matrix_service
        
        # 重新创建数据结构
        if self.matrix_service:
            self._create_matrix_data_structure()
            logger.info("Matrix数据结构已更新")
        else:
            self.matrix_data_structure = None
            logger.info("Matrix服务已清除")
            
        # 如果文档路径和Matrix数据结构都已设置，并且进度为0（未开始处理），则开始处理
        if self.document_path and self.matrix_data_structure is not None and self.progress_bar.value() == 0:
            logger.info("文档路径和Matrix数据结构均已设置，开始处理")
            self.start_processing()
        else:
            logger.info(f"Matrix服务已设置，但等待文档路径或处理已开始 - 路径: {bool(self.document_path)}, Matrix: {self.matrix_data_structure is not None}, 进度: {self.progress_bar.value()}")
            if self.matrix_data_structure is not None and not self.document_path:
                self.status_label.setText("等待文档路径设置...")
            elif self.matrix_data_structure is None:
                self.status_label.setText("等待Matrix数据结构...")
    
    def start_processing(self):
        """开始处理"""
        logger.info(f"开始处理 - document_path: {self.document_path}, matrix_data_structure: {self.matrix_data_structure is not None}")
        if not self.document_path:
            self.status_label.setText("错误: 未指定文档路径")
            logger.error("未指定文档路径")
            return
            
        # 重置进度
        self.progress_bar.setValue(0)
        self.status_label.setText("正在开始处理...")
        logger.info(f"开始处理文档: {self.document_path}")
        
        # 创建并启动工作线程，传递Matrix服务以便worker可以创建数据结构
        self.worker = TestSpecTablesWorker(self.document_path, self.matrix_service)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.status_updated.connect(self.update_status)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()
    
    @pyqtSlot(int)
    def update_progress(self, value):
        """更新进度"""
        self.progress_bar.setValue(value)
    
    @pyqtSlot(str)
    def update_status(self, status):
        """更新状态"""
        self.status_label.setText(status)
    
    @pyqtSlot(bool)
    def processing_finished(self, success):
        """处理完成"""
        if success:
            self.status_label.setText("处理完成！表格已成功填充。")
            self.progress_bar.setValue(100)
            
            # 处理成功后直接关闭向导
            parent_wizard = self.parent()
            if parent_wizard and hasattr(parent_wizard, 'accept'):
                parent_wizard.accept()
        else:
            self.status_label.setText("处理失败，请检查日志。")
            # 处理失败后也直接关闭向导
            parent_wizard = self.parent()
            if parent_wizard and hasattr(parent_wizard, 'accept'):
                parent_wizard.accept()
    
    def get_current_data(self):
        """获取当前页面的数据"""
        data = {
            'document_path': self.document_path,
            'matrix_data_structure': self.matrix_data_structure,
            'processing_completed': self.progress_bar.value() == 100
        }
        return data
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("正在填充 Test Description 和 Test Method 表格")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 说明文本
        desc_label = QLabel("正在从Matrix数据中提取信息并填充到Word文档表格中...")
        desc_label.setStyleSheet("font-size: 14px; color: #666666; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # 进度组
        progress_group = QGroupBox("处理进度")
        progress_group.setStyleSheet("font-size: 14px; font-weight: bold;")
        progress_layout = QVBoxLayout()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备开始处理...")
        self.status_label.setStyleSheet("font-size: 14px; color: #333333;")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 底部说明
        info_label = QLabel("提示：处理完成后将自动关闭向导")
        info_label.setStyleSheet("font-size: 14px; color: #666666; margin-top: 10px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        self.setLayout(layout)