"""
主窗口样式常量
包含LIMS风格的全局样式定义
"""

from src.shell.main_window.constants.design_tokens import DesignTokens

# 主窗口 Lims 风格全局样式（高分辨率屏幕优化版）
LIMS_APP_STYLESHEET = f"""
/* ==================== 顶栏样式 ==================== */
QWidget#LimsAppHeader {{
    background: #0F172A;
    border-bottom: none;
    min-height: 56px;
    max-height: 56px;
}}
QLabel#LimsBrandLabel {{
    color: #ffffff;
    font-weight: bold;
    font-size: 26px;
    letter-spacing: 0.5px;
}}
QLabel#LimsBreadcrumbLabel {{
    color: rgba(255, 255, 255, 0.75);
    font-size: 18px;
}}
QWidget#LimsHeaderActions {{
    background: transparent;
}}

/* ==================== 侧边栏样式 ==================== */
QWidget#LimsSidebar {{
    background: #1E293B;
    min-width: 260px;
    max-width: 260px;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}}
QLabel#LimsSidebarSection {{
    color: #90caf9;
    font-size: 15px;
    font-weight: bold;
    padding: 18px 18px 10px 24px;
    letter-spacing: 1px;
}}
QLabel#LimsSidebarSection:first-child {{
    padding-top: 24px;
}}
QListWidget#LimsNavList {{
    background-color: transparent;
    color: #e3f2fd;
    border: none;
    outline: none;
    font-size: 18px;
}}
QListWidget#LimsNavList::item {{
    padding: 14px 18px 14px 28px;
    margin: 4px 12px;
    border-radius: 8px;
}}
QListWidget#LimsNavList::item:hover {{
    background-color: rgba(255, 255, 255, 0.08);
}}
QListWidget#LimsNavList::item:focus {{
    background-color: rgba(49, 130, 206, 0.35);
    border: 1px solid rgba(144, 202, 249, 0.6);
    outline: none;
}}
QListWidget#LimsNavList::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {DesignTokens.COLOR_ACCENT}, stop:1 {DesignTokens.COLOR_SECONDARY});
    color: #ffffff;
    font-weight: 600;
}}

/* ==================== 主内容区样式 ==================== */
QWidget#LimsMainColumn {{
    background-color: {DesignTokens.COLOR_BG_CONTENT};
}}
QWidget#LimsPagePaper {{
    background-color: {DesignTokens.COLOR_SURFACE_CARD};
    border-radius: 10px;
    border: 1px solid rgba(0, 0, 0, 0.08);
}}
QLabel#LimsPageTitle {{
    color: {DesignTokens.COLOR_PRIMARY};
    font-size: 28px;
    font-weight: bold;
    padding: 12px 0 20px 6px;
    border-bottom: 2px solid {DesignTokens.COLOR_BORDER};
    margin-bottom: 6px;
}}
QLabel#LimsPageSubtitle {{
    color: {DesignTokens.COLOR_TEXT_MUTED};
    font-size: 18px;
    padding-left: 6px;
}}

/* 顶栏按钮已改为自绘 TitleBarButton，无需 QSS 样式 */

/* ==================== 状态栏样式 ==================== */
QStatusBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {DesignTokens.COLOR_SURFACE_CARD}, stop:1 {DesignTokens.COLOR_SURFACE_ALT});
    border-top: 1px solid {DesignTokens.COLOR_BORDER};
    color: {DesignTokens.COLOR_TEXT_SECONDARY};
    font-size: 16px;
}}
QStatusBar::item {{
    border: none;
}}
"""
