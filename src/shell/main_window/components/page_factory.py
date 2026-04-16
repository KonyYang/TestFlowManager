# src/shell/main_window/components/page_factory.py
"""
页面工厂模块
统一创建各类页面组件，提供可复用的页面构建方法
"""
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class PageFactory:
    """页面工厂 - 统一创建各类页面组件"""

    @staticmethod
    def create_placeholder_page(
        title: str,
        description: str = "",
        icon: str = "🚧"
    ) -> QWidget:
        """
        创建现代化的占位页面
        
        Args:
            title: 页面标题
            description: 页面描述文本（可选）
            icon: 页面图标 emoji（默认：🚧）
            
        Returns:
            QWidget: 配置好的占位页面对象
        """
        page = QWidget()
        page.setStyleSheet("""
            background-color: #fafbfc;
        """)
        
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)
        
        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 72px;
            padding: 24px;
            background: white;
            border-radius: 50%;
            border: 2px solid #e2e8f0;
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # 标题
        title_label = QLabel(f"{title}")
        title_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #2d3748;
            padding: 0px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 描述
        desc_text = description if description else "此功能正在开发中，敬请期待..."
        desc_label = QLabel(desc_text)
        desc_label.setStyleSheet("""
            font-size: 20px;
            color: #718096;
            padding: 0px;
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        
        # 卡片容器
        card = QWidget()
        card.setStyleSheet("""
            background: white;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            padding: 60px;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(60, 60, 60, 60)
        card_layout.setSpacing(20)
        card_layout.setAlignment(Qt.AlignCenter)
        
        card_layout.addWidget(icon_label)
        card_layout.addWidget(title_label)
        card_layout.addWidget(desc_label)
        
        layout.addWidget(card)
        return page
