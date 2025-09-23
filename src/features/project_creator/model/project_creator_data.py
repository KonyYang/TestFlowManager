from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class EmailAttachment:
    """邮件附件数据模型"""
    filename: str
    content: bytes
    content_type: Optional[str] = None
    size: Optional[int] = None


@dataclass
class EmailData:
    """邮件数据模型"""
    subject: str
    sender: str
    received_time: str
    body: str
    attachments: List[EmailAttachment]
    file_path: str


@dataclass
class ProjectData:
    """项目数据模型"""
    project_id: str
    name: str
    created_time: str
    temp_folder: str
    email_data: EmailData
    extracted_ltr_data: Optional[Dict[str, Any]] = None
    status: str = "initialized"  # initialized, processing, completed, failed


@dataclass
class WordProcessingResult:
    """Word文档处理结果模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processed_file_path: Optional[str] = None


@dataclass
class ProjectCreationContext:
    """项目创建上下文，用于在流程中传递数据"""
    email_data: Optional[EmailData] = None
    selected_file_path: Optional[str] = None
    temp_folder: Optional[str] = None
    word_processing_result: Optional[WordProcessingResult] = None
    project_data: Optional[ProjectData] = None
