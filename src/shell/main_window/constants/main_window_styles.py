"""
主窗口样式常量
包含LIMS风格的全局样式定义
"""

# 主窗口 Lims 风格全局样式（高分辨率屏幕优化版）
LIMS_APP_STYLESHEET = """
/* ==================== 顶栏样式 ==================== */
QWidget#LimsAppHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a3a5c, stop:1 #2c5282);
    border-bottom: none;
    min-height: 70px;
    max-height: 70px;
}
QLabel#LimsBrandLabel {
    color: #ffffff;
    font-weight: bold;
    font-size: 26px;
    letter-spacing: 0.5px;
}
QLabel#LimsBreadcrumbLabel {
    color: rgba(255, 255, 255, 0.9);
    font-size: 18px;
}
QWidget#LimsHeaderActions {
    background: transparent;
}

/* ==================== 侧边栏样式 ==================== */
QWidget#LimsSidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a3a5c, stop:1 #152a45);
    min-width: 260px;
    max-width: 260px;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
QLabel#LimsSidebarSection {
    color: #90caf9;
    font-size: 15px;
    font-weight: bold;
    padding: 18px 18px 10px 24px;
    letter-spacing: 1px;
}
QLabel#LimsSidebarSection:first-child {
    padding-top: 24px;
}
QListWidget#LimsNavList {
    background-color: transparent;
    color: #e3f2fd;
    border: none;
    outline: none;
    font-size: 18px;
}
QListWidget#LimsNavList::item {
    padding: 14px 18px 14px 28px;
    margin: 4px 12px;
    border-radius: 8px;
}
QListWidget#LimsNavList::item:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
QListWidget#LimsNavList::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3182ce, stop:1 #2c5282);
    color: #ffffff;
    font-weight: 600;
}

/* ==================== 主内容区样式 ==================== */
QWidget#LimsMainColumn {
    background-color: #f0f4f8;
}
QWidget#LimsPagePaper {
    background-color: #ffffff;
    border-radius: 10px;
    border: none;
    /* 添加阴影效果 */
    border-top: 1px solid rgba(0, 0, 0, 0.05);
}
QLabel#LimsPageTitle {
    color: #1a3a5c;
    font-size: 28px;
    font-weight: bold;
    padding: 12px 0 20px 6px;
    border-bottom: 2px solid #e2e8f0;
    margin-bottom: 6px;
}
QLabel#LimsPageSubtitle {
    color: #718096;
    font-size: 18px;
    padding-left: 6px;
}

/* ==================== 顶栏按钮样式 ==================== */
QToolButton#LimsHeaderMenuButton {
    color: rgba(255, 255, 255, 0.9);
    font-size: 18px;
    border: none;
    padding: 10px 16px;
    background: transparent;
    border-radius: 6px;
}
QToolButton#LimsHeaderMenuButton:hover {
    background-color: rgba(255, 255, 255, 0.15);
    color: #ffffff;
}
QToolButton#LimsHeaderMenuButton::menu-indicator {
    image: none;
    width: 0px;
}

/* ==================== 状态栏样式 ==================== */
QStatusBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f7fafc);
    border-top: 1px solid #e2e8f0;
    color: #4a5568;
    font-size: 16px;
}
QStatusBar::item {
    border: none;
}

/* ==================== Matrix 表格样式 ==================== */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #edf2f7;
    selection-background-color: #bee3f8;
    selection-color: #1a3a5c;
    font-size: 16px;
}
QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #edf2f7;
}
QTableWidget::item:alternate {
    background-color: #f7fafc;
}
QTableWidget::item:selected {
    background-color: #bee3f8;
    color: #1a3a5c;
}
QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f7fafc, stop:1 #edf2f7);
    color: #4a5568;
    padding: 12px;
    border: none;
    border-bottom: 2px solid #cbd5e0;
    font-weight: bold;
    font-size: 16px;
}
QHeaderView::section:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #edf2f7, stop:1 #e2e8f0);
}
"""
