# src/features/matrix/view/handlers/matrix_event_handlers.py
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
import os
from src.core.logger import logger
from src.core.project_document_context import ProjectDocumentContext
from src.features.matrix.view.matrix_filter_dialog import MatrixFilterDialog
from src.features.test_record_generator.controller.test_record_controller import TestRecordController


class MatrixEventHandlers:
    """Matrix事件处理器 - 处理所有用户交互事件"""
    
    def __init__(self, view, _legacy_controller=None):
        self.view = view
        
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
                self.view.sync_to_model()
                
                # 触发Controller层处理
                result = self.view.import_from_spec(file_path, page_number, keyword)
                if result and result.get("success", False):
                    # 更新表格显示
                    self.view.refresh_table()
                    QMessageBox.information(self.view, "成功", "数据已成功导入")
                else:
                    error_msg = result.get("error", "导入失败") if result else "导入失败"
                    QMessageBox.warning(self.view, "失败", f"数据导入失败: {error_msg}")
                    
    def on_standardize_and_fill_clicked(self):
        """处理标准化填充按钮点击事件"""
        try:
            logger.info("开始标准化填充Matrix")
            
            # 同步表格数据到模型
            self.view.sync_to_model()
            
            # 先执行标准化操作
            init_result = self.view.initialize_matrix()
            if not init_result:
                QMessageBox.warning(self.view, "失败", "Matrix标准化失败")
                return
            
            # 再尝试从已导入的规格书中提取测试方法
            extract_result = self.view.extract_test_methods_from_spec()
            
            # 更新标准版本号
            update_result = self.view.update_standard_versions()
            
            # 更新表格显示
            self.view.refresh_table()
            
            # 只要有执行操作就弹出信息
            if extract_result or update_result["success"]:
                QMessageBox.information(self.view, "成功", "标准化填充Matrix已完成")
            # 如果没有任何操作被执行，则不显示任何信息

        except Exception as e:
            logger.error(f"标准化填充Matrix时出错: {e}", exc_info=True)
            QMessageBox.warning(self.view, "错误", f"标准化填充Matrix时出错: {str(e)}")
            
    def on_show_basic_info_dialog(self):
        """显示基本信息对话框 - View层事件触发"""
        try:
            logger.debug("开始显示基本信息对话框")
            # 同步表格数据到模型
            self.view.sync_to_model()

            project_data_file_path = self.view.resolve_project_data_file_path()
            logger.debug(f"解析得到的项目数据文件路径: {project_data_file_path}")

            # 如果有项目数据文件路径，则读取数据并显示基本信息对话框
            if project_data_file_path and os.path.exists(project_data_file_path):
                logger.debug(f"项目数据文件存在: {project_data_file_path}")
                try:
                    import json
                    with open(project_data_file_path, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)

                    logger.debug(f"成功读取项目数据: {project_data}")
                    # 显示基本信息对话框，同时传入项目数据文件路径
                    from src.features.main_window.view.basic_info_dialog import BasicInfoDialog
                    dialog = BasicInfoDialog(project_data, self.view)
                    # 将项目数据文件路径设置到dialog对象上
                    dialog.project_data_file_path = project_data_file_path
                    dialog.exec_()
                except Exception as e:
                    logger.error(f"读取或显示项目基本信息时出错: {e}")
                    QMessageBox.warning(self.view, "错误", f"无法读取项目基本信息: {str(e)}")
            else:
                logger.warning(f"未找到项目基本信息文件或项目尚未打开: {project_data_file_path}")
                QMessageBox.information(self.view, "提示", "未找到项目基本信息文件或项目尚未打开")
        except Exception as e:
            logger.error(f"显示基本信息对话框时出错: {e}")
            QMessageBox.warning(self.view, "错误", f"显示基本信息对话框时出错: {str(e)}")

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
            current_project = self.view.get_project_path()
            logger.debug(f"当前项目路径: {current_project}")
            default_path = self.view.build_default_output_path(default_filename)
            logger.debug(f"构建默认路径: {default_path}")
                
            file_path, _ = QFileDialog.getSaveFileName(
                self.view, "保存Test Status表", default_path, "Excel Files (*.xlsx)"
            )
            if file_path:
                logger.debug(f"选择的文件路径: {file_path}")
                # 同步表格数据到模型
                self.view.sync_to_model()
                # 导出前先保存合并单元格信息
                self.view.save_merged_cells_info()
                # 触发Controller层处理
                logger.debug("开始调用控制器导出方法")
                result = self.view.export_to_excel(file_path, export_type)
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
                        # 文件不存在，检查路径是否有效
                        # 如果路径不存在，提示用户选择另存为位置或取消
                        msg_box = QMessageBox(self.view)
                        msg_box.setIcon(QMessageBox.Warning)
                        msg_box.setWindowTitle("路径问题")
                        msg_box.setText(f"无法找到正确的项目文件夹，无法自动保存Test Status表。\n\n默认路径: {file_path}\n\n请手动选择保存位置。")
                        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                        result = msg_box.exec_()
                        
                        if result == QMessageBox.Ok:
                            # 让用户选择保存路径
                            new_file_path, _ = QFileDialog.getSaveFileName(
                                self.view, 
                                "保存Test Status表", 
                                default_filename, 
                                "Excel Files (*.xlsx)"
                            )
                            
                            if new_file_path:
                                # 重新尝试导出
                                result = self.view.export_to_excel(new_file_path, export_type)
                                if result:
                                    QMessageBox.information(self.view, "成功", "Test Status表已成功导出到Excel")
                                else:
                                    QMessageBox.warning(self.view, "错误", "导出失败，发生未知错误")
                        else:
                            logger.info("用户取消了导出操作")
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
            self.view.sync_to_model()
            
            # 调用控制器更新标准版本号
            result = self.view.update_standard_versions()
            
            if result["success"]:
                # 更新表格显示
                self.view.refresh_table()
                
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
                elif result.get("file_missing", False):
                    # 文件不存在的情况
                    if result.get("network_disconnect", False):
                        # 网络断开的情况
                        QMessageBox.warning(
                            self.view, 
                            "失败", 
                            f"标准版本号更新失败：无法访问标准文件，请检查网络连接。\n文件路径: {result.get('file_path', '未知路径')}"
                        )
                        logger.warning(f"标准文件无法访问，可能是网络断开: {result.get('file_path', '未知路径')}")
                    else:
                        # 普通文件不存在的情况
                        QMessageBox.warning(
                            self.view, 
                            "失败", 
                            f"标准版本号更新失败：未找到标准文件。\n文件路径: {result.get('file_path', '未知路径')}"
                        )
                        logger.warning(f"标准文件不存在: {result.get('file_path', '未知路径')}")
                elif result.get("no_standards_found", False):
                    # 没有找到标准数据的情况
                    QMessageBox.information(self.view, "成功", "标准版本号更新完成，标准文件中未找到有效的标准数据")
                    logger.info("标准版本号更新完成，标准文件中未找到有效的标准数据")
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
            self.view.sync_to_model()
            
            # 创建Test Record控制器实例
            controller = TestRecordController(
                matrix_controller=self.view.matrix_controller,
                project_context=self.view.get_project_context(),
            )
            
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

    def on_generate_cost_sheet_clicked(self):
        """处理生成费用表按钮点击事件"""
        try:
            logger.info("开始生成费用表")
            
            # 同步表格数据到模型
            self.view.sync_to_model()
            
            # 获取Matrix数据结构
            from src.features.matrix.model.matrix_data_structure import MatrixDataStructure
            matrix_data_structure = MatrixDataStructure()
            
            document_context = ProjectDocumentContext.from_project_context(
                self.view.get_project_context()
            )
            dl_number = self.view.ltr_number or document_context.dl_number
            requested_by = document_context.get_field('requested_by', '')
            location = document_context.get_field('location', '')
            product_description = document_context.get_field('product_description', '')
            tests_to_be_performed = document_context.get_field('tests_to_be_performed', '')
            
            # 解析Matrix数据结构
            matrix_data_structure.parse_matrix_to_structure(self.view.get_data_model().rows)
            
            # 创建费用表导出服务实例
            from src.features.matrix.service.export.service.fee_sheet_export_service import FeeSheetExportService
            fee_sheet_service = FeeSheetExportService(
                project_context=self.view.get_project_context()
            )
            
            # 调用服务生成费用表，获取返回的实际保存路径
            success, save_path = fee_sheet_service.export_fee_sheet(
                matrix_data_structure=matrix_data_structure,
                dl_number=dl_number,
                requested_by=requested_by,
                location=location,
                product_description=product_description,
                tests_to_be_performed=tests_to_be_performed
            )
            
            if success:
                logger.info("费用表生成成功")
                # 直接使用服务返回的实际保存路径
                QMessageBox.information(self.view, "成功", f"费用表已成功生成并保存到:\n{save_path}")
            else:
                logger.error("费用表生成失败")
                QMessageBox.warning(self.view, "错误", "费用表生成失败，请检查日志")
                
        except Exception as e:
            logger.error(f"生成费用表时出错: {e}", exc_info=True)
            QMessageBox.warning(self.view, "错误", f"生成费用表时出错: {str(e)}")
