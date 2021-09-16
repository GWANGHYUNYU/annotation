import cv2
import numpy as np
import os
import xml.etree.ElementTree as ET


def make_directory(name_file):
    try:
        os.makedirs(name_file)
        print("Directory ", name_file, " Created ")
    except FileExistsError:
        print("Directory ", name_file, " already exists")


def crop_an_image(img, bb):
    cl, x, y, w, h = bb

    # make it square
    if (w > h):
        sz = w
    else:
        sz = h
    half_sz = sz // 2

    # shift bouding box in boundary case
    y = y + abs(y - half_sz) * (y < half_sz)
    x = x + abs(x - half_sz) * (x < half_sz)

    sub_img = img[(y - half_sz):(y + half_sz), (x - half_sz):(x + half_sz)]
    sub_img = cv2.resize(sub_img, (sz, sz))

    return sub_img


### directory level
# data
#    speice 1
#        class 1
#        class 1_annotation: .xml, .txt
#        class 2
#        class 2_annotation: .xml, .txt
#    speice 2
#        class 1
#        class 1_annotation: .xml, .txt
#        class 2
#        class 2_annotation: .xml, .txt


def crop_by_txt(folder_name="crop_data"):
    make_directory(folder_name)

    sp_list = os.listdir("data")
    n_class = 0
    for speice in os.listdir("data"):  # speice level

        n_speice = sp_list.index(speice)
        print(speice)
        make_directory(os.path.join(folder_name, speice))

        cl_list = [cl for cl in os.listdir(os.path.join("data", speice)) if (cl.find("annotated") == -1)]
        for cl in cl_list:  # class level

            n_class = cl_list.index(cl)
            print(cl)
            make_directory(os.path.join(folder_name, speice, cl))

            # global n_instance
            n_instance = 0
            for f in os.listdir(os.path.join("data", speice, cl))[:2]:  # file level
                print(f)
                img = cv2.imdecode(np.fromfile(os.path.join("data", speice, cl, f)), cv2.IMREAD_UNCHANGED)
                h_img, w_img = img.shape[:2]
                # img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                with open(os.path.join("data", speice, cl + "_annotated", "YOLO_darknet", f[:-4] + ".txt")) as f:
                    lines = f.readlines()

                    save_file = os.path.join(folder_name, speice, cl, "_".join([str(n_speice), str(n_class)]))
                    # Parallel(n_jobs=n_core)(delayed(crop_and_save_image)(img, bb, save_file, n_instance) for bb in lines)

                    for bb in lines:  # bounding box level
                        cl_index, x, y, w, h = bb[:-1].split(" ")
                        cl_index, x, y, w, h = int(cl_index), int(float(x) * w_img), int(float(y) * h_img), int(
                            float(w) * w_img), int(float(h) * h_img)
                        sub_img = crop_an_image(img, bb=[cl_index, x, y, w, h])

                        is_success, im_buf_arr = cv2.imencode(".jpg", sub_img)
                        im_buf_arr.tofile(save_file + str(n_instance) + ".jpg")
                        n_instance += 1
                del img


def crop_by_xml(folder_name="crop_data"):
    make_directory(folder_name)

    sp_list = os.listdir("data")
    n_class = 0
    for speice in os.listdir("data"):  # speice level

        n_speice = sp_list.index(speice)
        print(speice)
        make_directory(os.path.join(folder_name, speice))

        cl_list = [cl for cl in os.listdir(os.path.join("data", speice)) if (cl.find("annotated") == -1)]
        for cl in cl_list:  # class level

            n_class = cl_list.index(cl)
            print(cl)
            make_directory(os.path.join(folder_name, speice, cl))

            # global n_instance
            n_instance = 0
            for f in os.listdir(os.path.join("data", speice, cl))[:2]:  # file level
                print(f)
                img = cv2.imdecode(np.fromfile(os.path.join("data", speice, cl, f)), cv2.IMREAD_UNCHANGED)

                with open(os.path.join("data", speice, cl + "_annotated", "PASCAL_VOC", f[:-4] + ".xml")) as f:

                    tree = ET.parse(f)
                    annotation = tree.getroot()

                    save_file = os.path.join(folder_name, speice, cl, "_".join([str(n_speice), str(n_class)]))

                    for bb in annotation.findall('object'):  # bounding box level

                        class_name = bb.find('name').text
                        bndbox = bb.find('bndbox')
                        xmin = int(bndbox.find('xmin').text)
                        xmax = int(bndbox.find('xmax').text)
                        ymin = int(bndbox.find('ymin').text)
                        ymax = int(bndbox.find('ymax').text)
                        x = (xmax + xmin) // 2
                        y = (ymax + ymin) // 2
                        w = xmax - xmin
                        h = ymax - ymin

                        sub_img = crop_an_image(img, bb=[class_name, x, y, w, h])

                        is_success, im_buf_arr = cv2.imencode(".jpg", sub_img)
                        im_buf_arr.tofile(save_file + str(n_instance) + ".jpg")
                        n_instance += 1
                del img


if __name__ == "__main__":
    crop_by_xml()