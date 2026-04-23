"""
文件加密服务模块 - 使用标准 threading 模块（避免 QThread 栈溢出问题）
"""

import os
import re
import threading
from pathlib import Path
from typing import Dict, Tuple, Optional, Callable
from PyQt5.QtCore import pyqtSignal, QObject
from src.core.logger import logger
import pythoncom
from src.infrastructure.office.facade import OfficeFacade


class SignalEmitter(QObject):
    """用于从普通线程发送 Qt 信号的帮助类"""
    started_signal = pyqtSignal()
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, str)


class FileEncryptionService:
    """文件加密服务类"""
    
    def __init__(self):
        # 不再直接管理 COM 对象，改用 OfficeFacade workflow API。
        self._office_facade = OfficeFacade()
        
    @staticmethod
    def extract_password(parent_folder_name: str) -> str:
        """从父文件夹名称中提取密码"""
        try:
            match = re.search(r'(DL[^ ]*)', parent_folder_name, re.IGNORECASE)
            if not match:
                logger.warning(f"未在文件夹名称中找到 DL 开头的字符串：{parent_folder_name}")
                return ""
            
            dl_part = match.group(1)
            without_prefix = re.sub(r'^DL[-]?', '', dl_part, flags=re.IGNORECASE)
            without_dashes = without_prefix.replace('-', '')
            password = without_dashes.strip()
            
            logger.debug(f"从文件夹名称 '{parent_folder_name}' 提取密码：'{password}'")
            return password
            
        except Exception as e:
            logger.error(f"提取密码时出错：{e}")
            return ""
    
    @staticmethod
    def generate_secured_filename(original_path: str) -> str:
        """生成加密后的新文件名"""
        try:
            path = Path(original_path)
            stem = path.stem
            suffix = path.suffix
            parent = path.parent
            
            new_stem = f"{stem}_Secured"
            new_path = parent / f"{new_stem}{suffix}"
            
            logger.debug(f"生成新文件名：'{original_path}' -> '{new_path}'")
            return str(new_path)
            
        except Exception as e:
            logger.error(f"生成新文件名时出错：{e}")
            return ""
    
    def process_excel_file(self, file_path: str, password: str) -> Tuple[bool, str]:
        """处理单个 Excel 文件的加密 - 使用双重密码（打开密码 + 修改密码）"""
        try:
            file_path = os.path.normpath(file_path)
            
            logger.info(f"开始加密 Excel 文件：{file_path}")
            logger.info(f"使用密码：'{password}'")

            new_path = self.generate_secured_filename(file_path)
            logger.debug(f"目标文件路径：{new_path}")
            
            def _encrypt_workbook(workbook):
                workbook.Password = password
                workbook.WritePassword = password
                workbook.SaveAs(
                    Filename=new_path,
                    Password=password,
                    WriteResPassword=password,
                    ReadOnlyRecommended=False,
                    CreateBackup=False,
                )

            self._office_facade.with_excel_workbook(
                file_path,
                _encrypt_workbook,
                read_only=False,
                save=False,
            )
            logger.debug("SaveAs 执行成功")

            logger.info(f"✅ Excel 文件加密成功：{file_path} -> {new_path}")
            logger.info(f"   打开密码：{password}")
            logger.info(f"   修改密码：{password}")
            return True, ""
            
        except Exception as e:
            error_msg = f"处理 Excel 文件失败：{str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"错误类型：{type(e).__name__}")
            import traceback
            logger.error(f"详细错误：{traceback.format_exc()}")
            return False, error_msg
    
    def process_word_file(self, file_path: str, password: str) -> Tuple[bool, str]:
        """处理单个 Word 文件的加密"""
        try:
            # 规范化路径（解决 / 和 \ 混合的问题）
            file_path = os.path.normpath(file_path)
            
            logger.info(f"开始加密 Word 文件：{file_path}")
            logger.info(f"使用固定密码：'{password}'")

            new_path = self.generate_secured_filename(file_path)
            logger.debug(f"目标文件路径：{new_path}")

            def _encrypt_document(document):
                logger.debug("调用 SaveAs2 方法设置密码...")
                logger.debug(f"  - Password (打开密码): '{password}'")
                logger.debug(f"  - WritePassword (修改密码): '{password}'")

                document.SaveAs2(
                    FileName=new_path,
                    FileFormat=None,
                    LockComments=False,
                    Password=password,
                    AddToRecentFiles=False,
                    WritePassword=password,
                    ReadOnlyRecommended=False,
                    EmbedTrueTypeFonts=False,
                    SaveNativePictureFormat=False,
                    SaveFormsData=False,
                    SaveAsAOCELetter=False
                )
                logger.debug("SaveAs2 执行成功")

            self._office_facade.with_word_document(
                file_path,
                _encrypt_document,
                read_only=False,
                save=False,
            )
            
            logger.info(f"✅ Word 文件加密成功：{file_path} -> {new_path}")
            return True, ""
            
        except Exception as e:
            error_msg = f"处理 Word 文件失败：{str(e)}"
            import traceback
            logger.error(f"❌ {error_msg}")
            logger.error(f"错误类型：{type(e).__name__}")
            logger.error(f"详细错误：{traceback.format_exc()}")
            return False, error_msg
    
    def cleanup_resources(self):
        """兼容旧调用方；单文件流程的资源由 OfficeFacade workflow API 管理。"""
        logger.debug("FileEncryptionService 无持有型 Office session 需要释放")

    
    def encrypt_files_in_folder(self, target_folder: str) -> Dict[str, int]:
        """批量加密文件夹中的文件（仅处理当前目录，不递归）"""
        logger.debug(f"\n【FileEncryptionService.encrypt_files_in_folder】开始")
        logger.debug(f"目标文件夹：{target_folder}")
        
        stats = {
            'total': 0,
            'excel': 0,
            'word': 0,
            'success': 0,
            'failed': 0
        }
        
        errors = []
        
        try:
            parent_folder = os.path.basename(os.path.dirname(target_folder))
            logger.debug(f"父文件夹：{parent_folder}")
            
            excel_password = self.extract_password(parent_folder)
            word_password = "DGLAB"
            
            logger.info(f"开始加密文件夹：{target_folder}")
            logger.info(f"Excel 密码：{excel_password}, Word 密码：{word_password}")
            logger.debug(f"Excel 密码：{excel_password}, Word 密码：{word_password}")
            
            # 支持的扩展名
            supported_extensions = {'.doc', '.docx', '.xls', '.xlsx'}
            
            logger.debug(f"\n开始遍历文件夹（仅当前目录）...")
            file_count = 0
            
            # 只遍历当前目录，不递归子目录
            for filename in os.listdir(target_folder):
                file_path = os.path.join(target_folder, filename)
                
                # 跳过目录（包括子文件夹）
                if os.path.isdir(file_path):
                    logger.debug(f"  跳过子目录：{filename}")
                    continue
                
                file_ext = os.path.splitext(filename)[1].lower()
                file_count += 1
                
                logger.debug(f"  [{file_count}] 处理文件：{filename} (扩展名：{file_ext})")
                
                # 跳过不支持的文件类型
                if file_ext not in supported_extensions:
                    logger.debug(f"      → 跳过不支持的文件类型")
                    continue
                
                # 跳过临时文件（以~$开头）
                if filename.startswith('~$'):
                    logger.debug(f"      → 跳过 Office 临时文件")
                    continue
                
                # 跳过已加密的文件
                if '_Secured' in filename:
                    logger.debug(f"      → 跳过已加密文件")
                    continue
                
                success = False
                error_msg = ""
                
                if file_ext in ['.xls', '.xlsx']:
                    logger.debug(f"      → 类型：Excel，准备处理...")
                    stats['excel'] += 1
                    stats['total'] += 1
                    
                    if not excel_password:
                        error_msg = f"无法从父文件夹名称提取密码：{parent_folder}"
                        logger.error(error_msg)
                        errors.append((file_path, error_msg))
                        logger.debug(f"      ❌ {error_msg}")
                    else:
                        logger.debug(f"      → 调用 process_excel_file，密码：'{excel_password}'")
                        success, error_msg = self.process_excel_file(file_path, excel_password)
                        if success:
                            logger.debug(f"      ✅ Excel 加密成功")
                        else:
                            logger.debug(f"      ❌ Excel 加密失败：{error_msg}")
                            
                elif file_ext in ['.doc', '.docx']:
                    logger.debug(f"      → 类型：Word，准备处理...")
                    stats['word'] += 1
                    stats['total'] += 1
                    
                    logger.debug(f"      → 调用 process_word_file，密码：'{word_password}'")
                    success, error_msg = self.process_word_file(file_path, word_password)
                    if success:
                        logger.debug(f"      ✅ Word 加密成功")
                    else:
                        logger.debug(f"      ❌ Word 加密失败：{error_msg}")
                
                if success:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
                    errors.append((file_path, error_msg))
            
            logger.debug(f"\n文件遍历完成，总计处理：{stats['total']} 个文件")
            
            if errors:
                logger.debug(f"发现 {len(errors)} 个失败的文件：")
                for file_path, error in errors:
                    logger.error(f"文件处理失败：{file_path} - {error}")
                    logger.debug(f"  - {os.path.basename(file_path)}: {error}")
            
            logger.info(f"加密完成：总计 {stats['total']} 个文件，成功 {stats['success']} 个，失败 {stats['failed']} 个")
            logger.debug(f"\n✅ encrypt_files_in_folder 执行完成")
            logger.debug(f"统计结果：{stats}")
            
        except Exception as e:
            logger.debug(f"\n❌ 【异常捕获】encrypt_files_in_folder 出错：{e}")
            logger.error(f"批量加密过程中出错：{e}", exc_info=True)
            import traceback
            logger.debug(f"详细堆栈:\n{traceback.format_exc()}")
            raise
        
        # finally:
        #     logger.debug("\n[finally] 调用 cleanup_resources()...")
        #     self.cleanup_resources()
        
        return stats


