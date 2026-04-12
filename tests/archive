import sys
import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMenuBar, QMenu, QAction, QStatusBar, QFileDialog)
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

# 添加日志支持
sys.path.append('../src')
from src.core.logger import logger


class WordTableEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.doc = None
        self.table = None
        self.initUI()
        logger.info("WordTableEditor 初始化完成")

    def initUI(self):
        try:
            # 创建菜单栏
            menubar = self.menuBar()
            fileMenu = menubar.addMenu('文件')
            editMenu = menubar.addMenu('编辑')

            # 文件操作
            openAct = QAction('打开Word网页', self)
            openAct.triggered.connect(self.open_word)
            saveAct = QAction('保存修改', self)
            saveAct.triggered.connect(self.save_word)
            fileMenu.addAction(openAct)
            fileMenu.addAction(saveAct)

            # 编辑操作
            insertRowAct = QAction('插入行', self)
            insertRowAct.triggered.connect(self.insert_row)
            deleteRowAct = QAction('删除行', self)
            deleteRowAct.triggered.connect(self.delete_row)
            mergeCellsAct = QAction('合并选中单元格', self)
            mergeCellsAct.triggered.connect(self.merge_cells)
            splitCellAct = QAction('拆分单元格', self)
            splitCellAct.triggered.connect(self.split_cell)
            editMenu.addAction(insertRowAct)
            editMenu.addAction(deleteRowAct)
            editMenu.addAction(mergeCellsAct)
            editMenu.addAction(splitCellAct)

            # 表格控件
            self.table = QTableWidget()
            self.setCentralWidget(self.table)
            self.statusBar().showMessage('就绪')

            # 设置表头
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            # 显示行标题（之前设置为隐藏）
            self.table.verticalHeader().setVisible(True)
            
            # 设置选择模式，支持选择多个单元格
            # 使用 MultiSelection 模式而不是 ContiguousSelection
            self.table.setSelectionMode(QTableWidget.MultiSelection)
            self.table.setSelectionBehavior(QTableWidget.SelectItems)
            
            # 连接选择变化信号
            self.table.itemSelectionChanged.connect(self.on_selection_changed)
            
            # 安装事件过滤器以捕获鼠标事件
            self.table.viewport().installEventFilter(self)
            
            logger.info("UI初始化完成")
            logger.info(f"初始选择模式: {self.table.selectionMode()}")
            logger.info(f"初始选择行为: {self.table.selectionBehavior()}")
        except Exception as e:
            logger.error(f"初始化UI时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def eventFilter(self, obj, event):
        """事件过滤器，用于捕获鼠标事件"""
        try:
            if obj == self.table.viewport():
                if event.type() == event.MouseButtonPress:
                    logger.debug(f"鼠标按下: 位置({event.pos().x()}, {event.pos().y()}) 按钮: {event.button()}")
                elif event.type() == event.MouseButtonRelease:
                    logger.debug(f"鼠标释放: 位置({event.pos().x()}, {event.pos().y()}) 按钮: {event.button()}")
                elif event.type() == event.MouseMove:
                    logger.debug(f"鼠标移动: 位置({event.pos().x()}, {event.pos().y()}) 按钮: {event.buttons()}")
        except Exception as e:
            logger.error(f"事件过滤器中发生错误: {str(e)}")
            
        # 调用父类的事件过滤器
        return super().eventFilter(obj, event)

    def on_selection_changed(self):
        """当选择发生变化时的处理函数"""
        try:
            selected = self.table.selectedRanges()
            logger.info(f"选择发生变化，当前有 {len(selected)} 个选中区域")
            if selected:
                for i, selection in enumerate(selected):
                    top_row = selection.topRow()
                    left_col = selection.leftColumn()
                    bottom_row = selection.bottomRow()
                    right_col = selection.rightColumn()
                    logger.info(f"选中区域 {i}: 从({top_row},{left_col})到({bottom_row},{right_col})")
                    logger.info(f"选中区域 {i} 大小: {bottom_row - top_row + 1}行 x {right_col - left_col + 1}列")
            else:
                logger.info("当前没有选中任何区域")
        except Exception as e:
            logger.error(f"处理选择变化时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def open_word(self):
        """导入Word表格"""
        try:
            logger.info("开始打开Word文件")
            path, _ = QFileDialog.getOpenFileName(self, "选择Word网页", "", "Word Files (*.docx)")
            if not path:
                logger.info("用户取消选择文件")
                return

            logger.info(f"选择的文件路径: {path}")
            self.doc = Document(path)
            logger.info("Document对象创建成功")
            
            if not self.doc.tables:
                logger.warning("文档中没有找到表格")
                return

            # 加载第一个表格（完整导入，不做修改）
            logger.info(f"文档中找到 {len(self.doc.tables)} 个表格")
            self.load_table_full_import(self.doc.tables[0])
        except Exception as e:
            logger.error(f"打开Word文件时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def load_table_full_import(self, table):
        """完整导入表格到界面（不做修改）"""
        try:
            logger.info(f"开始完整导入表格: {len(table.rows)}行")
            self.table.setRowCount(len(table.rows))
            max_cols = max(len(row.cells) for row in table.rows)
            self.table.setColumnCount(max_cols)
            logger.info(f"表格列数: {max_cols}")

            # 填充数据（不做任何修改）
            for i, row in enumerate(table.rows):
                logger.debug(f"处理第{i}行，共{len(row.cells)}个单元格")
                for j, cell in enumerate(row.cells):
                    logger.debug(f"处理单元格({i},{j}): {cell.text}")
                    item = QTableWidgetItem(cell.text)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i, j, item)

            # 设置行列标题
            self._set_table_headers(max_cols, len(table.rows))

            # 处理合并单元格信息
            merge_info = self._extract_merge_info(table)
            self.apply_merges(merge_info)
            self.table.viewport().update()  # 强制刷新视图
            self.statusBar().showMessage(f'加载完成 - {len(table.rows)}行 x {max_cols}列')
            logger.info("表格完整导入完成")
        except Exception as e:
            logger.error(f"完整导入表格时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def _set_table_headers(self, col_count, row_count):
        """设置表格的行列标题"""
        try:
            # 设置列标题 (A, B, C, ...)
            for i in range(col_count):
                if i < 26:
                    # A to Z
                    header = chr(ord('A') + i)
                else:
                    # AA, AB, AC, ...
                    first = chr(ord('A') + (i // 26) - 1)
                    second = chr(ord('A') + (i % 26))
                    header = first + second
                self.table.setHorizontalHeaderItem(i, QTableWidgetItem(header))
            
            # 设置行标题 (1, 2, 3, ...)
            for i in range(row_count):
                header = str(i + 1)
                self.table.setVerticalHeaderItem(i, QTableWidgetItem(header))
                
            logger.debug(f"设置表格标题完成: {col_count}列, {row_count}行")
        except Exception as e:
            logger.error(f"设置表格标题时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def _extract_merge_info(self, table):
        """提取Word表格中的合并单元格信息"""
        merge_info = []
        try:
            logger.info("开始提取合并单元格信息")
            
            # 创建一个二维数组来跟踪已处理的单元格
            processed = [[False for _ in range(len(row.cells))] for row in table.rows]
            
            for i, row in enumerate(table.rows):
                for j, cell in enumerate(row.cells):
                    # 跳过已处理的单元格
                    if processed[i][j]:
                        continue
                        
                    try:
                        # 获取单元格的合并信息
                        cell_element = cell._element
                        
                        # 检查水平合并 (gridSpan)
                        grid_span = 1
                        grid_span_elem = cell_element.xpath('.//w:gridSpan')
                        if grid_span_elem:
                            grid_span = int(grid_span_elem[0].get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', 1))
                        
                        # 检查垂直合并 (vMerge)
                        v_merge = 1
                        v_merge_elem = cell_element.xpath('.//w:vMerge')
                        if v_merge_elem:
                            v_merge_val = v_merge_elem[0].get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                            # 如果是合并的开始 (restart) 或者没有值（默认是continue）
                            if not v_merge_val or v_merge_val == 'restart':
                                # 计算这个合并涉及多少行
                                v_merge = self._count_vmerge_rows(table, i, j)
                        
                        # 如果单元格是合并的，记录合并信息
                        if grid_span > 1 or v_merge > 1:
                            merge_info.append((i, j, v_merge, grid_span))
                            logger.debug(f"发现合并单元格({i},{j}): {v_merge}行 x {grid_span}列")
                            
                            # 标记已处理的单元格
                            for row_idx in range(i, min(i + v_merge, len(table.rows))):
                                for col_idx in range(j, min(j + grid_span, len(table.rows[row_idx].cells))):
                                    if row_idx < len(processed) and col_idx < len(processed[row_idx]):
                                        processed[row_idx][col_idx] = True
                        else:
                            processed[i][j] = True
                            
                    except Exception as cell_error:
                        logger.warning(f"处理单元格({i},{j})时出错: {str(cell_error)}")
                        processed[i][j] = True
                        
        except Exception as e:
            logger.error(f"提取合并信息时发生错误: {str(e)}")
            
        logger.info(f"提取到 {len(merge_info)} 个合并单元格信息")
        return merge_info

    def _count_vmerge_rows(self, table, start_row, col):
        """计算垂直合并涉及的行数"""
        try:
            count = 1  # 包括起始行
            # 从当前行的下一行开始检查
            for i in range(start_row + 1, len(table.rows)):
                # 确保列索引有效
                if col < len(table.rows[i].cells):
                    cell = table.rows[i].cells[col]
                    v_merge_elem = cell._element.xpath('.//w:vMerge')
                    # 如果找到vMerge元素，说明是合并的一部分
                    if v_merge_elem:
                        count += 1
                    else:
                        # 如果没有vMerge元素，说明合并结束
                        break
                else:
                    break
            return count
        except Exception as e:
            logger.error(f"计算垂直合并行数时出错: {str(e)}")
            return 1

    def apply_merges(self, merge_info):
        """应用合并单元格设置"""
        try:
            logger.info(f"应用 {len(merge_info)} 个合并信息")
            for (row, col, rowspan, colspan) in merge_info:
                logger.debug(f"应用合并: ({row},{col}) 跨 {rowspan} 行 {colspan} 列")
                self.table.setSpan(row, col, rowspan, colspan)
            self.table.viewport().update()  # 强制刷新视图
            logger.info("合并应用完成")
        except Exception as e:
            logger.error(f"应用合并时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def save_word(self):
        """保存修改到Word网页"""
        try:
            logger.info("开始保存Word文件")
            if not self.doc:
                logger.warning("没有可保存的文档")
                return

            # 清空原表格
            logger.debug("移除原文档中的表格")
            self.doc.tables[0]._element.getparent().remove(self.doc.tables[0]._element)

            # 创建新表格
            logger.debug(f"创建新表格: {self.table.rowCount()}行 x {self.table.columnCount()}列")
            new_table = self.doc.add_table(rows=self.table.rowCount(), cols=self.table.columnCount())

            # 填充数据
            for i in range(self.table.rowCount()):
                for j in range(self.table.columnCount()):
                    item = self.table.item(i, j)
                    if item:
                        cell = new_table.cell(i, j)
                        cell.text = item.text()
                        # 复制样式
                        cell.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                        for run in cell.paragraphs[0].runs:
                            run.font.size = Pt(12)
                    else:
                        logger.debug(f"单元格({i},{j})为空")

            # 应用合并单元格
            self.apply_merges_to_doc(new_table)
            self.doc.save('modified.docx')
            logger.info("文件保存成功: modified.docx")
            self.statusBar().showMessage('保存成功')
        except Exception as e:
            logger.error(f"保存Word文件时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def apply_merges_to_doc(self, table):
        """将界面合并信息应用到Word网页"""
        try:
            logger.info("开始应用合并到Word文档")
            for row in range(table.rows.__len__()):
                for col in range(table.columns.__len__()):
                    item = self.table.item(row, col)
                    if item:
                        # 获取合并信息（需反向推导）
                        span = self.get_span_from_ui(row, col)
                        if span[0] > 1 or span[1] > 1:
                            logger.debug(f"合并Word单元格({row},{col}) 跨 {span[0]} 行 {span[1]} 列")
                            table.cell(row, col).merge(table.cell(row + span[0] - 1, col + span[1] - 1))
            logger.info("Word文档合并应用完成")
        except Exception as e:
            logger.error(f"应用合并到Word文档时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def get_span_from_ui(self, row, col):
        """从界面获取合并跨度"""
        try:
            span = [1, 1]
            for r in range(row, self.table.rowCount()):
                if self.table.item(r, col) is None:
                    span[0] += 1
                else:
                    break
            for c in range(col, self.table.columnCount()):
                if self.table.item(row, c) is None:
                    span[1] += 1
                else:
                    break
            logger.debug(f"获取到跨度信息: ({row},{col}) 跨 {span[0]} 行 {span[1]} 列")
            return span
        except Exception as e:
            logger.error(f"获取跨度信息时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return [1, 1]

    # 以下是核心操作函数
    def insert_row(self):
        """在当前行上方插入新行"""
        try:
            current_row = self.table.currentRow()
            logger.debug(f"在行 {current_row} 上方插入新行")
            self.table.insertRow(current_row)
            self.statusBar().showMessage(f'已在行 {current_row} 上方插入新行')
        except Exception as e:
            logger.error(f"插入行时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def delete_row(self):
        """删除当前选中行"""
        try:
            current_row = self.table.currentRow()
            logger.debug(f"删除行 {current_row}")
            if current_row >= 0:
                self.table.removeRow(current_row)
                self.statusBar().showMessage(f'已删除行 {current_row}')
            else:
                logger.warning("没有选中任何行")
        except Exception as e:
            logger.error(f"删除行时发生错误: {str(e)}")
            logger.error(traceback.format_exc())

    def merge_cells(self):
        """合并选中区域"""
        try:
            logger.info("开始执行合并单元格操作")
            logger.debug(f"当前选择模式: {self.table.selectionMode()}")
            logger.debug(f"当前选择行为: {self.table.selectionBehavior()}")
            
            # 再次检查选择
            selected = self.table.selectedRanges()
            logger.info(f"执行合并时检测到 {len(selected)} 个选中区域")
            
            if selected:
                # 尝试将所有选中的区域合并为一个大的矩形区域
                if len(selected) > 1:
                    logger.info("检测到多个选中区域，尝试合并为一个区域")
                    # 计算包含所有区域的边界框
                    min_row = min(selection.topRow() for selection in selected)
                    max_row = max(selection.bottomRow() for selection in selected)
                    min_col = min(selection.leftColumn() for selection in selected)
                    max_col = max(selection.rightColumn() for selection in selected)
                    
                    logger.info(f"合并后的大区域: 从({min_row},{min_col})到({max_row},{max_col})")
                    row_count = max_row - min_row + 1
                    col_count = max_col - min_col + 1
                    logger.info(f"合并后区域大小: {row_count}行 x {col_count}列")
                    
                    # 检查是否选择了多个单元格
                    if row_count == 1 and col_count == 1:
                        logger.warning("只选择了一个单元格，无法合并")
                        self.statusBar().showMessage('请至少选择两个单元格进行合并')
                        return
                    
                    # 执行合并操作
                    logger.debug(f"执行合并: setSpan({min_row}, {min_col}, {row_count}, {col_count})")
                    self.table.setSpan(min_row, min_col, row_count, col_count)
                    
                    # 强制刷新视图
                    self.table.viewport().update()
                    self.statusBar().showMessage(f'合并了 {row_count}x{col_count} 区域')
                    logger.info(f"成功合并 {row_count}x{col_count} 区域")
                else:
                    # 只有一个选中区域
                    selection = selected[0]
                    top_row = selection.topRow()
                    left_column = selection.leftColumn()
                    bottom_row = selection.bottomRow()
                    right_column = selection.rightColumn()
                    
                    # 计算行列范围
                    row_count = bottom_row - top_row + 1
                    col_count = right_column - left_column + 1
                    
                    logger.info(f"选中区域: 从({top_row},{left_column})到({bottom_row},{right_column})")
                    logger.info(f"合并范围: {row_count}行 x {col_count}列")
                    
                    # 检查选中区域是否有效
                    if row_count < 1 or col_count < 1:
                        logger.warning("选中区域无效")
                        self.statusBar().showMessage('选中区域无效')
                        return
                    
                    # 检查是否选择了多个单元格
                    if row_count == 1 and col_count == 1:
                        logger.warning("只选择了一个单元格，无法合并")
                        self.statusBar().showMessage('请至少选择两个单元格进行合并')
                        return
                        
                    # 执行合并操作
                    logger.debug(f"执行合并: setSpan({top_row}, {left_column}, {row_count}, {col_count})")
                    self.table.setSpan(top_row, left_column, row_count, col_count)
                    
                    # 强制刷新视图
                    self.table.viewport().update()
                    self.statusBar().showMessage(f'合并了 {row_count}x{col_count} 区域')
                    logger.info(f"成功合并 {row_count}x{col_count} 区域")
            else:
                logger.warning("没有选中任何区域")
                self.statusBar().showMessage('请先选择要合并的单元格区域（需选择多个单元格）')
        except Exception as e:
            logger.error(f"合并单元格时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            self.statusBar().showMessage('合并单元格时发生错误')

    def split_cell(self):
        """拆分选中单元格"""
        try:
            logger.info("开始执行拆分单元格操作")
            selected = self.table.selectedRanges()
            if selected:
                logger.debug(f"找到 {len(selected)} 个选中区域")
                top_row = selected[0].topRow()
                left_column = selected[0].leftColumn()
                bottom_row = selected[0].bottomRow()
                right_column = selected[0].rightColumn()
                
                logger.info(f"选中区域: 从({top_row},{left_column})到({bottom_row},{right_column})")
                
                # 检查是否选择了多个单元格
                row_count = bottom_row - top_row + 1
                col_count = right_column - left_column + 1
                if row_count > 1 or col_count > 1:
                    logger.warning("选择了多个单元格，拆分操作只能针对单个合并单元格")
                    self.statusBar().showMessage('请选择单个合并单元格进行拆分')
                    return
                
                # 拆分单元格的实现
                split_count = 0
                # 遍历选中区域中的每个单元格（应该只有一个）
                for row in range(top_row, bottom_row + 1):
                    for col in range(left_column, right_column + 1):
                        # 获取当前单元格的跨度信息
                        row_span = self.table.rowSpan(row, col)
                        col_span = self.table.columnSpan(row, col)
                        logger.debug(f"单元格({row},{col})当前跨度: {row_span}行 x {col_span}列")
                        
                        # 如果单元格是合并的，则拆分它
                        if row_span > 1 or col_span > 1:
                            logger.debug(f"拆分单元格({row},{col}): 设置跨度为1x1")
                            # PyQt中没有直接的拆分方法，需要手动处理
                            self.table.setSpan(row, col, 1, 1)
                            split_count += 1
                        else:
                            logger.info(f"单元格({row},{col})未被合并，无需拆分")
                
                logger.info(f"共拆分了 {split_count} 个合并单元格")
                
                # 强制刷新视图
                self.table.viewport().update()
                
                if split_count > 0:
                    self.statusBar().showMessage(f'已拆分{split_count}个合并单元格')
                else:
                    self.statusBar().showMessage('选中的单元格未被合并')
                    
                logger.info("成功拆分选中区域")
            else:
                logger.warning("没有选中任何区域")
                self.statusBar().showMessage('请先选择要拆分的合并单元格')
        except Exception as e:
            logger.error(f"拆分单元格时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            self.statusBar().showMessage('拆分单元格时发生错误')

if __name__ == '__main__':
    try:
        logger.info("启动WordTableEditor应用程序")
        app = QApplication(sys.argv)
        editor = WordTableEditor()
        editor.resize(1024, 768)
        editor.show()
        logger.info("应用程序窗口显示完成")
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"应用程序运行时发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)