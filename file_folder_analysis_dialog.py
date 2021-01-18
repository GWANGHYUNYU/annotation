import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from PyQt5 import uic
# PyQT designer로 작성된 ui파일 로드하여 사용
form_class = uic.loadUiType("file_folder_analysis_dialog.ui")[0]


class FileFolderAnalysisDialog(QDialog, form_class):
    def __init__(self, parent=None):
        super(FileFolderAnalysisDialog, self).__init__(parent)

        # PyQT designer로 작성된 ui파일 로드하여 사용
        self.setupUi(self)

        self.setWindowTitle("파일/폴더 분석 결과")

        self.parent = parent
        self.size = self.parent.n_objects + 3

        self.pushButton_OK.clicked.connect(self.onOKButtonClicked)
        self.pushButton_Save.clicked.connect(self.onSaveButtonClicked)

        # self.tableWidget_analysis_result

    def onOKButtonClicked(self):
        self.reject()

    def onSaveButtonClicked(self):
        self.accept()

    def showModal(self):
        ''' 세부 분석결과 디스플레이 위젯 관련 '''
        # 세부 분석결과 디스플레이 테이블 위젯 초기화
        self.tableWidget_analysis_result.clearContents()
        self.tableWidget_analysis_result.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget_analysis_result.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableWidget_analysis_result.setSelectionMode(QTableWidget.SingleSelection)
        self.tableWidget_analysis_result.setAlternatingRowColors(True)

        table_column_cnt = self.size
        self.tableWidget_analysis_result.setColumnCount(table_column_cnt)
        # 포즈 추정 결과 표시 열의 헤더(제목) 설정
        column_headers = ['식물과', '식물종', '원본영상'] + self.parent.ELE_LIST
        self.tableWidget_analysis_result.setHorizontalHeaderLabels(column_headers)

        row_cnt = len(self.parent.species_list)
        self.tableWidget_analysis_result.setRowCount(row_cnt)

        table_index = 0
        for i in range(0, len(self.parent.species_list)):
            for i in range(0, len(self.parent.species_list)):
                class_str = str(self.parent.class_list[self.parent.species_class_index_list[i]])
                species_str = str(self.parent.species_list[i])
                species_cnt_str = str(self.parent.species_cnt_list[i])

                ele_cnt_str = [str(self.parent.species_ele_cnt_list[n][i]) for n in range(self.parent.n_objects)]
                # leaf_cnt_str = str(self.parent.species_leaf_cnt_list[i])
                # flower_fruit_cnt_str = str(self.parent.species_flower_fruit_cnt_list[i])
                # entire_cnt_str = str(self.parent.species_entire_cnt_list[i])
                # multi_entire_cnt_str = str(self.parent.species_multi_entire_cnt_list[i])

            # 해당 어노테이션 정보에 대해서 부모 클래스의 어노테이션 디스플레이 테이블에 정보 추가
            item_list = [class_str, species_str, species_cnt_str] + ele_cnt_str

            for column in range(len(item_list)):
                item = QTableWidgetItem(item_list[column])
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.tableWidget_analysis_result.setItem(table_index, column, item)

            table_index += 1

        # 윈도우 사이즈에 맞춰 테이블 정보 사이즈 맞추기
        width = int(self.width())
        resize_width = int(width / (self.size))
        for i in range(self.size):
            self.tableWidget_analysis_result.setColumnWidth(i, resize_width - 15)

        ''' 세부 분석결과 디스플레이 위젯 관련 '''
        # 세부 분석결과 디스플레이 테이블 위젯 초기화
        self.tableWidget_analysis_result_total.clearContents()
        self.tableWidget_analysis_result_total.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget_analysis_result_total.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableWidget_analysis_result_total.setSelectionMode(QTableWidget.SingleSelection)
        self.tableWidget_analysis_result_total.setAlternatingRowColors(True)

        table_column_cnt = self.size
        self.tableWidget_analysis_result_total.setColumnCount(table_column_cnt)
        # 포즈 추정 결과 표시 열의 헤더(제목) 설정
        column_headers = ['식물과', '식물종', '원본영상'] + self.parent.ELE_LIST
        # column_headers = ['식물과', '식물종', '원본영상', 'leaf', 'flower/fruit', 'entire', 'multi-entire']
        self.tableWidget_analysis_result_total.setHorizontalHeaderLabels(column_headers)

        row_cnt = len(self.parent.class_list) + 1
        self.tableWidget_analysis_result_total.setRowCount(row_cnt)

        table_index = 0
        for i in range(0, len(self.parent.class_list)):
            class_str = str(self.parent.class_list[i])
            species_str = str(self.parent.class_list[i])
            species_cnt_str = str(self.parent.class_cnt_list[i])
            ele_cnt_str = [str(self.parent.class_ele_cnt_list[n][i]) for n in range(self.parent.n_objects)]

            # 해당 어노테이션 정보에 대해서 부모 클래스의 어노테이션 디스플레이 테이블에 정보 추가
            item_list = [class_str, species_str, species_cnt_str] + ele_cnt_str

            for column in range(len(item_list)):
                item = QTableWidgetItem(item_list[column])
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.tableWidget_analysis_result_total.setItem(table_index, column, item)

            table_index += 1

        item_list = ['합계', '합계', str(self.parent.total_cnt)] + [str(self.parent.total_ele_cnt_list[n]) for n in range(self.parent.n_objects)]

        for column in range(len(item_list)):
            item = QTableWidgetItem(item_list[column])
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.tableWidget_analysis_result_total.setItem(table_index, column, item)

        # 윈도우 사이즈에 맞춰 테이블 정보 사이즈 맞추기
        width = int(self.width())
        resize_width = int(width / self.size)
        for i in range(7):
            self.tableWidget_analysis_result_total.setColumnWidth(i, resize_width - 15)

        ''' 다이얼로그 수행 '''
        return super().exec_()
