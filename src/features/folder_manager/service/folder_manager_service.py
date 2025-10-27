"""
项目文件夹管理服务模块
提供项目文件夹创建和管理的核心功能
"""

import os
import re
import glob
import json
import shutil
import stat
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QMessageBox, QWidget

from src.core.config_manager import config_manager
from src.core.logger import logger
from src.utils.file_utils import ensure_directory_exists
from src.utils.excel_initializer import initialize_customer_feedback_form, initialize_fee_evaluation_form


class FolderManagerService:
    """
    项目文件夹管理服务类
    提供项目文件夹创建和管理的核心功能
    """

    def __init__(self):
        """初始化项目文件夹管理服务"""
        pass

    def sanitize_filename(self, name: str) -> str:
        """
        清理文件名中的非法字符

        Args:
            name: 原始文件名

        Returns:
            清理后的文件名
        """
        invalid_chars = r'[\\/:*?"<>|]'
        return re.sub(invalid_chars, "_", name)

    def create_subfolders_in_project(self, project_dir: str) -> Dict[str, str]:
        """
        创建项目所需子目录结构

        Args:
            project_dir: 项目目录路径

        Returns:
            包含创建的子目录路径的字典
        """
        email_dir = os.path.join(project_dir, "E-mail")
        submitted_dir = os.path.join(project_dir, "Submitted Material")

        if not os.path.exists(email_dir):
            os.makedirs(email_dir)
            logger.info(f"创建 E-mail 文件夹: {email_dir}")
        else:
            logger.info(f"E-mail 文件夹已存在: {email_dir}")

        if not os.path.exists(submitted_dir):
            os.makedirs(submitted_dir)
            logger.info(f"创建 Submitted Material 文件夹: {submitted_dir}")
        else:
            logger.info(f"Submitted Material 文件夹已存在: {submitted_dir}")

        return {
            'email': email_dir,
            'submitted': submitted_dir
        }

    def move_files_by_extension(self, src_dir: str, dst_dir: str, ext: str = "*.msg", copy_only: bool = True) -> bool:
        """
        根据扩展名复制/移动文件

        Args:
            src_dir: 源目录
            dst_dir: 目标目录
            ext: 文件扩展名模式
            copy_only: 是否仅复制而不移动

        Returns:
            操作是否成功
        """
        files = glob.glob(os.path.join(src_dir, ext))
        for f in files:
            try:
                if copy_only:
                    shutil.copy2(f, dst_dir)
                else:
                    shutil.move(f, dst_dir)
                logger.info(f"{'复制' if copy_only else '移动'} 文件: {f} -> {dst_dir}")
            except Exception as e:
                logger.error(f"文件操作失败: {f} -> {dst_dir}, 错误: {e}")
                return False
        return True

    def backup_existing_folder(self, source_path: str, backup_root: str) -> bool:
        """
        备份现有文件夹到 BackupPath，并加上时间戳。

        Args:
            source_path: 源路径
            backup_root: 备份根目录

        Returns:
            是否成功备份
        """
        if not os.path.exists(source_path):
            logger.warning(f"源路径不存在，无需备份：{source_path}")
            return True

        try:
            os.makedirs(backup_root, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = os.path.basename(source_path)
            dest_path = os.path.join(backup_root, f"{folder_name}_{timestamp}")
            shutil.move(source_path, dest_path)
            logger.info(f"项目文件夹已备份至：{dest_path}")
            return True
        except Exception as e:
            logger.error(f"备份项目文件夹失败：{e}", exc_info=True)
            return False

    def handle_existing_project(self, target_folder: str, backup_path: str, parent: Optional[QWidget] = None) -> Optional[bool]:
        """
        处理已有项目文件夹存在的情况。

        Args:
            target_folder: 目标文件夹路径
            backup_path: 备份路径
            parent: 父窗口，用于显示消息框

        Returns:
            True -> 用户选择备份或覆盖并继续；
            False -> 用户取消操作；
            None -> 执行失败。
        """
        if parent:
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle("项目已存在")
            msg_box.setText(f"项目文件夹 {os.path.basename(target_folder)} 已存在。\n请选择操作：")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

            backup_btn = msg_box.button(QMessageBox.No)
            backup_btn.setText("备份并新建")

            overwrite_btn = msg_box.button(QMessageBox.Yes)
            overwrite_btn.setText("覆盖并重建")

            cancel_btn = msg_box.button(QMessageBox.Cancel)
            cancel_btn.setText("取消操作")

            msg_box.exec_()
            clicked_button = msg_box.clickedButton()

            if clicked_button == cancel_btn:
                logger.info("用户取消项目创建流程")
                return False  # 明确返回 False 表示取消

            elif clicked_button == backup_btn:
                success = self.backup_existing_folder(target_folder, backup_path)
                if not success:
                    QMessageBox.critical(parent, "错误", "备份失败，请检查权限或路径。")
                    return None
                return True  # 表示可以继续

            elif clicked_button == overwrite_btn:
                def on_rm_error(func, path, exc_info):
                    """
                    强制处理只读文件，用于 shutil.rmtree
                    """
                    os.chmod(path, stat.S_IWRITE)
                    func(path)

                try:
                    shutil.rmtree(target_folder, onerror=on_rm_error)
                    logger.info(f"旧项目文件夹已删除：{target_folder}")
                    return True
                except Exception as e:
                    logger.error(f"删除旧项目文件夹失败：{e}")
                    QMessageBox.critical(parent, "错误", f"删除旧项目文件夹失败：{str(e)}")
                    return None
        else:
            # 如果没有父窗口，直接覆盖
            def on_rm_error(func, path, exc_info):
                """
                强制处理只读文件，用于 shutil.rmtree
                """
                os.chmod(path, stat.S_IWRITE)
                func(path)

            try:
                shutil.rmtree(target_folder, onerror=on_rm_error)
                logger.info(f"旧项目文件夹已删除：{target_folder}")
                return True
            except Exception as e:
                logger.error(f"删除旧项目文件夹失败：{e}")
                return None

    def create_complete_project_structure(self, project_data: Dict[str, Any], parent: Optional[QWidget] = None) -> Optional[str]:
        """
        创建完整的项目结构，包括子文件夹、模板文件等

        Args:
            project_data: 项目数据，包含DL编号等信息
            parent: 父窗口，用于显示消息框

        Returns:
            项目子文件夹路径，如果失败则返回None
        """
        logger.info("【创建新项目】开始创建完整项目结构")
        logger.debug(f"接收到的项目数据: {project_data}")
        temp_folder_to_cleanup = None

        if not project_data:
            project_data = {}
            
        dl_number = project_data.get("DL", "")
        if not dl_number:
            if parent:
                QMessageBox.critical(parent, "错误", "缺少 DL 编号，无法创建新项目")
            logger.error("未提供 DL 编号，项目创建终止")
            return None

        # 获取路径配置，使用项目中定义的配置键
        template_dir = config_manager.get("paths.template_dir", r"D:\TestFlowManager\Template")
        project_base_dir = config_manager.get("paths.default_project_path", r"D:\TestFlowManager\Projects")
        backup_path = config_manager.get("paths.backup_path", r"D:\TestFlowManager\Backup")

        target_folder = os.path.join(project_base_dir, dl_number)
        source_folder = os.path.join(template_dir, "DL-XXXX-YY-ZZZ")

        # Step 1: 检查目标是否存在
        if os.path.exists(target_folder):
            result = self.handle_existing_project(target_folder, backup_path, parent)
            if result is False:  # 用户点击取消或处理失败
                logger.info("用户取消项目创建流程或操作被中断")
                return None
            elif not result:
                logger.error("处理已有项目失败")
                return None

        # Step 2: 复制模板
        if not os.path.exists(source_folder):
            logger.error(f"模板路径不存在: {source_folder}")
            if parent:
                QMessageBox.critical(parent, "错误", "模板路径不存在，请检查配置。")
            return None

        try:
            shutil.copytree(source_folder, target_folder)
            logger.info(f"成功复制模板到目标路径: {target_folder}")
        except Exception as e:
            logger.error(f"复制模板失败: {e}", exc_info=True)
            if parent:
                QMessageBox.critical(parent, "错误", f"复制模板失败: {str(e)}")
            return None

        # Step 3: 重命名子文件夹
        product_description = self.sanitize_filename(project_data.get("product_description", ""))
        tests_to_be_performed = self.sanitize_filename(project_data.get("tests_to_be_performed", ""))

        original_subfolder_name = "DL-XXXX-YY-ZZZ Title"
        # 改进文件夹名称的构建方式，避免多余空格
        name_parts = [dl_number, product_description, tests_to_be_performed]
        # 过滤掉空的部分并用单个空格连接
        new_subfolder_name = " ".join(part for part in name_parts if part).strip()
        new_subfolder_name = self.sanitize_filename(new_subfolder_name)  # 再次清理一遍
        subfolder_path = os.path.join(target_folder, new_subfolder_name)

        # 重命名子文件夹
        old_path = os.path.join(target_folder, original_subfolder_name)
        new_path = os.path.join(target_folder, new_subfolder_name)

        if os.path.exists(old_path):
            try:
                os.rename(old_path, new_path)
                logger.info(f"重命名文件夹: {old_path} -> {new_path}")
            except Exception as e:
                logger.error(f"重命名失败: {e}")
                if parent:
                    QMessageBox.warning(parent, "警告", f"重命名子文件夹失败：{str(e)}")
                return None
        else:
            # 如果原始子文件夹不存在，直接创建新的
            if not ensure_directory_exists(subfolder_path):
                logger.error(f"无法创建子文件夹: {subfolder_path}")
                if parent:
                    QMessageBox.warning(parent, "警告", f"无法创建子文件夹: {subfolder_path}")
                return None

        # Step 4: 创建子目录结构 (E-mail, Submitted Material)
        folder_structure = self.create_subfolders_in_project(subfolder_path)

        # Step 5: 初始化 Excel 表格
        # 获取默认的project_leader
        default_project_leader = config_manager.get("defaults.project_leader", "")
        # 构建带project_leader的文件名（仅用于客户反馈表）
        fee_filename = f"{os.path.basename(new_subfolder_name)} Form for Testing Fee Evaluation.xls"
        if default_project_leader:
            feedback_filename = f"{os.path.basename(new_subfolder_name)} Customer Feedback Form_{default_project_leader}.xlsx"
        else:
            feedback_filename = f"{os.path.basename(new_subfolder_name)} Customer Feedback Form.xlsx"
        
        success_fee = initialize_fee_evaluation_form(
            template_dir, subfolder_path,
            fee_filename,
            project_data
        )
        success_feedback = initialize_customer_feedback_form(
            template_dir, subfolder_path,
            feedback_filename,
            project_data
        )

        if not success_fee:
            logger.warning("测试费用评估表初始化失败")
        if not success_feedback:
            logger.warning("客户反馈表初始化失败")

        # Step 6: 获取附件来源路径
        temp_file_path = project_data.get('file_path', None)
        logger.debug(f"从项目数据中获取的临时文件路径: {temp_file_path}")
        if not temp_file_path or not os.path.exists(temp_file_path):
            logger.warning("未找到有效的临时文件路径，无法复制附件")
            logger.debug(f"临时文件路径是否存在: {temp_file_path and os.path.exists(temp_file_path)}")
            if parent:
                QMessageBox.warning(parent, "警告", "没有提取到有效的文件路径，无法复制附件。")
        else:
            # 检查temp_file_path是文件还是目录
            if os.path.isfile(temp_file_path):
                src_dir = os.path.dirname(temp_file_path)
            else:
                src_dir = temp_file_path
                # 记录需要清理的临时文件夹
                temp_folder_to_cleanup = temp_file_path
                
            logger.info(f"使用附件来源路径: {src_dir}")

            # Step 7: 复制 .msg 文件到 E-mail
            if not self.move_files_by_extension(src_dir, folder_structure["email"], "*.msg", copy_only=True):
                logger.warning("复制 .msg 文件失败或无匹配文件")

            # Step 8: 先复制文件到 Submitted Material
            # Step 9: 依据application_data.json找到关键字"selected_filename"的值处理文件
            from src.features.document_parser.service.document_parser_service import DocumentParserService
            document_parser = DocumentParserService()
            document_parser.copy_ltr_application_form(project_data, folder_structure["submitted"], src_dir)

            # Step 10: 根据application_data.json信息进行文档的操作更新
            # 查找需要更新的Word文档
            selected_filename = project_data.get('selected_filename', '')
            if selected_filename:
                word_file_path = os.path.join(folder_structure["submitted"], selected_filename)
                if os.path.exists(word_file_path):
                    logger.info(f"更新Word文档: {word_file_path}")
                    document_parser.update_word_document(word_file_path, project_data)
                else:
                    logger.warning(f"要更新的Word文档不存在: {word_file_path}")
            else:
                # 如果没有指定selected_filename，尝试查找目录中的Word文档
                submitted_files = [f for f in os.listdir(folder_structure["submitted"]) 
                                 if os.path.isfile(os.path.join(folder_structure["submitted"], f))]
                word_files = [f for f in submitted_files if f.endswith(('.doc', '.docx'))]
                
                if word_files:
                    word_file_path = os.path.join(folder_structure["submitted"], word_files[0])
                    logger.info(f"更新找到的第一个Word文档: {word_file_path}")
                    document_parser.update_word_document(word_file_path, project_data)
                else:
                    logger.warning("在Submitted Material目录中未找到Word文档")

        logger.info(f"项目 {dl_number} 已成功创建！")
        logger.info("【创建新项目】流程结束")
        
        # 清理临时文件夹（如果需要）
        if temp_folder_to_cleanup and os.path.exists(temp_folder_to_cleanup):
            try:
                shutil.rmtree(temp_folder_to_cleanup)
                logger.info(f"已清理临时文件夹: {temp_folder_to_cleanup}")
            except Exception as e:
                logger.error(f"清理临时文件夹失败: {e}")
        
        return subfolder_path