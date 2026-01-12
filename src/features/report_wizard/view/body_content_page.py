"""
正文内容页面视图
实现向导中正文内容编辑页面的UI组件
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QFrame, QTextEdit, QFileDialog,
    QSplitter, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import pyqtSignal
from src.features.content_editor.service.body_content_service import BodyContentService
from src.core.logger import logger
from src.utils.document_editor_mixin import DocumentEditorMixin


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
        # 添加状态保持变量
        self._cached_purpose_content = ""
        self._cached_conclusions_content = ""
        self._content_loaded = False  # 标记内容是否已加载
        logger.info(f"开始初始化正文内容页面，混入类初始化状态检查:")
        logger.info(f"  - body_content_service 实例: {self.body_content_service is not None}")
        logger.info(f"  - body_content_service 预设描述: {self.body_content_service.predefined_descriptions}")
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
            current_item = self.purpose_preset_list.currentItem()
            if current_item:
                preset_text = current_item.data(100)
                current_text = self.edit_purpose_content.toPlainText()
                # 将预设文本添加到当前编辑内容的末尾
                if current_text and not current_text.endswith('\n'):
                    preset_text = '\n' + preset_text
                new_text = current_text + preset_text
                self.edit_purpose_content.setPlainText(new_text)
                
                # 触发内容变化事件以更新保存按钮状态
                self._on_purpose_content_changed()
                
                # 在向导模式下，立即保存更改到文档
                if self.document_path:
                    logger.info("在向导模式下，加载PURPOSE预设后立即保存到文档")
                    self.save_current_edits_to_document()
                
        except Exception as e:
            logger.error(f"加载选中PURPOSE预设时出错: {e}")
    
    def _load_selected_conclusions_preset(self):
        """加载选中的CONCLUSIONS预设描述"""
        try:
            current_item = self.conclusions_preset_list.currentItem()
            if current_item:
                preset_text = current_item.data(100)
                current_text = self.edit_conclusions_content.toPlainText()
                # 将预设文本添加到当前编辑内容的末尾
                if current_text and not current_text.endswith('\n'):
                    preset_text = '\n' + preset_text
                new_text = current_text + preset_text
                self.edit_conclusions_content.setPlainText(new_text)
                
                # 触发内容变化事件以更新保存按钮状态
                self._on_conclusions_content_changed()
                
                # 在向导模式下，立即保存更改到文档
                if self.document_path:
                    logger.info("在向导模式下，加载CONCLUSIONS预设后立即保存到文档")
                    self.save_current_edits_to_document()
                
        except Exception as e:
            logger.error(f"加载选中CONCLUSIONS预设时出错: {e}")

    def load_document_content(self):
        """加载文档内容"""
        try:
            logger.info(f"开始加载文档内容，文件路径: {self.file_path}")
            
            # 检查 body_content_service 是否存在
            if not hasattr(self, 'body_content_service') or not self.body_content_service:
                logger.error("body_content_service 未初始化")
                return
            
            # 检查编辑器组件是否已初始化
            logger.info(f"检查编辑器组件初始化状态:")
            logger.info(f"  - edit_purpose_content: {getattr(self, 'edit_purpose_content', 'NOT SET') is not None}")
            logger.info(f"  - edit_conclusions_content: {getattr(self, 'edit_conclusions_content', 'NOT SET') is not None}")
            logger.info(f"  - purpose_preset_list: {getattr(self, 'purpose_preset_list', 'NOT SET') is not None}")
            logger.info(f"  - conclusions_preset_list: {getattr(self, 'conclusions_preset_list', 'NOT SET') is not None}")
            
            # 检查编辑器组件是否存在
            if not hasattr(self, 'edit_purpose_content') or self.edit_purpose_content is None:
                logger.error("edit_purpose_content 未初始化")
                return
            if not hasattr(self, 'edit_conclusions_content') or self.edit_conclusions_content is None:
                logger.error("edit_conclusions_content 未初始化")
                return
            
            # 检查是否已有缓存内容，如果有则优先使用缓存内容以保持状态
            if self._content_loaded and hasattr(self, '_cached_purpose_content') and hasattr(self, '_cached_conclusions_content'):
                logger.info("检测到已缓存的内容，使用缓存内容以保持状态")
                self.edit_purpose_content.setPlainText(self._cached_purpose_content)
                self.edit_conclusions_content.setPlainText(self._cached_conclusions_content)
            else:
                # 使用优化后的方法，一次性获取所有需要的内容，只需遍历文档一次
                all_sections_content = self.body_content_service.get_all_content_sections(self.file_path)
                logger.info(f"获取到的所有章节内容: {list(all_sections_content.keys())}")
                
                # 获取 PURPOSE 到 CONCLUSIONS 的内容
                purpose_content = all_sections_content.get("PURPOSE-CONCLUSIONS", "")
                logger.info(f"PURPOSE后内容长度: {len(purpose_content)}, 内容预览: {purpose_content[:100] if purpose_content else 'None'}")
                self.edit_purpose_content.setPlainText(purpose_content)
                
                # 获取 CONCLUSIONS 到 SAMPLE DESCRIPTION 的内容
                conclusions_content = all_sections_content.get("CONCLUSIONS-SAMPLE DESCRIPTION", "")
                
                # 如果没有找到 SAMPLE DESCRIPTION，则尝试获取 CONCLUSIONS 之后的所有内容
                if not conclusions_content and "CONCLUSIONS-SAMPLE DESCRIPTION" not in all_sections_content:
                    conclusions_content = all_sections_content.get("CONCLUSIONS-END", "")
                    logger.info(f"CONCLUSIONS后内容长度（到文档末尾或表格停止）: {len(conclusions_content)}, 内容预览: {conclusions_content[:100] if conclusions_content else 'None'}")
                else:
                    logger.info(f"CONCLUSIONS后内容长度（SAMPLE DESCRIPTION之前）: {len(conclusions_content)}, 内容预览: {conclusions_content[:100] if conclusions_content else 'None'}")
                
                self.edit_conclusions_content.setPlainText(conclusions_content)
                
                # 保存到缓存中
                self._cached_purpose_content = purpose_content
                self._cached_conclusions_content = conclusions_content
            
            # 保存原始内容用于比较
            self.original_purpose_content = QTextEdit()
            self.original_purpose_content.setPlainText(self._cached_purpose_content)
            self.original_conclusions_content = QTextEdit()
            self.original_conclusions_content.setPlainText(self._cached_conclusions_content)
            
            # 现在连接信号，确保原始内容已设置
            logger.info("连接内容变化信号")
            self.edit_purpose_content.textChanged.connect(self._on_purpose_content_changed)
            self.edit_conclusions_content.textChanged.connect(self._on_conclusions_content_changed)
            
            # 加载预设描述 - 添加调试信息
            logger.info("开始加载预设描述")
            logger.info(f"PURPOSE 预设列表组件状态: {getattr(self, 'purpose_preset_list', None) is not None}")
            logger.info(f"CONCLUSIONS 预设列表组件状态: {getattr(self, 'conclusions_preset_list', None) is not None}")
            
            # 检查 body_content_service 中的预设描述
            logger.info(f"body_content_service 中的 PURPOSE 预设: {self.body_content_service.get_predefined_descriptions('PURPOSE')}")
            logger.info(f"body_content_service 中的 CONCLUSIONS 预设: {self.body_content_service.get_predefined_descriptions('CONCLUSIONS')}")
            
            # 检查预设列表组件是否存在
            if hasattr(self, 'purpose_preset_list') and self.purpose_preset_list is not None:
                self._load_preset_descriptions("PURPOSE", self.purpose_preset_list)
            else:
                logger.warning("PURPOSE 预设列表组件未初始化")
            
            if hasattr(self, 'conclusions_preset_list') and self.conclusions_preset_list is not None:
                self._load_preset_descriptions("CONCLUSIONS", self.conclusions_preset_list)
            else:
                logger.warning("CONCLUSIONS 预设列表组件未初始化")
            
            # 标记内容已加载
            self._content_loaded = True
            logger.info("文档内容加载完成")
            
        except Exception as e:
            logger.error(f"加载文档内容时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")

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
            
            # 检查是否有更改
            purpose_changed = current_purpose_content != original_purpose_content
            conclusions_changed = current_conclusions_content != original_conclusions_content
            
            if not purpose_changed and not conclusions_changed:
                logger.info("没有内容更改，无需保存")
                return True
            
            # 获取当前文档的所有章节内容
            all_sections_content = self.body_content_service.get_all_content_sections(self.document_path)
            
            # 准备批量更新的数据
            updates = {}
            if purpose_changed:
                updates["PURPOSE-CONCLUSIONS"] = current_purpose_content
                logger.info(f"准备更新 PURPOSE 内容，长度: {len(current_purpose_content)}")
            
            if conclusions_changed:
                # 检查是否存在 CONCLUSIONS-SAMPLE DESCRIPTION 的内容
                if "CONCLUSIONS-SAMPLE DESCRIPTION" in all_sections_content:
                    updates["CONCLUSIONS-SAMPLE DESCRIPTION"] = current_conclusions_content
                else:
                    # 如果不存在 SAMPLE DESCRIPTION，更新到文档末尾
                    updates["CONCLUSIONS-END"] = current_conclusions_content
                logger.info(f"准备更新 CONCLUSIONS 内容，长度: {len(current_conclusions_content)}")
            
            if updates:
                # 使用批量更新方法
                success = self.body_content_service.update_multiple_sections_content(self.document_path, updates)
                
                if success:
                    logger.info(f"成功更新 {len(updates)} 个部分的内容")
                    
                    # 更新原始内容，避免重复保存相同的更改
                    if self.original_purpose_content:
                        self.original_purpose_content.setPlainText(current_purpose_content)
                    if self.original_conclusions_content:
                        self.original_conclusions_content.setPlainText(current_conclusions_content)
                    
                    # 发送信号通知内容已更新
                    self.content_updated.emit(self.document_path)
                    return True
                else:
                    logger.error("更新文档内容失败")
                    return False
            else:
                logger.info("没有内容更改需要保存")
                return True
                
        except Exception as e:
            logger.error(f"保存当前编辑到文档时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return False
