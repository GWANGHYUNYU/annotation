import os
import cv2
import numpy as np
import math
from lxml import etree
import xml.etree.cElementTree as ET

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class AnnotationManager(QWidget):
    def __init__(self, parent=None):
        super(AnnotationManager, self).__init__(parent)

        # 부모인 메인 프로그램 클래스 변수/함수 상속
        self.parent = parent

        # **** 어노테이션 데이터 관련
        # 어노테이션 클래스 지정 정보
        # self.CLASS_LIST = ['leaf', 'flower/fruit', 'entire', 'multi-entire']  # 식물 어노테이션
        self.CLASS_LIST = ['Head', 'Wire', 'entire']                            # 케이블 어노테이션
        self.annotation_formats = {'PASCAL_VOC': '.xml', 'YOLO_darknet': '.txt'}
        self.n_objects = len(self.CLASS_LIST)

        self.flg_mouse_clicked_draw_box = False
        self.flg_mouse_clicked_bbox_selected = False

        self.img_objects = []
        self.is_bbox_selected = False
        self.selected_bbox = -1
        self.prev_selected_bbox = -1
        self.selected_bbox_class = -1

        self.selected_object = None
        self.anchor_being_dragged = None

        self.INPUT_DIR = ''
        self.OUTPUT_DIR = ''

        # 클래스별 색상 다르게 보이기 위한 색상 테이블 지정
        self.class_rgb = [
            (0, 0, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 255, 255),
            (255, 0, 255), (192, 192, 192), (128, 128, 128), (128, 0, 0),
            (128, 128, 0), (0, 128, 0), (128, 0, 128), (0, 128, 128), (0, 0, 128)]
        self.class_rgb = np.array(self.class_rgb)
        # 지정 클래스 수가 색상 테이블보다 많은 경우 랜덤으로 색상 추가
        num_colors_missing = self.n_objects - len(self.class_rgb)
        if num_colors_missing > 0:
            more_colors = np.random.randisnt(0, 255 + 1, size=(num_colors_missing, 3))
            self.class_rgb = np.vstack([self.class_rgb, more_colors])
        self.last_class_index = self.n_objects - 1

    ''' 어노테이션 데이터 로드 함수(메인) '''
    # 어노테이션 데이터 처리 함수
    def load_annotation_data(self, img_path):
        # 바운딩 박스 오브젝트 정보 초기화
        self.img_objects = []

        # 입력 파일 경로에 대해서 폴더 경로와 어노테이션 폴더 경로 설정
        self.INPUT_DIR = os.path.dirname(img_path)
        base_folder = os.path.dirname(self.INPUT_DIR)
        self.OUTPUT_DIR = os.path.join(base_folder, os.path.basename(self.INPUT_DIR) + '_annotated')

        # 어노테이션 폴더 없는 경우 해당 어노테이션 폴더 생성
        for ann_dir in self.annotation_formats:
            new_dir = os.path.join(self.OUTPUT_DIR, ann_dir)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)

        # 어노테이션 파일이 없는 경우 해당 어노테이션 파일 생성(빈파일)
        for ann_path in self.get_annotation_paths(img_path, self.annotation_formats, self.INPUT_DIR, self.OUTPUT_DIR):
            if not os.path.isfile(ann_path):
                if '.txt' in ann_path:
                    open(ann_path, 'a').close()
                elif '.xml' in ann_path:
                    abs_path = os.path.abspath(img_path)
                    folder_name = os.path.dirname(img_path)
                    image_name = os.path.basename(img_path)
                    img_height, img_width, img_depth = (str(number) for number in self.parent.proc_img.shape)
                    self.create_PASCAL_VOC_xml(ann_path, abs_path, folder_name, image_name, img_height, img_width,
                                               img_depth)

        annotation_paths = self.get_annotation_paths(img_path, self.annotation_formats, self.INPUT_DIR, self.OUTPUT_DIR)
        self.draw_bboxes_from_file(annotation_paths)

    ''' 어노테이션 파일 경로 관련 '''
    # 이미지 파일 경로로부터 어노테이션 파일경로 생성
    def get_annotation_paths(self, img_path, annotation_formats, input_dir, output_dir):
        annotation_paths = []
        for ann_dir, ann_ext in annotation_formats.items():
            new_path = os.path.join(output_dir, ann_dir)
            new_path = img_path.replace(input_dir, new_path, 1)
            pre_path, img_ext = os.path.splitext(new_path)
            new_path = new_path.replace(img_ext, ann_ext, 1)
            annotation_paths.append(new_path)
        return annotation_paths

    ''' PASCAL VOC xml / YOLO text 파일 관련 '''
    # PASCAL VOC xml 파일 생성
    def create_PASCAL_VOC_xml(self, xml_path, abs_path, folder_name, image_name, img_height, img_width, img_depth):
        annotation = ET.Element('annotation')
        ET.SubElement(annotation, 'folder').text = folder_name
        ET.SubElement(annotation, 'filename').text = image_name
        ET.SubElement(annotation, 'path').text = abs_path
        source = ET.SubElement(annotation, 'source')
        ET.SubElement(source, 'database').text = 'Unknown'
        size = ET.SubElement(annotation, 'size')
        ET.SubElement(size, 'width').text = img_width
        ET.SubElement(size, 'height').text = img_height
        ET.SubElement(size, 'depth').text = img_depth
        ET.SubElement(annotation, 'segmented').text = '0'

        xml_str = ET.tostring(annotation)
        self.write_xml(xml_str, xml_path)

    # xml 파일 저장
    def write_xml(self, xml_str, xml_path):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_str, parser)

        xml_str = etree.tostring(root, pretty_print=True)

        with open(xml_path, 'wb') as temp_xml:
            temp_xml.write(xml_str)
            
    # Yolo text 어노테이션 데이터 저장 포맷 지정
    def yolo_format(self, class_index, point_1, point_2, width, height):
        x_center = (point_1[0] + point_2[0]) / float(2.0 * width)
        y_center = (point_1[1] + point_2[1]) / float(2.0 * height)
        x_width = float(abs(point_2[0] - point_1[0])) / width
        y_height = float(abs(point_2[1] - point_1[1])) / height
        items = map(str, [class_index, x_center, y_center, x_width, y_height])
        return ' '.join(items)

    # PASCAL voc xml 어노테이션 데이터 저장 포맷 지정
    def voc_format(self, class_name, point_1, point_2):
        xmin, ymin = min(point_1[0], point_2[0]), min(point_1[1], point_2[1])
        xmax, ymax = max(point_1[0], point_2[0]), max(point_1[1], point_2[1])
        items = map(str, [class_name, xmin, ymin, xmax, ymax])
        return items

    # 어노테이션 데이터 파일에 이번 검출 어노테이션 바운딩 박스 정보 붙여넣기
    def append_bb(self, ann_path, line, extension):
        if '.txt' in extension:
            with open(ann_path, 'a') as myfile:
                myfile.write(line + '\n')
        elif '.xml' in extension:
            class_name, xmin, ymin, xmax, ymax = line

            tree = ET.parse(ann_path)
            annotation = tree.getroot()

            obj = ET.SubElement(annotation, 'object')
            ET.SubElement(obj, 'name').text = class_name
            ET.SubElement(obj, 'pose').text = 'Unspecified'
            ET.SubElement(obj, 'truncated').text = '0'
            ET.SubElement(obj, 'difficult').text = '0'

            bbox = ET.SubElement(obj, 'bndbox')
            ET.SubElement(bbox, 'xmin').text = xmin
            ET.SubElement(bbox, 'ymin').text = ymin
            ET.SubElement(bbox, 'xmax').text = xmax
            ET.SubElement(bbox, 'ymax').text = ymax

            xml_str = ET.tostring(annotation)
            self.write_xml(xml_str, ann_path)

    # xml 어노테이션 정보 로드
    def get_xml_object_data(self, obj):
        class_name = obj.find('name').text
        class_index = self.CLASS_LIST.index(class_name)
        bndbox = obj.find('bndbox')
        xmin = int(bndbox.find('xmin').text)
        xmax = int(bndbox.find('xmax').text)
        ymin = int(bndbox.find('ymin').text)
        ymax = int(bndbox.find('ymax').text)
        return [class_name, class_index, xmin, ymin, xmax, ymax]

    # 어노테이션 바운딩 박스 정보 어노테이션 파일에 저장
    def save_bounding_box(self, annotation_paths, class_index, point_1, point_2, width, height):
        for ann_path in annotation_paths:
            if '.txt' in ann_path:
                line = self.yolo_format(class_index, point_1, point_2, width, height)
                self.append_bb(ann_path, line, '.txt')
            elif '.xml' in ann_path:
                line = self.voc_format(self.CLASS_LIST[class_index], point_1, point_2)
                self.append_bb(ann_path, line, '.xml')

    ''' 어노테이션 데이터 관리 관련 '''
    # 어노테이션 정보에 대해서 영상에 정보 디스플레이
    def draw_bboxes_from_file(self, annotation_paths):
        # 입력영상 크기 확인(영상에 따른 어노테이션 정보 크기 맞춰 출력하기 위해
        height, width, bytevalue = self.parent.proc_img.shape

        self.img_objects = []
        ann_path = next(path for path in annotation_paths if 'PASCAL_VOC' in path)
        if os.path.isfile(ann_path):
            # 어노테이션 데이트 파일 경로 확인 및 정보 로드
            tree = ET.parse(ann_path)
            annotation = tree.getroot()

            # 어노테이션 정보에서 각 정보들 로드
            object_list = annotation.findall('object')
            for obj in object_list:
                class_name, class_index, xmin, ymin, xmax, ymax = self.get_xml_object_data(obj)

                # 현재 선택된 클래스 디스플레이 정보에 따른 선택 정보만 그리기 위함
                if (self.parent.sel_class_text != 'Display All') and (class_name != self.parent.sel_class_text):
                    continue

                self.img_objects.append([class_index, xmin, ymin, xmax, ymax])

                color = self.class_rgb[class_index].tolist()
                set_color_pen = (color[0], color[1], color[2])

                thickness = max(int(math.sqrt(height * width) / 500), 1)

                cv2.rectangle(self.parent.proc_img, (xmin, ymin), (xmax, ymax), set_color_pen, thickness)
                cv2.putText(self.parent.proc_img, class_name, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, thickness / 3, set_color_pen, thickness)

        self.update_table_anno_data()
        self.update_label_anno_data(annotation_paths)

    # 어노테이션 바운딩 박스 정보 테이블 위젯 업데이트
    def update_table_anno_data(self):
        ann_cnt = len(self.img_objects)
        # 어노테이션 데이터에 대해서 테이블에 정보 출력
        self.parent.tableWidget_ann_data.clearContents()
        self.parent.tableWidget_ann_data.setEditTriggers(QTableWidget.NoEditTriggers)
        self.parent.tableWidget_ann_data.setSelectionBehavior(QTableWidget.SelectRows)
        self.parent.tableWidget_ann_data.setSelectionMode(QTableWidget.SingleSelection)
        self.parent.tableWidget_ann_data.setAlternatingRowColors(True)
        self.parent.tableWidget_ann_data.setRowCount(ann_cnt)

        table_index = 0
        for obj in self.img_objects:
            class_name = self.CLASS_LIST[obj[0]]
            class_index = obj[0]
            xmin = obj[1]
            ymin = obj[2]
            xmax = obj[3]
            ymax = obj[4]
            # 해당 어노테이션 정보에 대해서 부모 클래스의 어노테이션 디스플레이 테이블에 정보 추가
            item_list = [class_name, '%d' % class_index, '%d' % xmin, '%d' % ymin, '%d' % xmax, '%d' % ymax]

            for column in range(len(item_list)):
                item = QTableWidgetItem(item_list[column])
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.parent.tableWidget_ann_data.setItem(table_index, column, item)

            table_index += 1

        # 윈도우 사이즈에 맞춰 테이블 정보 사이즈 맞추기
        width = int(self.parent.width() * 0.30)
        resize_width = int(width / 6)
        for i in range(6):
            self.parent.tableWidget_ann_data.setColumnWidth(i, resize_width - 5)

        self.parent.tableWidget_ann_data.show()

    # 어노테이션 바운딩 박스 정보 라벨 업데이트
    def update_label_anno_data(self, annotation_paths):
        # 라벨 부분 하드 코딩 체인지
        cnt_arrays = [0] * (self.n_objects)
        all_cnt = 0

        ann_path = next(path for path in annotation_paths if 'PASCAL_VOC' in path)
        if os.path.isfile(ann_path):
            # 어노테이션 데이트 파일 경로 확인 및 정보 로드
            tree = ET.parse(ann_path)
            annotation = tree.getroot()

            # 어노테이션 정보에서 각 정보들 로드
            object_list = annotation.findall('object')
            for obj in object_list:
                class_name, class_index, xmin, ymin, xmax, ymax = self.get_xml_object_data(obj)

                for i in range(self.n_objects):
                    if(class_name == self.CLASS_LIST[i]):
                        cnt_arrays[i] += 1

                all_cnt += 1

        base_str = 'Annotation class information'
        data_str = "( all = {} )".format(all_cnt)
        for i in range(self.n_objects):
            data_str += " [ %s = %d ]"%(self.CLASS_LIST[i], cnt_arrays[i])

        final_str = base_str + data_str
        self.parent.label_anno_class_info.setText(final_str)

    # 선택된 바운딩박스 정보 그리기
    def draw_selected_box(self):
        ind, xmin, ymin, xmax, ymax = self.img_objects[self.selected_bbox]

        height, width, bytevalue = self.parent.proc_img.shape

        color = self.class_rgb[ind].tolist()
        set_color_pen = (color[0], color[1], color[2])

        thickness = max(int(math.sqrt(height * width) / 500), 1)

        rect_overlay_img = self.parent.proc_img.copy()
        addweighted_img = self.parent.proc_img.copy()

        cv2.rectangle(rect_overlay_img, (xmin, ymin), (xmax, ymax), set_color_pen, -1)

        alpha = 0.5
        cv2.addWeighted(rect_overlay_img, alpha, addweighted_img, 1 - alpha, 0, self.parent.proc_img)

        self.parent.tableWidget_ann_data.selectRow(self.selected_bbox)

    # 입력좌표가 지정범위 내에 있는지 확인
    def pointInRect(self, pX, pY, rX_left, rY_top, rX_right, rY_bottom):
        return rX_left <= pX <= rX_right and rY_top <= pY <= rY_bottom

    # 바운딩 박스 영역 얻기
    def get_bbox_area(self, x1, y1, x2, y2):
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return width * height

    # 선택된 바운딩 박스 정보 확인
    def set_selected_bbox(self, pos):
        self.is_bbox_selected = False
        self.selected_bbox = -1
        smallest_area = -1

        real_x = pos[0]
        real_y = pos[1]

        for idx, obj in enumerate(self.img_objects):
            ind, x1, y1, x2, y2 = obj
            x1 = x1 - 5
            y1 = y1 - 5
            x2 = x2 + 5
            y2 = y2 + 5
            if self.pointInRect(real_x, real_y, x1, y1, x2, y2):
                self.is_bbox_selected = True
                tmp_area = self.get_bbox_area(x1, y1, x2, y2)
                if tmp_area < smallest_area or smallest_area == -1:
                    smallest_area = tmp_area
                    self.selected_bbox = idx
                    self.selected_bbox_class = ind

    # 바운딩 박스 정보 지우기
    def delete_bbox_obj(self):
        if self.is_bbox_selected is True:
            obj_to_edit = self.img_objects[self.selected_bbox]
            self.edit_bbox(obj_to_edit, self.parent.selected_file_path, 'delete')
            self.is_bbox_selected = False
            self.selected_bbox = -1

            annotation_paths = self.get_annotation_paths(self.parent.selected_file_path, self.annotation_formats, self.INPUT_DIR, self.OUTPUT_DIR)
            self.parent.proc_img = self.parent.input_img.copy()
            self.draw_bboxes_from_file(annotation_paths)

    # 바운딩 박스 정보 수정
    def edit_bbox(self, obj_to_edit, img_path, action):
        height, width, bytevalue = self.parent.proc_img.shape

        bboxes_to_edit_dict = {}
        current_img_path = img_path
        bboxes_to_edit_dict[current_img_path] = obj_to_edit

        for path in bboxes_to_edit_dict:
            obj_to_edit = bboxes_to_edit_dict[path]
            class_index, xmin, ymin, xmax, ymax = map(int, obj_to_edit)

            for ann_path in self.get_annotation_paths(path, self.annotation_formats, self.INPUT_DIR, self.OUTPUT_DIR):
                if '.txt' in ann_path:
                    with open(ann_path, 'r') as old_file:
                        lines = old_file.readlines()

                    yolo_line = self.yolo_format(class_index, (xmin, ymin), (xmax, ymax), width, height)

                    with open(ann_path, 'w') as new_file:
                        for line in lines:
                            if line != yolo_line + '\n':
                                new_file.write(line)

                elif '.xml' in ann_path:
                    tree = ET.parse(ann_path)
                    annotation = tree.getroot()
                    for obj in annotation.findall('object'):
                        class_name_xml, class_index_xml, xmin_xml, ymin_xml, xmax_xml, ymax_xml = self.get_xml_object_data(obj)
                        if (class_index == class_index_xml and
                                xmin == xmin_xml and
                                ymin == ymin_xml and
                                xmax == xmax_xml and
                                ymax == ymax_xml):
                            if 'delete' in action:
                                annotation.remove(obj)
                            break

                    xml_str = ET.tostring(annotation)
                    self.write_xml(xml_str, ann_path)
