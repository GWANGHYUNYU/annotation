# 필요 라이브러리 임포트
import sys                  # 변수, 함수 제어 등 기본 모듈
import configparser
import os

from image_viewer import ImageViewer
from file_manager import FileManager
from annotatation_manager import AnnotationManager

# GUI 프로그램 용 PyQT5 관련 모듈 임포트
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
# PyQT designer로 작성된 ui파일 로드하여 사용
form_class = uic.loadUiType("main.ui")[0]


class MainWindowClass(QMainWindow, form_class):
    def __init__(self):
        super(MainWindowClass, self).__init__()

        """ PyQT designer로 작성된 ui파일 로드하여 사용 """
        self.setupUi(self)

        # 사용자 아이디
        self.user_id = ''

        # 파일 트리 관련 변수 설정
        self.root_path = ''
        self.sel_path = ''
        self.model = None
        self.selected_file_path = '- - - -'
        self.selected_file_folder = '- - - -'
        self.treeview_current_index = None
        self.treeview_above_index = None
        self.treeview_below_index = None

        """ 프로그램 사용 설정값을 저장된 값을 불러와서 사용 """
        self.config = configparser.ConfigParser()
        self.load_prop_info()

        """ 메인 프로그램 영상 디스플레이 관련 클래스 설정 """
        self.img_viewer = ImageViewer(parent=self)
        self.input_img = None
        self.proc_img = None
        self.flg_img_ok = False

        """ 사용하는 클래스 관련 설정 """
        # 파일 관련 매니저 클래스 설정
        self.file_manager = FileManager(parent=self)

        # 어노테이션 데이터 관련 매니저 클래스 설정
        self.annot_manager = AnnotationManager(parent=self)

        """ 프로그램 GUI 관련 설정 """
        # 사용자 아이디 라인 에디트 설정
        self.lineEdit_user_id.returnPressed.connect(self.user_id_return_pressed)
        self.lineEdit_user_id.textChanged.connect(self.user_id_text_change)
        self.lineEdit_user_id.setText(self.user_id)
        # 목표 폴더 열기 버튼 설정
        self.pushButton_sel_root.clicked.connect(self.button_sel_target_root)
        # 파일 분석 버튼 설정
        self.pushButton_file_analysis.clicked.connect(self.button_file_analysis)
        self.pushButton_file_analysis.setDisabled(True)
        # 파일 추출 버튼 설정
        self.pushButton_file_extract.clicked.connect(self.button_file_extract)
        self.pushButton_file_extract.setDisabled(True)

        # 어노테이션 데이터 디스플레이 테이블 위젯 설정
        self.tableWidget_ann_data.setSortingEnabled(True)
        self.tableWidget_ann_data.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableWidget_ann_data.setSelectionBehavior(QTableWidget.SelectRows)
        # 테이블 위젯 헤더 정보 설정 및 추가
        column_headers = ['class_name', 'class_index', 'xmin', 'ymin', 'xmax', 'ymax']
        table_column_cnt = len(column_headers)
        self.tableWidget_ann_data.setColumnCount(table_column_cnt)
        # 포즈 추정 결과 표시 열의 헤더(제목) 설정
        self.tableWidget_ann_data.setHorizontalHeaderLabels(column_headers)
        # 테이블 row 단위 색깔 다르게 보이기
        self.tableWidget_ann_data.setAlternatingRowColors(True)

        # 어노테이션 데이터 디스플레이 클래스 선택 콤보 박스 설정
        # 어노테이션 클래스 정보에 맨 앞에는 전체 보이기, 맨 뒤에는 전체 안보이기 선택 추가
        self.comboBox_sel_class.addItem('Display All')
        for i in range(len(self.annot_manager.CLASS_LIST)):
            self.comboBox_sel_class.addItem(self.annot_manager.CLASS_LIST[i])
        self.comboBox_sel_class.activated.connect(self.combo_sel_class_change)
        self.comboBox_sel_class.addItem('No Show')
        self.sel_class_text = 'Display All'
        self.sel_class_index = -1

        # 프로그레스바 설정
        self.progressBar_main.setRange(0, 100)
        self.progressBar_main.setValue(0)


        # 스테이터스 바 텍스트
        self.status_text = ''

        # 프로그램 최대화 수행
        # self.showMaximized()

        """ 영상 디스플레이 타이머 """
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_func)
        self.timer.start(1)

    """ 기본 동작 함수 관련 """
    # 타이머 함수
    def timer_func(self):
        # 선택된 영상 디스플레이
        self.img_viewer.update_frame(self.proc_img)

    # 키보드 동작 이벤트 처리 함수
    def keyPressEvent(self, e):
        # 현재 선택된 이미지의 이전 이미지 선택 수행
        if e.key() in [Qt.Key_A]:
            self.treeview_file_sel_previous()
        # 현재 선택된 이미지의 다음 이미지 선택 수행
        elif e.key() in [Qt.Key_D]:
            self.treeview_file_sel_next()
        # 현재 선택된 이미지의 다음 이미지 선택 수행
        elif e.key() in [Qt.Key_W]:
            self.combo_sel_class_previous()
        # 현재 선택된 이미지의 다음 이미지 선택 수행
        elif e.key() in [Qt.Key_S]:
            self.combo_sel_class_next()
        # 현재 선택된 바운딩박스 정보 지우기
        elif e.key() in [Qt.Key_Space]:
            self.annot_manager.delete_bbox_obj()

    """ 버튼 동작 수행 함수 """
    # 목표 폴더 선택 버튼 클릭 동작 함수
    def button_sel_target_root(self):
        self.sel_path = self.root_path

        # 루트 디렉토리를 파일다이얼로그 이용하여 선택
        if self.user_id == 'vipslab':
            self.sel_path = '//168.131.152.237/외래잡초 영상 판별 시스템 개발 데이터 공유'

        # 기존 목표 폴더 경로가 없는 경우 현재 프로그램 폴더로 폴더선택 시작지점 변경
        if os.path.isdir(self.sel_path) is False:
            self.sel_path = os.getcwd()

        # 기준 경로에서 파일 다이얼로그 띄우기
        self.sel_path = str(QFileDialog.getExistingDirectory(self, "목표 디렉토리 선택", self.sel_path))
        if not self.sel_path:
            QMessageBox.warning(self, '경고', '목표 디렉토리 선택을 취소하였습니다!')
            return

        # 특정 아이디에 대해서는 특정 동작 수행
        if self.user_id != 'vipslab':
            self.root_path = self.sel_path

        # **** 지정폴더 파일 트리 뷰 추가
        self.model = QFileSystemModel()
        self.model.setRootPath(self.sel_path)
        self.treeView_file.setModel(self.model)
        self.treeView_file.setRootIndex(self.model.index(self.sel_path))
        self.treeView_file.selectionModel().currentChanged.connect(self.treeview_file_sel_changed)
        self.treeView_file.setColumnWidth(0, 250)
        # self.treeView_file.resizeColumnToContents(0)

        # 특정 아이디에 대해서는 특정 동작 수행
        if self.user_id == 'vipslab':
            self.pushButton_file_extract.setEnabled(True)
        else:
            self.pushButton_file_extract.setDisabled(True)

        # 폴더 트리 뷰에서 특정 폴더나 파일 선택 시에만 파일 분석 가능하게 버튼 활성화
        self.pushButton_file_analysis.setEnabled(True)

    # 파일 분석(파일 수 세기) 버튼 클릭 동작 함수
    def button_file_analysis(self):
        self.file_manager.file_folder_analysis(self.sel_path)

    # 파일 추출(어노테이션 크로핑 영상 데이터) 버튼 클릭 동작 함수
    def button_file_extract(self):
        print('button file extract')

    """ 리스트 뷰, 콤보 박스 등 이벤트 처리 함수 """
    # 사용자 아이디 라인에디트 변경/엔터 처리 수행 함수
    def user_id_return_pressed(self):
        self.user_id = self.lineEdit_user_id.text()
        self.lineEdit_user_id.clearFocus()
        self.button_sel_target_root()

    # 사용자 아이디 변경 입력시 해당 아이디 정보로 사용자 아이디 정보 변경
    def user_id_text_change(self):
        self.user_id = self.lineEdit_user_id.text()

    # 파일 트리뷰 선택 변경시 동작 함수
    def treeview_file_sel_changed(self, new_index, old_index):
        self.treeview_file_selected(new_index)

    # 파일 트리뷰 선택 시 동작 함수
    def treeview_file_selected(self, index):
        if index.row() >= 0:
            # 영상 로딩 시간 중에 마우스에 처리중 표시
            self.setCursor(Qt.WaitCursor)
            # 선택된 인덱스에 대해서 정보 및 파일 경로 얻기
            index_item = self.model.index(index.row(), 0, index.parent())
            self.selected_file_path = self.model.filePath(index_item)

            # 선택 경로 영상 열기
            self.file_manager.hangulFilePathImageRead(self.selected_file_path)

            # 어노테이션 데이터 유무 확인 및 어노테이션 데이터 디스플레이(영상 파일에 대해서만)
            if self.file_manager.check_is_images(self.selected_file_path):
                self.annot_manager.load_annotation_data(self.selected_file_path)

            # 마우스 포인터 원래대로 돌리기
            self.setCursor(Qt.ArrowCursor)

    # 현재 선택된 이미지의 이전 이미지 선택 동작 함수(파일 트리뷰)
    def treeview_file_sel_previous(self):
        if self.model is not None:
            # 현재 선택된 트리 아이템 인덱스
            current_index = self.treeView_file.currentIndex()
            # 현재 선택된 트리 아이템 인덱스에 대한 상위 아이템
            above_index = self.treeView_file.indexAbove(current_index)
            # 폴더 아닌 파일 경로 선택시에만 해당 이전 아이템 선택 동작 수행
            index_item = self.model.index(above_index.row(), 0, above_index.parent())
            tmp_path = self.model.filePath(index_item)
            if os.path.isfile(tmp_path):
                # 변경된 아이템 인덱스에 대해서 파일 트리 아이템 선택에 대한 동작 수행
                self.treeview_file_selected(above_index)
                # 변경된 아이템 인덱스로 선택 포커스 변경
                self.treeView_file.setCurrentIndex(above_index)

    # 현재 선택된 이미지의 다음 이미지 선택 동작 함수(파일 트리뷰)
    def treeview_file_sel_next(self):
        if self.model is not None:
            # 현재 선택된 트리 아이템 인덱스
            current_index = self.treeView_file.currentIndex()
            # 현재 선택된 트리 아이템 인덱스에 대한 하위 아이템
            below_index = self.treeView_file.indexBelow(current_index)
            # 폴더 아닌 파일 경로 선택시에만 해당 이전 아이템 선택 동작 수행
            index_item = self.model.index(below_index.row(), 0, below_index.parent())
            tmp_path = self.model.filePath(index_item)
            if os.path.isfile(tmp_path):
                # 변경된 아이템 인덱스에 대해서 파일 트리 아이템 선택에 대한 동작 수행
                self.treeview_file_selected(below_index)
                # 변경된 아이템 인덱스로 선택 포커스 변경
                self.treeView_file.setCurrentIndex(below_index)

    # 어노테이션 데이터 디스플레이 클래스 선택 콤보박스 선택에 따른 어노테이션 데이터 디스플레이 업데이트
    def update_combo_sel_class(self):
        # 선택 경로가 영상인 경우에만 수행
        if self.flg_img_ok is True:
            # 미리 처리 되어있던 정보를 지우기 위해 처리용 영상 원본 영상으로 초기화
            self.proc_img = self.input_img.copy()

            # 어노테이션 데이터 유무 확인 및 어노테이션 데이터 디스플레이(영상 파일에 대해서만)
            if self.file_manager.check_is_images(self.selected_file_path):
                self.annot_manager.load_annotation_data(self.selected_file_path)

    # 어노테이션 데이터 디스플레이 클래스 선택 콤보박스 선택변경 동작 함수
    def combo_sel_class_change(self):
        # 콤보박스로 선택한 클래스 정보 저장
        self.sel_class_text = str(self.comboBox_sel_class.currentText())

        # 선택 클래스 인덱스와 어노테이션 클래스 배열 인덱스와 맞추기 위해 'Display All'과 'No Show' 인덱스 제외
        curr_index = self.comboBox_sel_class.currentIndex()
        if self.sel_class_text == 'Display All' or self.sel_class_text == 'No Show':
            self.sel_class_index = -1
        else:
            self.sel_class_index = curr_index - 1

        # 클래스 선택에 따른 어노테이션 디스플레이 업데이트
        self.update_combo_sel_class()

    # 현재 선택된 어노테이션 클래스의 이전 클래스 선택 동작 함수(클래스 콤보박스)
    def combo_sel_class_previous(self):
        # 콤보박스 전체 크기 및 현재 클래스 선택정보 확인
        index_size = self.comboBox_sel_class.count() - 1
        curr_index = self.comboBox_sel_class.currentIndex()

        # 현재 선택클래스의 이전 클래스 정보 선택
        if curr_index == 0:
            pre_index = index_size
        else:
            pre_index = curr_index - 1

        # 선택된 클래스 정보 저장
        self.comboBox_sel_class.setCurrentIndex(pre_index)
        self.sel_class_text = str(self.comboBox_sel_class.currentText())

        # 선택 클래스 인덱스와 어노테이션 클래스 배열 인덱스와 맞추기 위해 'Display All'과 'No Show' 인덱스 제외
        curr_index = self.comboBox_sel_class.currentIndex()
        if self.sel_class_text == 'Display All' or self.sel_class_text == 'No Show':
            self.sel_class_index = -1
        else:
            self.sel_class_index = curr_index - 1

        # 클래스 선택에 따른 어노테이션 디스플레이 업데이트
        self.update_combo_sel_class()

    # 현재 선택된 어노테이션 클래스의 다음 클래스 선택 동작 함수(클래스 콤보박스)
    def combo_sel_class_next(self):
        # 콤보박스 전체 크기 및 현재 클래스 선택정보 확인
        index_size = self.comboBox_sel_class.count() - 1
        curr_index = self.comboBox_sel_class.currentIndex()

        # 현재 선택클래스의 다음 클래스 정보 선택
        if curr_index == index_size:
            next_index = 0
        else:
            next_index = curr_index + 1

        # 선택된 클래스 정보 저장
        self.comboBox_sel_class.setCurrentIndex(next_index)
        self.sel_class_text = str(self.comboBox_sel_class.currentText())

        # 선택 클래스 인덱스와 어노테이션 클래스 배열 인덱스와 맞추기 위해 'Display All'과 'No Show' 인덱스 제외
        curr_index = self.comboBox_sel_class.currentIndex()
        if self.sel_class_text == 'Display All' or self.sel_class_text == 'No Show':
            self.sel_class_index = -1
        else:
            self.sel_class_index = curr_index - 1

        # 클래스 선택에 따른 어노테이션 디스플레이 업데이트
        self.update_combo_sel_class()

    """ 프로그램 시작, 종료 등 기타 명령 수행 """
    # 프로그램 설정 파라미터 저장(프로그램 종료시)
    def save_prop_info(self):
        self.config.add_section('Program Setting Information')
        self.config.set('Program Setting Information', 'Last directory path', self.root_path)

        if self.user_id == 'vipslab':
            self.config.set('Program Setting Information', 'user_id', 'test')
        else:
            self.config.set('Program Setting Information', 'user_id', self.user_id)

        with open('setting.ini', 'w') as configfile:
            self.config.write(configfile)

    # 프로그램 설정 파라미터 불러오기(프로그램 시작시)
    def load_prop_info(self):
        self.config.read('setting.ini')
        self.root_path = self.config.get('Program Setting Information', 'Last directory path')
        self.user_id = self.config.get('Program Setting Information', 'user_id')

        self.config.clear()

    # 프로그램 종료 코드
    def closeEvent(self, event):
        # 현재 프로그램 설정 파라미터 저장
        self.save_prop_info()

        print('프로그램 종료')


""" 프로그램 메인 함수 """
# 프로그램 시작(QT application)
app = QApplication(sys.argv)
w = MainWindowClass()
w.setWindowTitle('WeedCroppingManagerNet')
w.show()
app.exec_()
