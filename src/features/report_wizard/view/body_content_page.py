"""
正文内容页面视图
实现向导中正文内容编辑页面的UI组件
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QFrame, QFileDialog,
    QSplitter, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import pyqtSignal
from src.features.content_editor.service.body_content_service import BodyContentService
from src.features.content_editor.service.document_content_service import (
    DocumentContentService,
)
from src.features.report_wizard.view.body_content_page_document_workflow import (
    BodyContentPageDocumentWorkflow,
)
from src.core.logger import logger
from src.features.content_editor.view.components.document_editor_mixin import DocumentEditorMixin


class BodyContentPage(QFrame, DocumentEditorMixin):
    """
    正文内容页面视图组件
    提供报告正文内容编辑的向导页面
    """
    
    # 自定义信号
    content_updated = pyqtSignal(str)  # 传递更新的文档路径
    # 导航信号
    # previous_clicked = pyqtSignal()  # 已禁用上一步功能
    # next_clicked = pyqtSignal()
    finish_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化正文内容页面"""
        super().__init__(parent)
        self.document_path = None
        self.body_content_service = BodyContentService()
        self.document_content_service = DocumentContentService()
        self._document_workflow = BodyContentPageDocumentWorkflow(self.document_content_service)
        # 添加状态保持变量
        self._cached_purpose_content = ""
        self._cached_conclusions_content = ""
        self._content_loaded = False  # 标记内容是否已加载
        logger.info(f"开始初始化正文内容页面，混入类初始化状态检查:")
        logger.info(f"  - body_content_service 实例: {self.body_content_service is not None}")
        # 使用 get_predefined_descriptions() 方法而非直接访问属性
        purpose_descs = self.body_content_service.get_predefined_descriptions("PURPOSE") if self.body_content_service else []
        conclusions_descs = self.body_content_service.get_predefined_descriptions("CONCLUSIONS") if self.body_content_service else []
        logger.info(f"  - body_content_service 预设描述 - PURPOSE: {len(purpose_descs)}项, CONCLUSIONS: {len(conclusions_descs)}项")
        self.init_ui()
        
        # 调试：检查预设列表是否已初始化
        logger.info(f"初始化正文内容页面")
        if hasattr(self, 'purpose_preset_list') and self.purpose_preset_list:
            logger.info(f"PURPOSE 预设列表已初始化，项目数量: {self.purpose_preset_list.count()}")
        else:
            logger.warning("PURPOSE 预设列表未初始化或为空")
        if hasattr(self, 'conclusions_preset_list') and self.conclusions_preset_list:
            logger.info(f"CONCLUSIONS 预设列表已初始化，项目数量: {self.conclusions_preset_list.count()}")
        else:
            logger.warning("CONCLUSIONS 预设列表未初始化或为空")
        
        # 初始化时加载默认文档路径
        self._load_default_document()
    
    def init_ui(self):
        """初始化用户界面"""
        logger.info("开始初始化用户界面")
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 主要内容编辑区域 - 使用与body_content_dialog相同的布局
        self.content_area = QFrame()
        content_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("编辑文档")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 5px;")
        content_layout.addWidget(title_label)
        
        # 创建分割窗口
        splitter = QSplitter()
        
        # 左侧：内容编辑区域（分上下两部分）
        left_widget = self._create_content_edit_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：预设描述区域（分上下两部分）
        logger.info("开始创建预设面板")
        right_widget = self._create_preset_panel()
        logger.info("预设面板创建完成")
        splitter.addWidget(right_widget)
        
        splitter.setSizes([600, 600])  # 设置初始大小
        content_layout.addWidget(splitter)
        
        self.content_area.setLayout(content_layout)
        layout.addWidget(self.content_area)

        # 添加弹性空间
        layout.addStretch()

        self.setLayout(layout)
        logger.info("用户界面初始化完成")
        
        # 调试：检查预设面板是否已创建
        if hasattr(self, 'purpose_preset_list') and self.purpose_preset_list:
            logger.info(f"PURPOSE 预设列表已创建，项目数量: {self.purpose_preset_list.count()}")
        else:
            logger.warning("PURPOSE 预设列表未创建或为空")
        if hasattr(self, 'conclusions_preset_list') and self.conclusions_preset_list:
            logger.info(f"CONCLUSIONS 预设列表已创建，项目数量: {self.conclusions_preset_list.count()}")
        else:
            logger.warning("CONCLUSIONS 预设列表未创建或为空")

    def set_document_path(self, document_path: str):
        """设置要编辑的文档路径"""
        logger.info(f"设置文档路径: {document_path}")
        self.document_path = document_path
        if self.document_path:
            logger.info(f"文档路径不为空，开始初始化文档编辑器组件")
            # 初始化文档编辑器组件
            logger.info(f"调用 _init_document_editor_components 之前，检查混入类属性:")
            logger.info(f"  - purpose_preset_list: {getattr(self, 'purpose_preset_list', 'NOT SET')}")
            logger.info(f"  - conclusions_preset_list: {getattr(self, 'conclusions_preset_list', 'NOT SET')}")
            logger.info(f"  - edit_purpose_content: {getattr(self, 'edit_purpose_content', 'NOT SET')}")
            logger.info(f"  - edit_conclusions_content: {getattr(self, 'edit_conclusions_content', 'NOT SET')}")
            
            self._init_document_editor_components(self.document_path)
            
            logger.info(f"调用 _init_document_editor_components 之后，检查混入类属性:")
            logger.info(f"  - purpose_preset_list: {getattr(self, 'purpose_preset_list', 'NOT SET')}")
            logger.info(f"  - conclusions_preset_list: {getattr(self, 'conclusions_preset_list', 'NOT SET')}")
            logger.info(f"  - edit_purpose_content: {getattr(self, 'edit_purpose_content', 'NOT SET')}")
            logger.info(f"  - edit_conclusions_content: {getattr(self, 'edit_conclusions_content', 'NOT SET')}")
            
            # 加载文档内容
            logger.info(f"正在加载文档内容: {self.document_path}")
            self.load_document_content()
            logger.info(f"文档内容加载完成")
            # 调试：检查预设列表是否已初始化
            if hasattr(self, 'purpose_preset_list') and self.purpose_preset_list:
                logger.info(f"PURPOSE 预设列表已初始化，对象ID: {id(self.purpose_preset_list)}，项目数量: {self.purpose_preset_list.count()}")
                # 检查预设列表中的项目
                for i in range(self.purpose_preset_list.count()):
                    item = self.purpose_preset_list.item(i)
                    if item:
                        logger.info(f"PURPOSE 预设项 {i}: {item.text()}")
            else:
                logger.warning("PURPOSE 预设列表未初始化或为空")
            if hasattr(self, 'conclusions_preset_list') and self.conclusions_preset_list:
                logger.info(f"CONCLUSIONS 预设列表已初始化，对象ID: {id(self.conclusions_preset_list)}，项目数量: {self.conclusions_preset_list.count()}")
                # 检查预设列表中的项目
                for i in range(self.conclusions_preset_list.count()):
                    item = self.conclusions_preset_list.item(i)
                    if item:
                        logger.info(f"CONCLUSIONS 预设项 {i}: {item.text()}")
            else:
                logger.warning("CONCLUSIONS 预设列表未初始化或为空")
            # 连接混入类的信号
            self._connect_common_signals()
            # 禁用混入类中的保存和预览按钮，因为我们将使用向导导航按钮
            if hasattr(self, 'save_btn') and self.save_btn:
                self.save_btn.setVisible(False)

    def _create_buttons(self):
        """重写按钮创建方法，不创建按钮（因为使用向导导航按钮）"""
        # 返回一个空布局，因为我们使用向导导航按钮
        layout = QHBoxLayout()
        layout.addStretch()
        return layout

    def _connect_common_signals(self):
        """重写信号连接方法，禁用保存和预览按钮功能"""
        # 先调用父类的方法连接预设按钮
        # 避免调用保存和预览按钮的连接
        if hasattr(self, 'load_purpose_preset_btn') and self.load_purpose_preset_btn:
            self.load_purpose_preset_btn.clicked.connect(self._load_selected_purpose_preset)
        if hasattr(self, 'add_purpose_preset_btn') and self.add_purpose_preset_btn:
            self.add_purpose_preset_btn.clicked.connect(self._add_current_purpose_to_preset)
        if hasattr(self, 'load_conclusions_preset_btn') and self.load_conclusions_preset_btn:
            self.load_conclusions_preset_btn.clicked.connect(self._load_selected_conclusions_preset)
        if hasattr(self, 'add_conclusions_preset_btn') and self.add_conclusions_preset_btn:
            self.add_conclusions_preset_btn.clicked.connect(self._add_current_conclusions_to_preset)
        
        # 重要：不连接保存和预览按钮信号，因为我们要禁用这些功能

    def _on_purpose_content_changed(self):
        """重写PURPOSE内容变化处理，禁用保存按钮"""
        try:
            current_text = self.edit_purpose_content.toPlainText()
            original_text = self.original_purpose_content.toPlainText()
            is_modified = current_text != original_text
            
            # 更新缓存内容以保持状态
            self._cached_purpose_content = current_text
            
            # 不启用混入类中的保存按钮，因为我们使用向导导航按钮
            if hasattr(self, 'save_btn') and self.save_btn:
                self.save_btn.setEnabled(False)  # 确保保存按钮始终被禁用
            
            if is_modified:
                self.current_edits["PURPOSE"] = current_text
            elif "PURPOSE" in self.current_edits:
                del self.current_edits["PURPOSE"]
                
            # 发出内容更新信号
            self.content_updated.emit(self.document_path)
            
            # 在向导模式下，当内容更改时自动保存到文档
            if self.document_path:
                logger.info("在向导模式下，内容更改后自动保存到文档")
                # 这里我们不需要立即保存，因为混入类中的预设加载方法会触发保存
                # 或者我们可以添加一个自动保存功能
                
        except Exception as e:
            logger.error(f"处理PURPOSE编辑内容变化时出错: {e}")

    def _on_conclusions_content_changed(self):
        """重写CONCLUSIONS内容变化处理，禁用保存按钮"""
        try:
            current_text = self.edit_conclusions_content.toPlainText()
            original_text = self.original_conclusions_content.toPlainText()
            is_modified = current_text != original_text
            
            # 更新缓存内容以保持状态
            self._cached_conclusions_content = current_text
            
            # 不启用混入类中的保存按钮，因为我们使用向导导航按钮
            if hasattr(self, 'save_btn') and self.save_btn:
                self.save_btn.setEnabled(False)  # 确保保存按钮始终被禁用
            
            if is_modified:
                self.current_edits["CONCLUSIONS"] = current_text
            elif "CONCLUSIONS" in self.current_edits:
                del self.current_edits["CONCLUSIONS"]
                
            # 发出内容更新信号
            self.content_updated.emit(self.document_path)
            
            # 在向导模式下，当内容更改时自动保存到文档
            if self.document_path:
                logger.info("在向导模式下，内容更改后自动保存到文档")
                # 这里我们不需要立即保存，因为混入类中的预设加载方法会触发保存
                
        except Exception as e:
            logger.error(f"处理CONCLUSIONS编辑内容变化时出错: {e}")

    def get_document_path(self) -> str:
        """
        获取文档路径

        Returns:
            文档路径
        """
        return self.document_path

    def get_current_edits(self):
        """
        获取当前编辑内容

        Returns:
            当前编辑的内容字典
        """
        return self.current_edits
    
    def _load_default_document(self):
        """加载默认文档路径"""
        # 在向导上下文中，文档路径通常由外部设置
        # 当前页面依赖外部调用set_document_path方法来设置文档
        # 以确保与向导流程的一致性
        pass
    
    def _load_selected_purpose_preset(self):
        """加载选中的PURPOSE预设描述"""
        try:
            self._apply_selected_preset(
                self.purpose_preset_list,
                self.edit_purpose_content,
                self._on_purpose_content_changed,
                self.save_current_edits_to_document,
            )
                
        except Exception as e:
            logger.error(f"加载选中PURPOSE预设时出错: {e}")
    
    def _load_selected_conclusions_preset(self):
        """加载选中的CONCLUSIONS预设描述"""
        try:
            self._apply_selected_preset(
                self.conclusions_preset_list,
                self.edit_conclusions_content,
                self._on_conclusions_content_changed,
                self.save_current_edits_to_document,
            )
                
        except Exception as e:
            logger.error(f"加载选中CONCLUSIONS预设时出错: {e}")

    def load_document_content(self):
        """加载文档内容"""
        try:
            logger.info(f"开始加载文档内容，文件路径: {self.file_path}")
            
            # 检查编辑器组件是否存在
            if not hasattr(self, 'edit_purpose_content') or self.edit_purpose_content is None:
                logger.error("edit_purpose_content 未初始化")
                return
            if not hasattr(self, 'edit_conclusions_content') or self.edit_conclusions_content is None:
                logger.error("edit_conclusions_content 未初始化")
                return
            
            # 委托文档工作流协作者
            result = self._document_workflow.load_content(
                file_path=self.file_path,
                edit_purpose=self.edit_purpose_content,
                edit_conclusions=self.edit_conclusions_content,
                cached_purpose=self._cached_purpose_content,
                cached_conclusions=self._cached_conclusions_content,
                content_loaded=self._content_loaded,
            )
            
            # 更新缓存
            self._cached_purpose_content = result["purpose_content"]
            self._cached_conclusions_content = result["conclusions_content"]
            
            # 保存原始内容快照
            originals = self._document_workflow.snapshot_originals(
                purpose_content=result["purpose_content"],
                conclusions_content=result["conclusions_content"],
            )
            self.original_purpose_content = originals["original_purpose_content"]
            self.original_conclusions_content = originals["original_conclusions_content"]
            
            # 连接内容变化信号
            logger.info("连接内容变化信号")
            self.edit_purpose_content.textChanged.connect(self._on_purpose_content_changed)
            self.edit_conclusions_content.textChanged.connect(self._on_conclusions_content_changed)
            
            # 加载预设描述
            logger.info("开始加载预设描述")
            if hasattr(self, 'purpose_preset_list') and self.purpose_preset_list is not None:
                self._document_workflow.load_preset_descriptions("PURPOSE", self.purpose_preset_list)
            else:
                logger.warning("PURPOSE 预设列表组件未初始化")
            
            if hasattr(self, 'conclusions_preset_list') and self.conclusions_preset_list is not None:
                self._document_workflow.load_preset_descriptions("CONCLUSIONS", self.conclusions_preset_list)
            else:
                logger.warning("CONCLUSIONS 预设列表组件未初始化")
            
            # 标记内容已加载
            self._content_loaded = True
            logger.info("文档内容加载完成")
            
        except Exception as e:
            logger.error(f"加载文档内容时出错: {e}")
            logger.error("加载文档内容失败", exc_info=True)

    def save_current_edits_to_document(self):
        """
        将当前编辑的内容保存到文档
        """
        try:
            if not self.document_path:
                logger.warning("文档路径未设置，无法保存")
                return False
            
            # 检查是否有编辑器组件
            if not hasattr(self, 'edit_purpose_content') or not self.edit_purpose_content:
                logger.error("edit_purpose_content 未初始化")
                return False
            if not hasattr(self, 'edit_conclusions_content') or not self.edit_conclusions_content:
                logger.error("edit_conclusions_content 未初始化")
                return False
            
            # 获取当前编辑器中的内容
            current_purpose_content = self.edit_purpose_content.toPlainText()
            current_conclusions_content = self.edit_conclusions_content.toPlainText()
            
            # 更新缓存内容以保持状态
            self._cached_purpose_content = current_purpose_content
            self._cached_conclusions_content = current_conclusions_content
            
            # 获取原始内容
            original_purpose_content = self.original_purpose_content.toPlainText() if self.original_purpose_content else ""
            original_conclusions_content = self.original_conclusions_content.toPlainText() if self.original_conclusions_content else ""
            
            # 委托文档工作流协作者
            result = self._document_workflow.save_edits(
                document_path=self.document_path,
                current_purpose=current_purpose_content,
                current_conclusions=current_conclusions_content,
                original_purpose=original_purpose_content,
                original_conclusions=original_conclusions_content,
            )

            if result["success"] and result["had_changes"]:
                if self.original_purpose_content:
                    self.original_purpose_content.setPlainText(current_purpose_content)
                if self.original_conclusions_content:
                    self.original_conclusions_content.setPlainText(current_conclusions_content)

                self.content_updated.emit(self.document_path)

            return result["success"]
                
        except Exception as e:
            logger.error(f"保存当前编辑到文档时出错: {e}")
            logger.error("保存当前编辑到文档失败", exc_info=True)
            return False
