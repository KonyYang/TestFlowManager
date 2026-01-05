"""
文档编辑器基类组件
提供文档编辑功能的共用组件和方法，可以被QDialog和QWidget类型使用
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTextEdit, QListWidget, QListWidgetItem, QPushButton, 
    QLabel, QGroupBox, QFormLayout, QFrame
)
from PyQt5.QtCore import pyqtSignal
from src.core.logger import logger
# 延迟导入 BodyContentService 以避免循环导入
# from src.features.content_editor.service.body_content_service import BodyContentService


class DocumentEditorMixin:
    """
    文档编辑器混入类
    提供文档编辑功能的通用组件和方法
    """
    
    def _init_document_editor_components(self, file_path: str):
        """
        初始化文档编辑器组件
        
        Args:
            file_path: Word文档路径
        """
        logger.info(f"开始初始化文档编辑器组件，文件路径: {file_path}")
        self.file_path = file_path
        self.current_edits = {}
        
        # 只有当 body_content_service 不存在时才创建新实例
        if not hasattr(self, 'body_content_service') or self.body_content_service is None:
            # 延迟导入 BodyContentService 以避免循环导入
            from src.features.content_editor.service.body_content_service import BodyContentService
            self.body_content_service = BodyContentService()
            logger.info(f"BodyContentService 实例已创建，预设描述内容: {self.body_content_service.predefined_descriptions}")
        else:
            logger.info(f"BodyContentService 实例已存在，预设描述内容: {self.body_content_service.predefined_descriptions}")

        # 不要重新初始化编辑器、预设列表等组件，因为它们可能已经在UI初始化时创建了
        # 只初始化那些需要的属性
        if not hasattr(self, 'current_edits') or self.current_edits is None:
            self.current_edits = {}
        
        # 初始化按钮
        if not hasattr(self, 'save_btn'):
            self.save_btn = None
        
        # 初始化原始内容存储
        if not hasattr(self, 'original_purpose_content'):
            self.original_purpose_content = None
        if not hasattr(self, 'original_conclusions_content'):
            self.original_conclusions_content = None
    
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
        
        panel.setLayout(layout)
        
        return panel
    
    def _create_preset_panel(self):
        """创建预设面板"""
        logger.info("开始创建预设面板")
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
        logger.info(f"PURPOSE 预设列表已创建，对象ID: {id(self.purpose_preset_list)}")
        purpose_preset_layout.addWidget(self.purpose_preset_list)
        
        # 预设描述按钮
        purpose_preset_button_layout = QHBoxLayout()
        
        self.load_purpose_preset_btn = QPushButton("加载选中描述")
        purpose_preset_button_layout.addWidget(self.load_purpose_preset_btn)
        
        self.add_purpose_preset_btn = QPushButton("添加到预设")
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
        logger.info(f"CONCLUSIONS 预设列表已创建，对象ID: {id(self.conclusions_preset_list)}")
        conclusions_preset_layout.addWidget(self.conclusions_preset_list)
        
        # 预设描述按钮
        conclusions_preset_button_layout = QHBoxLayout()
        
        self.load_conclusions_preset_btn = QPushButton("加载选中描述")
        conclusions_preset_button_layout.addWidget(self.load_conclusions_preset_btn)
        
        self.add_conclusions_preset_btn = QPushButton("添加到预设")
        conclusions_preset_button_layout.addWidget(self.add_conclusions_preset_btn)
        
        conclusions_preset_button_layout.addStretch()  # 添加弹性空间
        conclusions_preset_layout.addLayout(conclusions_preset_button_layout)
        conclusions_preset_group.setLayout(conclusions_preset_layout)
        layout.addWidget(conclusions_preset_group)
        
        panel.setLayout(layout)
        
        logger.info("预设面板创建完成")
        # 调试：检查预设列表是否已初始化
        if hasattr(self, 'purpose_preset_list') and self.purpose_preset_list:
            logger.info(f"PURPOSE 预设列表已初始化，项目数量: {self.purpose_preset_list.count()}")
        else:
            logger.warning("PURPOSE 预设列表未初始化或为空")
        if hasattr(self, 'conclusions_preset_list') and self.conclusions_preset_list:
            logger.info(f"CONCLUSIONS 预设列表已初始化，项目数量: {self.conclusions_preset_list.count()}")
        else:
            logger.warning("CONCLUSIONS 预设列表未初始化或为空")
        
        # 额外调试：检查混入类初始化状态
        logger.info(f"混入类初始化状态检查:")
        logger.info(f"  - file_path: {getattr(self, 'file_path', '未设置')}")
        logger.info(f"  - body_content_service: {getattr(self, 'body_content_service', '未设置') is not None}")
        logger.info(f"  - edit_purpose_content: {getattr(self, 'edit_purpose_content', '未设置') is not None}")
        logger.info(f"  - edit_conclusions_content: {getattr(self, 'edit_conclusions_content', '未设置') is not None}")
        
        # 检查 body_content_service 是否存在以及预设描述是否加载
        if hasattr(self, 'body_content_service') and self.body_content_service:
            logger.info(f"body_content_service 预设描述内容: {self.body_content_service.predefined_descriptions}")
            
            # 如果 body_content_service 已存在，立即加载预设描述
            logger.info("body_content_service 已存在，立即加载预设描述")
            self._load_preset_descriptions("PURPOSE", self.purpose_preset_list)
            self._load_preset_descriptions("CONCLUSIONS", self.conclusions_preset_list)
        else:
            logger.warning("body_content_service 未初始化或不存在")
        
        return panel
    
    def _create_buttons(self):
        """创建按钮布局"""
        layout = QHBoxLayout()
        
        # 保存按钮
        self.save_btn = QPushButton("保存修改")
        self.save_btn.setEnabled(False)  # 初始时禁用
        layout.addWidget(self.save_btn)
        

        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        layout.addWidget(cancel_btn)
        
        # 添加弹性空间
        layout.addStretch()
        
        return layout
    
    def _connect_common_signals(self):
        """连接共用信号"""
        # 预设按钮信号连接
        if hasattr(self, 'load_purpose_preset_btn') and self.load_purpose_preset_btn:
            self.load_purpose_preset_btn.clicked.connect(self._load_selected_purpose_preset)
        if hasattr(self, 'add_purpose_preset_btn') and self.add_purpose_preset_btn:
            self.add_purpose_preset_btn.clicked.connect(self._add_current_purpose_to_preset)
        if hasattr(self, 'load_conclusions_preset_btn') and self.load_conclusions_preset_btn:
            self.load_conclusions_preset_btn.clicked.connect(self._load_selected_conclusions_preset)
        if hasattr(self, 'add_conclusions_preset_btn') and self.add_conclusions_preset_btn:
            self.add_conclusions_preset_btn.clicked.connect(self._add_current_conclusions_to_preset)
        
        # 保存按钮信号连接
        if hasattr(self, 'save_btn') and self.save_btn:
            self.save_btn.clicked.connect(self._save_changes)
    
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
            
            # 保存原始内容用于比较
            self.original_purpose_content = QTextEdit()
            self.original_purpose_content.setPlainText(purpose_content)
            self.original_conclusions_content = QTextEdit()
            self.original_conclusions_content.setPlainText(conclusions_content)
            
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
            
            logger.info("文档内容加载完成")
            
        except Exception as e:
            logger.error(f"加载文档内容时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
    
    def _load_preset_descriptions(self, category: str, list_widget: QListWidget):
        """加载预设描述"""
        logger.info(f"开始加载 {category} 预设描述")
        try:
            # 检查 body_content_service 是否存在
            if not hasattr(self, 'body_content_service') or not self.body_content_service:
                logger.error(f"body_content_service 未初始化，无法加载 {category} 预设描述")
                return
            
            # 从服务获取预设描述
            descriptions = self.body_content_service.get_predefined_descriptions(category)
            logger.info(f"获取到 {len(descriptions)} 个 {category} 预设描述: {descriptions}")
            
            # 检查列表小部件是否已初始化
            if list_widget is None:
                logger.error(f"{category} 预设列表未初始化")
                return
            
            logger.info(f"{category} 预设列表已初始化，开始清空并添加项目")
            
            # 清空现有项目
            list_widget.clear()
            
            # 添加预设描述
            for i, desc in enumerate(descriptions):
                logger.info(f"添加 {category} 预设项 {i}: {desc[:50] + '...' if len(desc) > 50 else desc}")
                item = QListWidgetItem(desc[:50] + "..." if len(desc) > 50 else desc)
                item.setData(100, desc)  # 存储完整描述
                list_widget.addItem(item)
            
            logger.info(f"{category} 预设列表已填充，总项目数: {list_widget.count()}")
            
        except Exception as e:
            logger.error(f"加载预设描述时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
    
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
                if hasattr(self, 'file_path') and self.file_path:
                    logger.info("在向导模式下，加载预设后立即保存到文档")
                    self._save_changes_to_document()
                
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
                if hasattr(self, 'file_path') and self.file_path:
                    logger.info("在向导模式下，加载预设后立即保存到文档")
                    self._save_changes_to_document()
                
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
            
            if is_modified:
                self.current_edits["PURPOSE"] = current_text
            elif "PURPOSE" in self.current_edits:
                del self.current_edits["PURPOSE"]
            
            # 更新保存按钮状态
            self._update_save_button_state()
                
            # 发出内容更新信号
            if hasattr(self, 'content_updated'):
                self.content_updated.emit(self.file_path)
                
        except Exception as e:
            logger.error(f"处理PURPOSE编辑内容变化时出错: {e}")
    
    def _on_conclusions_content_changed(self):
        """处理CONCLUSIONS编辑内容变化"""
        try:
            current_text = self.edit_conclusions_content.toPlainText()
            original_text = self.original_conclusions_content.toPlainText()
            is_modified = current_text != original_text
            
            if is_modified:
                self.current_edits["CONCLUSIONS"] = current_text
            elif "CONCLUSIONS" in self.current_edits:
                del self.current_edits["CONCLUSIONS"]
            
            # 更新保存按钮状态
            self._update_save_button_state()
                
            # 发出内容更新信号
            if hasattr(self, 'content_updated'):
                self.content_updated.emit(self.file_path)
                
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
                    if hasattr(self, 'content_updated'):
                        self.content_updated.emit(self.current_edits)
                    if hasattr(self, 'accept'):
                        self.accept()  # 关闭对话框
                else:
                    logger.error("批量更新失败")
            else:
                logger.warning("没有修改内容需要保存")
                
        except Exception as e:
            logger.error(f"保存修改时出错: {e}")
    
    def _update_save_button_state(self):
        """更新保存按钮的状态"""
        try:
            if hasattr(self, 'save_btn') and self.save_btn:
                # 检查是否有任何内容被修改
                current_purpose_text = self.edit_purpose_content.toPlainText()
                original_purpose_text = self.original_purpose_content.toPlainText()
                purpose_modified = current_purpose_text != original_purpose_text
                
                current_conclusions_text = self.edit_conclusions_content.toPlainText()
                original_conclusions_text = self.original_conclusions_content.toPlainText()
                conclusions_modified = current_conclusions_text != original_conclusions_text
                
                # 如果任一内容被修改，则启用保存按钮
                is_modified = purpose_modified or conclusions_modified
                self.save_btn.setEnabled(is_modified)
                
        except Exception as e:
            logger.error(f"更新保存按钮状态时出错: {e}")
    
    def _save_changes_to_document(self):
        """将当前编辑内容保存到文档中"""
        try:
            logger.info("开始将更改保存到文档")
            
            if not hasattr(self, 'file_path') or not self.file_path:
                logger.error("文档路径未设置，无法保存更改")
                return False
            
            # 先获取当前文档的所有章节内容，以确定是否需要更新到文档末尾
            all_sections_content = self.body_content_service.get_all_content_sections(self.file_path)
            
            # 准备批量更新的数据
            updates = {}
            
            # 获取当前编辑器中的内容
            current_purpose_content = self.edit_purpose_content.toPlainText()
            current_conclusions_content = self.edit_conclusions_content.toPlainText()
            
            # 添加 PURPOSE 到 CONCLUSIONS 的内容更新
            if current_purpose_content != self.original_purpose_content.toPlainText():
                logger.info(f" PURPOSE 内容已更改，准备更新，新内容长度: {len(current_purpose_content)}")
                updates["PURPOSE-CONCLUSIONS"] = current_purpose_content
            
            # 添加 CONCLUSIONS 到 SAMPLE DESCRIPTION 的内容更新
            if current_conclusions_content != self.original_conclusions_content.toPlainText():
                logger.info(f" CONCLUSIONS 内容已更改，准备更新，新内容长度: {len(current_conclusions_content)}")
                
                # 检查是否存在 CONCLUSIONS-SAMPLE DESCRIPTION 的内容
                if "CONCLUSIONS-SAMPLE DESCRIPTION" in all_sections_content:
                    updates["CONCLUSIONS-SAMPLE DESCRIPTION"] = current_conclusions_content
                else:
                    # 如果不存在 SAMPLE DESCRIPTION，更新到文档末尾
                    updates["CONCLUSIONS-END"] = current_conclusions_content
            
            if updates:
                # 使用批量更新方法，只需打开文档一次
                success = self.body_content_service.update_multiple_sections_content(self.file_path, updates)
                
                if success:
                    logger.info(f"成功更新 {len(updates)} 个部分的内容到文档")
                    
                    # 更新原始内容，避免重复保存相同的更改
                    self.original_purpose_content.setPlainText(current_purpose_content)
                    self.original_conclusions_content.setPlainText(current_conclusions_content)
                    
                    # 发送信号通知控制器更新内容
                    if hasattr(self, 'content_updated'):
                        self.content_updated.emit(self.file_path)
                    
                    # 更新保存按钮状态（此时文档已保存，按钮应被禁用）
                    self._update_save_button_state()
                    return True
                else:
                    logger.error("批量更新失败")
                    return False
            else:
                logger.info("没有内容更改需要保存")
                return True
                
        except Exception as e:
            logger.error(f"保存更改到文档时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return False
