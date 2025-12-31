"""
正文内容编辑对话框视图
提供交互式编辑Word文档正文内容的界面
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTextEdit, QListWidget, QListWidgetItem, QPushButton, 
    QLabel, QGroupBox, QFormLayout, QFrame, QScrollArea
)
from PyQt5.QtCore import pyqtSignal
from src.core.logger import logger
from src.features.document_parser.service.body_content_service import BodyContentService


class BodyContentDialog(QDialog):
    """
    正文内容编辑对话框
    提供交互式编辑Word文档正文内容的界面
    """
    
    # 自定义信号
    content_updated = pyqtSignal(dict)  # 传递更新的内容字典
    
    def __init__(self, file_path: str, parent=None):
        """
        初始化正文内容编辑对话框

        Args:
            file_path: Word文档路径
            parent: 父窗口
        """
        super().__init__(parent)
        self.file_path = file_path
        self.current_edits = {}
        self.body_content_service = BodyContentService()
        
        self.setWindowTitle("正文内容编辑")
        self.setGeometry(200, 200, 1200, 800)
        
        # 初始化UI
        self.init_ui()
        
        # 加载文档内容
        self.load_document_content()
    
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel(f"编辑文档: {self.file_path}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 创建分割窗口
        splitter = QSplitter()
        
        # 左侧：内容编辑区域（分上下两部分）
        left_widget = self._create_content_edit_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：预设描述区域（分上下两部分）
        right_widget = self._create_preset_panel()
        splitter.addWidget(right_widget)
        
        splitter.setSizes([600, 600])  # 设置初始大小
        main_layout.addWidget(splitter)
        
        # 按钮区域
        button_layout = self._create_buttons()
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def _create_content_edit_panel(self):
        """创建内容编辑面板"""
        panel = QFrame()
        layout = QVBoxLayout()
        
        # 标题
        label = QLabel("内容编辑")
        label.setStyleSheet("font-weight: bold; margin: 5px;")
        layout.addWidget(label)
        
        # PURPOSE 部分
        edit_purpose_group = QGroupBox("PURPOSE")
        edit_purpose_layout = QVBoxLayout()
        self.edit_purpose_content = QTextEdit()
        edit_purpose_layout.addWidget(self.edit_purpose_content)
        edit_purpose_group.setLayout(edit_purpose_layout)
        layout.addWidget(edit_purpose_group)
        
        # CONCLUSIONS 部分
        edit_conclusions_group = QGroupBox("CONCLUSIONS")
        edit_conclusions_layout = QVBoxLayout()
        self.edit_conclusions_content = QTextEdit()
        edit_conclusions_layout.addWidget(self.edit_conclusions_content)
        edit_conclusions_group.setLayout(edit_conclusions_layout)
        layout.addWidget(edit_conclusions_group)
        
        # 连接编辑器信号
        # 暂时不连接信号，等加载完文档内容后再连接
        # self.edit_purpose_content.textChanged.connect(self._on_purpose_content_changed)
        # self.edit_conclusions_content.textChanged.connect(self._on_conclusions_content_changed)
        
        panel.setLayout(layout)
        
        return panel
    
    def _create_preset_panel(self):
        """创建预设面板"""
        panel = QFrame()
        layout = QVBoxLayout()
        
        # 标题
        label = QLabel("预设描述")
        label.setStyleSheet("font-weight: bold; margin: 5px;")
        layout.addWidget(label)
        
        # PURPOSE 预设部分
        purpose_preset_group = QGroupBox("PURPOSE 预设描述")
        purpose_preset_layout = QVBoxLayout()
        
        # 预设描述列表
        self.purpose_preset_list = QListWidget()
        purpose_preset_layout.addWidget(self.purpose_preset_list)
        
        # 预设描述按钮
        purpose_preset_button_layout = QHBoxLayout()
        
        self.load_purpose_preset_btn = QPushButton("加载选中描述")
        self.load_purpose_preset_btn.clicked.connect(self._load_selected_purpose_preset)
        purpose_preset_button_layout.addWidget(self.load_purpose_preset_btn)
        
        self.add_purpose_preset_btn = QPushButton("添加到预设")
        self.add_purpose_preset_btn.clicked.connect(self._add_current_purpose_to_preset)
        purpose_preset_button_layout.addWidget(self.add_purpose_preset_btn)
        
        purpose_preset_button_layout.addStretch()  # 添加弹性空间
        purpose_preset_layout.addLayout(purpose_preset_button_layout)
        purpose_preset_group.setLayout(purpose_preset_layout)
        layout.addWidget(purpose_preset_group)
        
        # CONCLUSIONS 预设部分
        conclusions_preset_group = QGroupBox("CONCLUSIONS 预设描述")
        conclusions_preset_layout = QVBoxLayout()
        
        # 预设描述列表
        self.conclusions_preset_list = QListWidget()
        conclusions_preset_layout.addWidget(self.conclusions_preset_list)
        
        # 预设描述按钮
        conclusions_preset_button_layout = QHBoxLayout()
        
        self.load_conclusions_preset_btn = QPushButton("加载选中描述")
        self.load_conclusions_preset_btn.clicked.connect(self._load_selected_conclusions_preset)
        conclusions_preset_button_layout.addWidget(self.load_conclusions_preset_btn)
        
        self.add_conclusions_preset_btn = QPushButton("添加到预设")
        self.add_conclusions_preset_btn.clicked.connect(self._add_current_conclusions_to_preset)
        conclusions_preset_button_layout.addWidget(self.add_conclusions_preset_btn)
        
        conclusions_preset_button_layout.addStretch()  # 添加弹性空间
        conclusions_preset_layout.addLayout(conclusions_preset_button_layout)
        conclusions_preset_group.setLayout(conclusions_preset_layout)
        layout.addWidget(conclusions_preset_group)
        
        panel.setLayout(layout)
        
        return panel
    
    def _create_buttons(self):
        """创建按钮布局"""
        layout = QHBoxLayout()
        
        # 保存按钮
        self.save_btn = QPushButton("保存修改")
        self.save_btn.clicked.connect(self._save_changes)
        self.save_btn.setEnabled(False)  # 初始时禁用
        layout.addWidget(self.save_btn)
        
        # 预览按钮
        self.preview_btn = QPushButton("预览")
        self.preview_btn.clicked.connect(self._preview_changes)
        layout.addWidget(self.preview_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # 添加弹性空间
        layout.addStretch()
        
        return layout
    
    def load_document_content(self):
        """加载文档内容"""
        try:
            logger.info(f"开始加载文档内容，文件路径: {self.file_path}")
            
            # 使用优化后的方法，一次性获取所有需要的内容，只需遍历文档一次
            all_sections_content = self.body_content_service.get_all_content_sections(self.file_path)
            
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
            
            # 保存原始内容用于比较
            self.original_purpose_content = QTextEdit()
            self.original_purpose_content.setPlainText(purpose_content)
            self.original_conclusions_content = QTextEdit()
            self.original_conclusions_content.setPlainText(conclusions_content)
            
            # 现在连接信号，确保原始内容已设置
            self.edit_purpose_content.textChanged.connect(self._on_purpose_content_changed)
            self.edit_conclusions_content.textChanged.connect(self._on_conclusions_content_changed)
            
            # 加载预设描述
            self._load_preset_descriptions("PURPOSE", self.purpose_preset_list)
            self._load_preset_descriptions("CONCLUSIONS", self.conclusions_preset_list)
            
            logger.info("文档内容加载完成")
            
        except Exception as e:
            logger.error(f"加载文档内容时出错: {e}")
    
    def _load_preset_descriptions(self, category: str, list_widget: QListWidget):
        """加载预设描述"""
        try:
            # 从服务获取预设描述
            descriptions = self.body_content_service.get_predefined_descriptions(category)
            
            # 清空现有项目
            list_widget.clear()
            
            # 添加预设描述
            for desc in descriptions:
                item = QListWidgetItem(desc[:50] + "..." if len(desc) > 50 else desc)
                item.setData(100, desc)  # 存储完整描述
                list_widget.addItem(item)
                
        except Exception as e:
            logger.error(f"加载预设描述时出错: {e}")
    
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
                
        except Exception as e:
            logger.error(f"加载选中CONCLUSIONS预设时出错: {e}")
    
    def _add_current_purpose_to_preset(self):
        """将当前PURPOSE内容添加到预设"""
        try:
            current_text = self.edit_purpose_content.toPlainText().strip()
            if current_text:
                # 添加到服务的预设描述
                self.body_content_service.add_predefined_description("PURPOSE", current_text)
                
                # 重新加载预设列表
                self._load_preset_descriptions("PURPOSE", self.purpose_preset_list)
                
                logger.info(f"将内容添加到 PURPOSE 预设: {current_text[:50]}...")
                
        except Exception as e:
            logger.error(f"添加当前PURPOSE内容到预设时出错: {e}")
    
    def _add_current_conclusions_to_preset(self):
        """将当前CONCLUSIONS内容添加到预设"""
        try:
            current_text = self.edit_conclusions_content.toPlainText().strip()
            if current_text:
                # 添加到服务的预设描述
                self.body_content_service.add_predefined_description("CONCLUSIONS", current_text)
                
                # 重新加载预设列表
                self._load_preset_descriptions("CONCLUSIONS", self.conclusions_preset_list)
                
                logger.info(f"将内容添加到 CONCLUSIONS 预设: {current_text[:50]}...")
                
        except Exception as e:
            logger.error(f"添加当前CONCLUSIONS内容到预设时出错: {e}")
    
    def _on_purpose_content_changed(self):
        """处理PURPOSE编辑内容变化"""
        try:
            current_text = self.edit_purpose_content.toPlainText()
            original_text = self.original_purpose_content.toPlainText()
            is_modified = current_text != original_text
            self.save_btn.setEnabled(is_modified or 
                                   (self.edit_conclusions_content.toPlainText() != 
                                    self.original_conclusions_content.toPlainText()))
            
            if is_modified:
                self.current_edits["PURPOSE"] = current_text
            elif "PURPOSE" in self.current_edits:
                del self.current_edits["PURPOSE"]
                
        except Exception as e:
            logger.error(f"处理PURPOSE编辑内容变化时出错: {e}")
    
    def _on_conclusions_content_changed(self):
        """处理CONCLUSIONS编辑内容变化"""
        try:
            current_text = self.edit_conclusions_content.toPlainText()
            original_text = self.original_conclusions_content.toPlainText()
            is_modified = current_text != original_text
            self.save_btn.setEnabled(is_modified or 
                                   (self.edit_purpose_content.toPlainText() != 
                                    self.original_purpose_content.toPlainText()))
            
            if is_modified:
                self.current_edits["CONCLUSIONS"] = current_text
            elif "CONCLUSIONS" in self.current_edits:
                del self.current_edits["CONCLUSIONS"]
                
        except Exception as e:
            logger.error(f"处理CONCLUSIONS编辑内容变化时出错: {e}")
    
    def _save_changes(self):
        """保存修改"""
        try:
            logger.info("开始保存修改")
            
            # 先获取当前文档的所有章节内容，以确定是否需要更新到文档末尾
            all_sections_content = self.body_content_service.get_all_content_sections(self.file_path)
            
            # 准备批量更新的数据
            updates = {}
            
            # 添加 PURPOSE 到 CONCLUSIONS 的内容更新
            if "PURPOSE" in self.current_edits:
                new_content = self.current_edits["PURPOSE"]
                logger.info(f"准备更新 PURPOSE 到 CONCLUSIONS 的内容，新内容长度: {len(new_content)}")
                updates["PURPOSE-CONCLUSIONS"] = new_content
            
            # 添加 CONCLUSIONS 到 SAMPLE DESCRIPTION 的内容更新
            if "CONCLUSIONS" in self.current_edits:
                new_content = self.current_edits["CONCLUSIONS"]
                logger.info(f"准备更新 CONCLUSIONS 到 SAMPLE DESCRIPTION 的内容，新内容长度: {len(new_content)}")
                
                # 检查是否存在 CONCLUSIONS-SAMPLE DESCRIPTION 的内容
                if "CONCLUSIONS-SAMPLE DESCRIPTION" in all_sections_content:
                    updates["CONCLUSIONS-SAMPLE DESCRIPTION"] = new_content
                else:
                    # 如果不存在 SAMPLE DESCRIPTION，更新到文档末尾
                    updates["CONCLUSIONS-END"] = new_content
            
            if updates:
                # 使用批量更新方法，只需打开文档一次
                success = self.body_content_service.update_multiple_sections_content(self.file_path, updates)
                
                if success:
                    logger.info(f"成功更新 {len(updates)} 个部分的内容")
                    # 发送信号通知控制器更新内容
                    self.content_updated.emit(self.current_edits)
                    self.accept()  # 关闭对话框
                else:
                    logger.error("批量更新失败")
            else:
                logger.warning("没有修改内容需要保存")
                
        except Exception as e:
            logger.error(f"保存修改时出错: {e}")
    
    def _preview_changes(self):
        """预览修改"""
        try:
            purpose_text = self.edit_purpose_content.toPlainText()
            conclusions_text = self.edit_conclusions_content.toPlainText()
            logger.info(f"PURPOSE内容预览: {purpose_text[:100]}...")
            logger.info(f"CONCLUSIONS内容预览: {conclusions_text[:100]}...")
            
        except Exception as e:
            logger.error(f"预览修改时出错: {e}")