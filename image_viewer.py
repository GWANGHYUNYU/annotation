import cv2
import numpy as np
import math

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class ImageViewer(QWidget):
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent)

        # 부모인 메인 프로그램 클래스 변수/함수 상속
        self.parent = parent

        # 출력 영상(Qt프로그램 디스플레이 관련)
        self.cam_label = self.parent.label_image
        self.qImage = QImage()
        self.qpixmap = QPixmap()

        # 프로그램 윈도우 가로/세로 크기
        self.window_width = 0
        self.window_height = 0
        # 카메라 원본 영상 가로/세로 크기
        self.org_width = 0
        self.org_height = 0
        # 줌(영상 확대/축소)에 의해 변환된 영상 가로/세로 크기
        self.zoom_height = 0
        self.zoom_width = 0
        # 윈도우 크기에 맞춰 변환된 영상 가로/세로 크기
        self.scaled_width = 0
        self.scaled_height = 0

        # 영상 줌(확대/축소) 비율
        self.zoomX = 1

        # 줌(확대/축소) 영상에 대한 시작과 끝 위치
        self.zoom_start_x = 0
        self.zoom_start_y = 0
        self.zoom_end_x = 0
        self.zoom_end_y = 0

        # 실제 윈도우 내의 마우스 위치 좌표
        self.m_pos_x = 0
        self.m_pos_y = 0
        # 실제 윈도우 내에서 배경 제외한 윈도우 내의 마우스 위치 좌표
        self.trans_m_x = 0
        self.trans_m_y = 0
        # 출력 영상 내의 변환된 마우스 위치 좌표
        self.real_m_x = 0
        self.real_m_y = 0
        # 줌(확대/축소) 설정 시의 마우스 위치 좌표
        self.zoom_m_x = 0
        self.zoom_m_y = 0
        # 마우스 클릭 시 여부 확인
        # self.flg_mouse_clicked_draw_box = False
        self.flg_mouse_clicked_bbox_selected = False
        self.clicked_start_trans_m_x = 0
        self.clicked_start_trans_m_y = 0
        self.clicked_end_trans_m_x = 0
        self.clicked_end_trans_m_y = 0
        self.clicked_start_real_m_x = 0
        self.clicked_start_real_m_y = 0
        self.clicked_end_real_m_x = 0
        self.clicked_end_real_m_y = 0

        # 카메라 뷰(qlabel) 연동
        self.parent.label_image.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.__connectEvents()

        # Bbox Maximum / Minimum Threshold Value
        self.bbox_threshold_w = 50
        self.bbox_threshold_h = 50

    def __connectEvents(self):
        # 설정 윈도우 내에서의 마우스 위치 좌표 확인 위함
        self.parent.label_image.setMouseTracking(True)
        self.parent.label_image.mouseMoveEvent = self.mouseMoveAction
        # 영상 줌(확대/축소) 수행 관련
        self.parent.label_image.wheelEvent = self.mouseWheelAction
        # 마우스 클릭 수행 관련
        self.parent.label_image.mousePressEvent = self.mousePressAction
        # 마우스 릴리즈 수행 관련
        self.parent.label_image.mouseReleaseEvent = self.mouseReleaseAction

    # 마우스 휠 이벤트(영상 확대/축소)
    def mouseWheelAction(self, QMouseEvent):
        if not self.qImage.isNull():
            if QMouseEvent.angleDelta().y() > 0:
                self.zoomX += 1
            else:
                if self.zoomX > 1:
                    self.zoomX -= 1

            # 확대/축소 시도 시의 마우스 위치값 따로 저장(마우스위치에 따른 영역 바뀌지 않게)
            self.zoom_m_x = self.real_m_x
            self.zoom_m_y = self.real_m_y

    # 마우스 휠을 통한 줌(확대/축소) 수행 동작 함수
    def zoom(self):
        # 확대/축소 없는 경우 영상 전체 그대로 출력
        if self.zoomX == 1:
            self.zoom_start_x = 0
            self.zoom_start_y = 0
            self.zoom_end_x = int(self.org_width / self.zoomX)
            self.zoom_end_y = int(self.org_height / self.zoomX)
        # 확대/축소 있는 경우 변환된 영상영역 맞춰 출력
        else:
            # 원본 영상에 대해서 줌 배율만큼 크기의 영상만 뽑아서 디스플레이
            # 마우스 중심으로부터 좌우로 확대/축소하여 보이기 위해 1/2
            zoom_sz_x = int(self.org_width / self.zoomX / 2)
            zoom_sz_y = int(self.org_height / self.zoomX / 2)

            # 마우스 좌표에서 1/2의 확대/축소 영상 크기만큼 뺀값을 시작점으로 지정
            self.zoom_start_x = self.zoom_m_x - zoom_sz_x
            self.zoom_start_y = self.zoom_m_y - zoom_sz_y

            # 계산된 시작점이 영상을 벗어나서 마이너스가 될 경우에는 시작점을 0,0으로 지정
            if self.zoom_start_x < 0:
                self.zoom_start_x = 0
            if self.zoom_start_y < 0:
                self.zoom_start_y = 0

            # 시작점으로부터 1/2의 확대/축소 영상 크기만큼 더한값을 종료점으로 지정
            self.zoom_end_x = self.zoom_start_x + (zoom_sz_x * 2)
            self.zoom_end_y = self.zoom_start_y + (zoom_sz_y * 2)

            # 계산된 끝점이 영상의 최대값을 벗어나는 경우 시작점을 차이만큼 옮김
            if self.zoom_end_x > self.org_width:
                self.zoom_end_x = self.org_width
                self.zoom_start_x = self.zoom_start_x - (self.zoom_end_x - self.org_width)
            if self.zoom_end_y > self.org_height:
                self.zoom_end_y = self.org_height
                self.zoom_start_y = self.zoom_start_y - (self.zoom_end_y - self.org_height)

    # 마우스 무브 이벤트(마우스 위치 좌표 확인)
    def mouseMoveAction(self, QMouseEvent):
        if not self.qImage.isNull():
            self.m_pos_x, self.m_pos_y = QMouseEvent.pos().x(), QMouseEvent.pos().y()

            # 영상 내에서 마우스 위치 정보 상태바에 출력
            # 윈도우 크기에 대해서 영상 크기의 비율에 맞춰 실제 마우스 위치와 영상 내 좌표는 다름
            chg_x = int((self.window_width - self.scaled_width) / 2)
            chg_y = int((self.window_height - self.scaled_height) / 2)

            # 실제 마우스좌표를 변환 영상 내의 마우스 좌표로 바꾸려면 윈도우 크기에서 변환영상의 위치
            # 실제 마우스 좌표 = 현재 마우스 좌표 - ((윈도우 크기 - 변환영상 크기) / 2)
            self.trans_m_x = self.m_pos_x - chg_x
            self.trans_m_y = self.m_pos_y - chg_y

            # 계산된 마우스 좌표는 영상을 벗어나는 경우 마이너스 값이나 영상 크기보다 큰값 나오므로 값 제한
            if self.trans_m_x < 0:
                self.trans_m_x = 0
            if self.trans_m_y < 0:
                self.trans_m_y = 0
            if self.trans_m_x > self.scaled_width:
                self.trans_m_x = self.scaled_width
            if self.trans_m_y > self.scaled_height:
                self.trans_m_y = self.scaled_height

            # 변환영상 내에서의 마우스 좌표를 실제 영상크기에 맞는 값으로 변환하여 마우스 위치 좌표 계산
            scale_w = float(self.zoom_width) / float(self.scaled_width)
            scale_h = float(self.zoom_height) / float(self.scaled_height)

            # 변환영상과 원본영상의 비율에 맞춰 원본 영상 내에서의 마우스 좌표값 계산
            real_m_x = int(self.trans_m_x * scale_w)
            real_m_y = int(self.trans_m_y * scale_h)

            # 현재 줌 정보에 따른 실제 영상에 대한 마우스 좌표 값 저장
            self.real_m_x = real_m_x + self.zoom_start_x
            self.real_m_y = real_m_y + self.zoom_start_y

            # 마우스 클릭이 수행 중일 때 현재 마우스 좌표를 클릭에 대한 종료 좌표로 저장
            if self.parent.annot_manager.flg_mouse_clicked_draw_box is True:
                self.clicked_end_trans_m_x = self.trans_m_x
                self.clicked_end_trans_m_y = self.trans_m_y
                self.clicked_end_real_m_x = self.real_m_x
                self.clicked_end_real_m_y = self.real_m_y

    # 마우스 클릭 이벤트
    def mousePressAction(self, QMouseEvent):
            # 마우스 왼쪽 버튼 클릭 동작
            if QMouseEvent.buttons() == Qt.LeftButton:
                # 현재 선택 경로에 대해서 영상 파일이고, 클래스가 선택된 경우에만 수행
                if self.parent.file_manager.check_is_images(
                        self.parent.selected_file_path) and self.parent.sel_class_index >= 0:
                    self.clicked_start_trans_m_x = self.trans_m_x
                    self.clicked_start_trans_m_y = self.trans_m_y
                    self.clicked_end_trans_m_x = self.trans_m_x
                    self.clicked_end_trans_m_y = self.trans_m_y
                    self.clicked_start_real_m_x = self.real_m_x
                    self.clicked_start_real_m_y = self.real_m_y
                    self.clicked_end_real_m_x = self.real_m_x
                    self.clicked_end_real_m_y = self.real_m_y

                    self.parent.annot_manager.flg_mouse_clicked_draw_box = True
                    # print('mouse left clicked')

            # 마우스 오른쪽 버튼 클릭 동작
            elif QMouseEvent.buttons() == Qt.RightButton:
                real_m_pos = (self.real_m_x, self.real_m_y)
                # 클릭 위치가 특정 바운딩박스 안에 있는지 확인
                self.parent.annot_manager.set_selected_bbox(real_m_pos)

                # 특정 바운딩 박스를 선택한 경우
                if self.parent.annot_manager.is_bbox_selected:
                    # 이전 그리기 상황 리셋하고 처리 내용 다시 그리기
                    annotation_paths = self.parent.annot_manager.get_annotation_paths(self.parent.selected_file_path,
                                                                                      self.parent.annot_manager.annotation_formats,
                                                                                      self.parent.annot_manager.INPUT_DIR,
                                                                                      self.parent.annot_manager.OUTPUT_DIR)

                    # 이전에 그려졌던 데이터 지우기 위해 처리영상 다시 입력영상으로 초기화
                    self.parent.proc_img = self.parent.input_img.copy()
                    # 어노테이션 데이터 로드하여 다시그리기
                    self.parent.annot_manager.draw_bboxes_from_file(annotation_paths)
                    # 선택된 바운딩 박스에 대한 선택표시 앵커박스 그리기
                    self.parent.annot_manager.draw_selected_box()
                    
                # 특정 바운딩 박스 선택하지 않고 다른곳 선택한 경우
                else:
                    self.parent.annot_manager.is_bbox_selected = False
                    self.parent.annot_manager.selected_bbox = -1

                    annotation_paths = self.parent.annot_manager.get_annotation_paths(self.parent.selected_file_path,
                                                                                      self.parent.annot_manager.annotation_formats,
                                                                                      self.parent.annot_manager.INPUT_DIR,
                                                                                      self.parent.annot_manager.OUTPUT_DIR)

                    self.parent.proc_img = self.parent.input_img.copy()
                    self.parent.annot_manager.draw_bboxes_from_file(annotation_paths)

                # print('mouse right Clicked')

    # 마우스 릴리스 이벤트
    def mouseReleaseAction(self, QMouseEvent):
        # print('mouse released')
        # 현재 선택 경로에 대해서 영상 파일이고, 클래스가 선택된 경우에만 수행
        if self.parent.file_manager.check_is_images(
                self.parent.selected_file_path) and self.parent.sel_class_index >= 0:
            # 바운딩 박스 그리기 위해 마우스 클릭한 경우 클릭 릴리즈 시 동작
            if self.parent.annot_manager.flg_mouse_clicked_draw_box is True:
                # 박스그리기 위한 마우스 좌표 시작과 종료 좌표가 뒤집힌 경우 반대로 적용
                if self.clicked_start_real_m_x < self.clicked_end_real_m_x:
                    sx = self.clicked_start_real_m_x
                    ex = self.clicked_end_real_m_x
                else:
                    sx = self.clicked_end_real_m_x
                    ex = self.clicked_start_real_m_x

                if self.clicked_start_real_m_y < self.clicked_end_real_m_y:
                    sy = self.clicked_start_real_m_y
                    ey = self.clicked_end_real_m_y
                else:
                    sy = self.clicked_end_real_m_y
                    ey = self.clicked_start_real_m_y

                dw = ex - sx
                dh = ey - sy

                # 최소 크기가 임계치보다 큰 경우만 어노테이션 바운딩박스 정보 저장
                if dw > self.bbox_threshold_w and dh > self.bbox_threshold_h:
                    point_1 = (sx, sy)
                    point_2 = (ex, ey)

                    width = self.org_width
                    height = self.org_height

                    annotation_paths = self.parent.annot_manager.get_annotation_paths(self.parent.selected_file_path,
                                                                                      self.parent.annot_manager.annotation_formats,
                                                                                      self.parent.annot_manager.INPUT_DIR,
                                                                                      self.parent.annot_manager.OUTPUT_DIR)

                    self.parent.annot_manager.save_bounding_box(annotation_paths, self.parent.sel_class_index, point_1, point_2, width, height)
                    self.parent.annot_manager.draw_bboxes_from_file(annotation_paths)

                self.parent.annot_manager.flg_mouse_clicked_draw_box = False

    # 어노테이션 크로핑 클래스 가이드 라인 그리기 함수
    def draw_box_anno_class(self):
        painter = QPainter()
        painter.begin(self.qpixmap)

        color = self.parent.annot_manager.class_rgb[self.parent.sel_class_index].tolist()
        set_color_pen = QColor(color[2], color[1], color[0])
        set_color_brush = QColor(color[2], color[1], color[0])
        set_color_brush.setAlphaF(0.5)

        painter.setPen(QPen(set_color_pen, 3))
        painter.setBrush(set_color_brush)

        # 박스그리기 위한 마우스 좌표 시작과 종료 좌표가 뒤집힌 경우 반대로 적용
        if self.clicked_start_trans_m_x < self.clicked_end_trans_m_x:
            sx = self.clicked_start_trans_m_x
            ex = self.clicked_end_trans_m_x
        else:
            sx = self.clicked_end_trans_m_x
            ex = self.clicked_start_trans_m_x

        if self.clicked_start_trans_m_y < self.clicked_end_trans_m_y:
            sy = self.clicked_start_trans_m_y
            ey = self.clicked_end_trans_m_y
        else:
            sy = self.clicked_end_trans_m_y
            ey = self.clicked_start_trans_m_y

        dw = ex - sx
        dh = ey - sy

        painter.drawRect(sx, sy, dw, dh)

        painter.end()

    # 어노테이션 크로핑 클래스 가이드 라인 그리기 함수
    def draw_guide_line_anno_class(self):
        painter = QPainter()
        painter.begin(self.qpixmap)

        color = self.parent.annot_manager.class_rgb[self.parent.sel_class_index].tolist()
        set_color_pen = QColor(color[2], color[1], color[0])
        set_color_brush = QColor(color[2], color[1], color[0])
        set_color_brush.setAlphaF(0.5)

        painter.setPen(QPen(set_color_pen, 3))
        painter.setBrush(set_color_brush)

        painter.drawLine(self.trans_m_x, 0, self.trans_m_x, self.window_height)
        painter.drawLine(0, self.trans_m_y, self.window_width, self.trans_m_y)

        painter.setFont(QFont("Times", 15, QFont.Bold))
        painter.drawText(QPoint(self.trans_m_x + 5, self.trans_m_y - 5),
                         self.parent.annot_manager.CLASS_LIST[self.parent.sel_class_index])

        painter.end()

    # 전체 디스플레이 가이드 라인 그리기 함수
    def draw_guide_line_display_all(self):
        painter = QPainter()
        painter.begin(self.qpixmap)

        color = (255, 255, 255)
        set_color_pen = QColor(color[2], color[1], color[0])
        set_color_brush = QColor(color[2], color[1], color[0])
        set_color_brush.setAlphaF(0.5)

        painter.setPen(QPen(set_color_pen, 3))
        painter.setBrush(set_color_brush)

        painter.drawLine(self.trans_m_x, 0, self.trans_m_x, self.window_height)
        painter.drawLine(0, self.trans_m_y, self.window_width, self.trans_m_y)

        painter.setFont(QFont("Times", 15, QFont.Bold))
        painter.drawText(QPoint(self.trans_m_x + 5, self.trans_m_y - 5),
                         'Display All')

        painter.end()

    # 입력 영상 디스플레이 함수
    def draw_image(self, cam_img):
        # 입력원본 영상 크기 계산
        self.org_height, self.org_width, cam_img_colors = cam_img.shape

        # 확대/축소 영역 확인 및 적용
        self.zoom()
        zoom_img = cam_img[self.zoom_start_y:self.zoom_end_y, self.zoom_start_x:self.zoom_end_x]
        self.zoom_height, self.zoom_width, zoom_img_colors = zoom_img.shape

        # 카메라 뷰 라벨 윈도우 크기 계산
        self.window_width = self.cam_label.frameSize().width()
        self.window_height = self.cam_label.frameSize().height()

        # 영상 출력을 위해 현재 윈도우 사이즈에 맞춰 영상 크기 변환(변환 비율 계산)
        scale_w = float(self.window_width) / float(self.zoom_width)
        scale_h = float(self.window_height) / float(self.zoom_height)
        scale = min([scale_w, scale_h])

        if scale == 0:
            scale = 1

        scaled_img = cv2.resize(zoom_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # 비율 변환된 영상의 컬러포맷 변경 및 변환 영상 크기계산
        scaled_img = cv2.cvtColor(scaled_img, cv2.COLOR_BGR2RGB)
        self.scaled_height, self.scaled_width, bpc = scaled_img.shape
        bpl = bpc * self.scaled_width

        # 변환영상에 대해서 opencv 영상에서 qt영상 포맷으로 형식 변환
        self.qImage = QImage(scaled_img.data, self.scaled_width, self.scaled_height, bpl, QImage.Format_RGB888)

        # 최종 영상 윈도우에 그리기 준비
        self.cam_label.setStyleSheet("background-color: black;")
        self.qpixmap = QPixmap.fromImage(self.qImage)

        # 영상 열기 성공한 경우에만 가이드라인 및 어노테이션 박스 그리기 수행
        if self.parent.flg_img_ok is True:
            # 현재 클래스 선택정보가 어노테이션 클래스에 해당하는 경우('Display All'이나 'No Show' 아닌경우)
            if self.parent.sel_class_index >= 0:
                # 마우스 클릭 여부 확인(클릭스 어노테이션 박스 그리기 수행중으로 가이드라인 그리지 않음)
                if self.parent.annot_manager.flg_mouse_clicked_draw_box is True:
                    self.draw_box_anno_class()
                # 가이드 라인 그리기
                else:
                    self.draw_guide_line_anno_class()
            else:
                if self.parent.sel_class_text == 'Display All':
                    self.draw_guide_line_display_all()

        # 최종 영상 윈도우에 그리기
        self.cam_label.setPixmap(self.qpixmap)

    def update_frame(self, in_img):
        if self.parent.flg_img_ok is True:
            # 입력 영상 그리기
            self.draw_image(in_img)

            # 상태 바 출력
            text = '[ 해상도(%dx%d) / 마우스(%d, %d) | 경로 : ' % (
            self.org_width, self.org_height, self.real_m_x, self.real_m_y) + self.parent.selected_file_path + ' ]'

            self.parent.statusBar().showMessage(text)
        else:
            # 입력영상 없는 경우 검은 영상 그리기
            zero_img = np.zeros((100, 100, 3), dtype=np.uint8)
            self.draw_image(zero_img)

            # 상태 바 출력
            text = '[ 경로 : ' + self.parent.selected_file_path + ' ]'
            self.parent.statusBar().showMessage(text)



