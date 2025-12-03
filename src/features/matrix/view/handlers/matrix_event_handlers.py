# src/features/matrix/view/handlers/matrix_event_handlers.py
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
import os
from src.core.logger import logger
from src.features.matrix.view.matrix_filter_dialog import MatrixFilterDialog
from src.features.test_record_generator.controller.test_record_controller import TestRecordController
from src.core.state_manager import state_manager


class MatrixEventHandlers:
    """Matrix事件处理器 - 处理所有用户交互事件"""
    
    def __init__(self, view, controller):
        self.view = view
        self.controller = controller
        
    def on_import_clicked(self):
        """处理导入按钮点击事件"""
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, "选择规格书文件", "", "Word Files (*.docx *.doc);;PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            # 检查文件扩展名
            _, ext = os.path.splitext(file_path.lower())
            if ext in ['.pdf']:
                QMessageBox.warning(self.view, "不支持的格式", "暂不支持PDF格式文件，请选择Word文档(.docx/.doc)")
                return
            
            # 显示筛选对话框，获取页码和关键字
            filter_dialog = MatrixFilterDialog(self.view)
            if filter_dialog.exec_() == 1:  # QDialog.Accepted
                filter_params = filter_dialog.get_filter_params()
                page_number = filter_params['page']
                keyword = filter_params['keyword']
                
                # 同步表格数据到模型
                self.view._sync_table_to_model()
                
                # 触发Controller层处理
                result = self.controller.import_from_spec(file_path, page_number, keyword)
                if result and result.get("success", False):
                    # 更新表格显示
                    self.view._update_table()
                    QMessageBox.information(self.view, "成功", "数据已成功导入")
                else:
                    error_msg = result.get("error", "导入失败") if result else "导入失败"
                    QMessageBox.warning(self.view, "失败", f"数据导入失败: {error_msg}")
                    
    def on_standardize_and_fill_clicked(self):
        """处理标准化填充按钮点击事件"""
        try:
            logger.info("开始标准化填充Matrix")
            
            # 同步表格数据到模型
            self.view._sync_table_to_model()
            
            # 调用控制器处理
            result = self.controller.standardize_and_fill_matrix()
            if result["success"]:
                # 更新表格显示
                self.view._update_table()
                QMessageBox.information(self.view, "成功", result["message"])
            else:
                QMessageBox.warning(self.view, "失败", result["error"])
                
        except Exception as e:
            logger.error(f"标准化填充Matrix时出错: {e}", exc_info=True)
            QMessageBox.warning(self.view, "错误", f"标准化填充Matrix时出错: {str(e)}")
            
    def on_find_clicked(self):
        """处理查找按钮点击事件"""
        # 弹出输入对话框让用户输入查找内容
        search_text, ok = QInputDialog.getText(self.view, "查找", "请输入要查找的内容:")
        if ok and search_text:
            # 同步表格数据到模型
            self.view._sync_table_to_model()
            # 调用控制器查找
            results = self.controller.find_content(search_text)
            if results:
                # 显示查找结果
                msg = f"找到 {len(results)} 个匹配项:\n"
                for result in results:
                    msg += f"第{result['row']+1}行, {result['header']}列: {result['value']}\n"
                QMessageBox.information(self.view, "查找结果", msg)
            else:
                QMessageBox.information(self.view, "查找结果", "未找到匹配项")
                
    def on_export_clicked(self):
        """处理导出按钮点击事件"""
        logger.debug("开始执行导出Test Status表到Excel操作")
        try:
            # 直接设置导出类型为test_status
            export_type = "test_status"
            
            # 使用LTR编号作为文件名的一部分
            if self.view.ltr_number:
                default_filename = f"{self.view.ltr_number} test status.xlsx"
            else:
                default_filename = "test status.xlsx"
                
            # 获取当前项目路径作为默认保存路径
            current_project = state_manager.get_state("current_project")
            logger.debug(f"当前项目路径: {current_project}")
            if current_project and os.path.exists(current_project):
                default_path = os.path.join(current_project, default_filename)
                logger.debug(f"构建默认路径: {default_path}")
            else:
                default_path = default_filename
                logger.debug(f"使用默认文件名: {default_path}")
                
            file_path, _ = QFileDialog.getSaveFileName(
                self.view, "保存Test Status表", default_path, "Excel Files (*.xlsx)"
            )
            if file_path:
                logger.debug(f"选择的文件路径: {file_path}")
                # 同步表格数据到模型
                self.view._sync_table_to_model()
                # 导出前先保存合并单元格信息
                self.view._save_merged_cells_info()
                # 触发Controller层处理
                logger.debug("开始调用控制器导出方法")
                result = self.controller.export_to_excel(file_path, export_type)
                logger.debug(f"控制器导出方法返回结果: {result}")
                if result:
                    QMessageBox.information(self.view, "成功", "Test Status表已成功导出到Excel")
                else:
                    # 检查文件是否被占用
                    try:
                        # 尝试以独占模式打开文件
                        with open(file_path, 'r+b') as f:
                            pass
                        # 如果能打开，说明是其他问题
                        QMessageBox.warning(self.view, "错误", "导出失败，请检查文件路径或权限")
                    except PermissionError:
                        # 文件被其他程序占用
                        QMessageBox.warning(self.view, "错误", "导出失败，文件已被其他程序占用（可能已在Excel中打开），请关闭文件后重试")
                    except FileNotFoundError:
                        # 文件不存在，应该是其他问题
                        QMessageBox.warning(self.view, "错误", "导出失败，请检查文件路径是否正确")
                    except Exception:
                        # 其他未知错误
                        QMessageBox.warning(self.view, "错误", "导出失败，发生未知错误")
        except Exception as e:
            logger.error(f"导出过程中发生异常: {e}", exc_info=True)
            QMessageBox.warning(self.view, "错误", f"导出过程中发生异常: {str(e)}")
            
    def on_update_standards_clicked(self):
        """处理更新标准版本按钮点击事件"""
        try:
            logger.info("开始更新标准版本号")
            
            # 同步表格数据到模型
            self.view._sync_table_to_model()
            
            # 调用控制器更新标准版本号
            result = self.controller.update_standard_versions()
            
            if result["success"]:
                # 更新表格显示
                self.view._update_table()
                
                # 显示更新详情
                details = result["details"]
                if details:
                    details_msg = "\n".join([f"第{detail['row']}行: {detail['old_method']} -> {detail['new_method']}" 
                                               for detail in details])
                    msg = f"标准版本号更新完成，共更新{result['updated_count']}项:\n{details_msg}"
                    # 创建自定义消息框以支持更宽的窗口
                    msg_box = QMessageBox(self.view)
                    msg_box.setWindowTitle("成功")
                    msg_box.setText(msg)
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    msg_box.setIcon(QMessageBox.NoIcon)
                    # 设置消息框宽度和内容靠左显示
                    msg_box.setStyleSheet("QLabel{min-width: 450px; text-align: left;}")
                    msg_box.exec_()
                else:
                    # 没有需要更新的项，但不是失败
                    QMessageBox.information(self.view, "成功", "标准版本号更新完成，没有需要更新的项")
                    logger.info("标准版本号更新完成")
            else:
                # 失败情况，只有在真正失败时才显示错误消息
                if "error" in result:
                    QMessageBox.warning(self.view, "失败", f"标准版本号更新出错: {result['error']}")
                    logger.error(f"标准版本号更新出错: {result['error']}")
                else:
                    # 没有找到需要更新的项，但不是错误
                    QMessageBox.information(self.view, "成功", "标准版本号更新完成，没有需要更新的项")
                    logger.info("标准版本号更新完成，没有需要更新的项")
        except Exception as e:
            logger.error(f"更新标准版本号时出错: {e}", exc_info=True)
            QMessageBox.warning(self.view, "错误", f"更新标准版本号时出错: {str(e)}")
            
    def on_generate_test_record_clicked(self):
        """处理生成Test Record按钮点击事件"""
        try:
            logger.info("开始生成Test Record文档")
            
            # 同步表格数据到模型
            self.view._sync_table_to_model()
            
            # 创建Test Record控制器实例
            controller = TestRecordController(matrix_service=self.controller.service)
            
            # 调用控制器生成Test Record（直接使用固定路径）
            success = controller.generate_test_record(parent=self.view)
            
            if success:
                logger.info("Test Record文档生成成功")
            else:
                # 错误信息已经在controller中处理过了，这里不需要额外提示
                logger.warning("Test Record文档生成失败或被取消")
        except Exception as e:
            logger.error(f"生成Test Record时出错: {e}", exc_info=True)
            QMessageBox.warning(self.view, "错误", f"生成Test Record时出错: {str(e)}")