def start_encryption_thread(folder_path: str, emitter: SignalEmitter):
    """在线程中执行加密任务"""
    service = None
    try:
        logger.debug("[start_encryption_thread] 开始执行")
        
        # 创建服务实例
        logger.debug("[0] 正在创建 FileEncryptionService 实例...")
        service = FileEncryptionService()
        logger.debug("✅ FileEncryptionService 实例创建成功")
        
        # 初始化 COM
        logger.debug("[1] 正在初始化 COM...")
        pythoncom.CoInitialize()
        logger.debug("✅ COM 初始化完成")
        
        # 发送开始信号
        emitter.started_signal.emit()
        logger.debug("✅ started_signal 已发送")
        
        # 执行加密任务
        logger.info(f"[2] 开始执行加密任务，文件夹：{folder_path}")
        stats = service.encrypt_files_in_folder(folder_path)
        logger.info(f"✅ 加密任务完成，统计：{stats}")
        
        # 发送完成信号
        emitter.finished_signal.emit(stats)
        logger.debug("✅ finished_signal 已发送")
        
    except Exception as e:
        error_msg = f"加密过程发生错误：{str(e)}"
        logger.error(f"\n❌ 【异常捕获】{error_msg}", exc_info=True)
        logger.error(f"错误类型：{type(e).__name__}")
        import traceback
        logger.error(f"详细堆栈:\n{traceback.format_exc()}")
        emitter.error_signal.emit(error_msg)
    finally:
        logger.debug("[4] 正在清理资源...")
        if service:
            service.cleanup_resources()
        logger.debug("✅ 资源清理完成")
