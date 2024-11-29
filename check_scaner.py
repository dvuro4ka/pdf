import fitz
import cv2
import os
import numpy as np
import easyocr


def get_text_on_image(check_path) -> str:
    try:
        parts = check_path.split("/")
        png_filename = parts[-1][:-4] + ".png"
        png_path = "/".join(parts[:-1]) + "/" + png_filename

        convert_pdf_to_png(check_path, png_path)

        image = cv2.imread(png_path)

        reader = easyocr.Reader(['ru'], gpu=False)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = np.where(gray == 255, 0, 255).astype(np.uint8)
        thresh = cv2.threshold(thresh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        results = reader.readtext(thresh)

        if not results:
            return ""

        text = " ".join([result[1] for result in results])

        return text
    except:
        return ""


def check_text_on_image_easyocr(image) -> bool:
    try:
        reader = easyocr.Reader(['ru'], gpu=False)

        image_height, image_width = image.shape[:2]

        background = np.zeros((round(image_height * 1.5), round(image_width * 1.5), 3), dtype=np.uint8)
        background[:] = (255, 255, 255)

        background_height, background_width = background.shape[:2]
        x = (background_width - image_width) // 2
        y = (background_height - image_height) // 2
        background[y:y + image_height, x:x + image_width] = image.copy()

        gray = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        results = reader.readtext(thresh)

        if not results:
            return True

        text = " ".join([result[1] for result in results])

        parts = text.split()

        if len(parts) == 3 and len(parts[2]) == 2 and parts[2][0].isalpha() and parts[2][1] == '.':
            return False

        if any(part.startswith('+') or part.startswith('Ж') or part.endswith('₽') or part.startswith('ж') or part.startswith('*') for part in parts):
            return False

        if len(parts) == 1 and (len(parts[0]) == 6 or len(parts[0]) == 10):
            return False

        if parts[-1][0] == "(" and parts[-1][-1] == ")":
            return False

        return True
    except:
        return True


def convert_pdf_to_png(pdf_path, png_path): # Конвертирует pdf в png
    doc = fitz.open(pdf_path)
    page = doc[0]
    dpi = 900
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(png_path)


def create_references(ref_pdf_dir): # Создает референсные изображений
    num = 0
    for pdf_filename in os.listdir(ref_pdf_dir):
        if pdf_filename.endswith((".pdf")):
            png_filename = pdf_filename[:-4] + ".png"

            pdf_filename_path = os.path.join(ref_pdf_dir, pdf_filename)
            png_filename_path = os.path.join(ref_pdf_dir, png_filename)
            convert_pdf_to_png(pdf_filename_path, png_filename_path)

            ref_image = cv2.imread(png_filename_path)
            main_img = ref_image.copy()
            ref_gray = cv2.cvtColor(main_img, cv2.COLOR_BGR2GRAY)
            thresh = np.where(ref_gray >= 240, 0, 255).astype(np.uint8)
            for i in range(10):
                thresh[i] = 0
                thresh[int(thresh.shape[0] - i - 1)] = 0
                thresh[:, i] = 0
                thresh[:, int(thresh.shape[1] - 1 - i)] = 0

            cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if len(cnts) == 2 else cnts[1]

            text_areas = []
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                text_areas.append((x, y, x + w, y + h))

            text_areas.sort(key=lambda area: (area[1], area[0]))

            for area in text_areas:
                ref_flag = True
                image = ref_image[area[1]:area[3], area[0]:area[2]].copy()

                for png_ref in os.listdir(ref_pdf_dir):
                    if png_ref.endswith((".png")) and ref_flag:
                        png_ref_path = os.path.join(ref_pdf_dir, png_ref)
                        png_ref_image = cv2.imread(png_ref_path)

                        if np.array_equal(png_ref_image, image):
                            ref_flag = False
                            break

                if ref_flag:
                    image_name = str(area[0]) + "_" + str(area[1]) + "_" + str(area[2]) + "_" + str(area[3]) + "_" + str(num) + ".png"
                    image_name_path = os.path.join(ref_pdf_dir, image_name)
                    cv2.imwrite(image_name_path, image)
                    num = num + 1

            i = 0
            while i < len(text_areas):
                ref_flag = True
                area_left = text_areas[i]
                area_right = area_left
                left = area_left[0]
                right = area_right[2]
                top = area_left[1]
                bottom = area_right[3]

                for j in range(i + 1, len(text_areas)):
                    area = text_areas[j]
                    if (int((area[3] + area[1])/2) == int((top + bottom)/2) and area[2] > area_right[2]) or (area[3] == area_left[3] and area[2] > area_right[2]) or (area[1] > top and area[1] < bottom):
                        area_right = area
                        left = min(left, area_right[0])
                        right = max(right, area_right[2])
                        top = min(top, area_right[1])
                        bottom = max(bottom, area_right[3])
                        i = j

                image = ref_image[top:bottom, left:right].copy()

                if check_text_on_image_easyocr(image):

                    for png_ref in os.listdir(ref_pdf_dir):
                        if png_ref.endswith((".png")) and ref_flag:
                            png_ref_path = os.path.join(ref_pdf_dir, png_ref)
                            png_ref_image = cv2.imread(png_ref_path)

                            if png_ref_image.shape == image.shape:

                                diff = cv2.absdiff(png_ref_image, image)
                                thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY)[1]
                                thresh = cv2.cvtColor(thresh, cv2.COLOR_BGR2GRAY)
                                total_pixels = cv2.countNonZero(thresh)

                                parts = png_ref.split("_")

                                if (total_pixels == 0) and (left == int(parts[0])):
                                    ref_flag = False
                                    break

                    if ref_flag:
                        image_name = str(left) + "_" + str(top) + "_" + str(right) + "_" + str(
                            bottom) + "_" + str(num) + ".png"
                        image_name_path = os.path.join(ref_pdf_dir, image_name)
                        cv2.imwrite(image_name_path, image)
                        num = num + 1

                i += 1

            os.remove(png_filename_path)


def verification_check(check_path, ref_dir) -> float:
    counts_of_mistackes = 0

    parts = check_path.split("/")
    png_filename = parts[-1][:-4] + ".png"
    png_path = "/".join(parts[:-1]) + "/" + png_filename

    convert_pdf_to_png(check_path, png_path)

    check_image = cv2.imread(png_path)
    main_img = check_image.copy()
    check_gray = cv2.cvtColor(main_img, cv2.COLOR_BGR2GRAY)
    thresh = np.where(check_gray >= 240, 0, 255).astype(np.uint8)
    for i in range(10):
        thresh[i] = 0
        thresh[int(thresh.shape[0] - i - 1)] = 0
        thresh[:, i] = 0
        thresh[:, int(thresh.shape[1] - 1 - i)] = 0

    cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    text_areas = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        text_areas.append((x, y, x + w, y + h))

    text_areas.sort(key=lambda area: (area[1], area[0]))

    for area in text_areas:
        area_image = check_image[area[1]:area[3], area[0]:area[2]].copy()
        changes_flag = True

        for filename in os.listdir(ref_dir):
            if filename.endswith((".png")):
                ref_path = os.path.join(ref_dir, filename)

                ref_image = cv2.imread(ref_path)

                if ref_image.shape == area_image.shape:

                    diff = cv2.absdiff(ref_image, area_image)
                    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY)[1]
                    thresh = cv2.cvtColor(thresh, cv2.COLOR_BGR2GRAY)
                    total_pixels = cv2.countNonZero(thresh)

                    if total_pixels == 0:
                        changes_flag = False
                        break

        if changes_flag:
            counts_of_mistackes = counts_of_mistackes + 10
            check_image[area[1]:area[3], area[0]:area[2]] = [0, 0, 0]

    i = 0
    while i < len(text_areas):
        changes_flag = False
        area_left = text_areas[i]
        area_right = area_left
        left = area_left[0]
        right = area_right[2]
        top = area_left[1]
        bottom = area_right[3]

        for j in range(i + 1, len(text_areas)):
            area = text_areas[j]
            if (int((area[3] + area[1]) / 2) == int((top + bottom) / 2) and area[2] > area_right[2]) or (
                    area[3] == area_left[3] and area[2] > area_right[2]) or (area[1] > top and area[1] < bottom):
                area_right = area
                left = min(left, area_right[0])
                right = max(right, area_right[2])
                top = min(top, area_right[1])
                bottom = max(bottom, area_right[3])
                i = j

        image = check_image[top:bottom, left:right].copy()

        if check_text_on_image_easyocr(image):

            for png_ref in os.listdir(ref_dir):
                if png_ref.endswith((".png")):
                    png_ref_path = os.path.join(ref_dir, png_ref)
                    ref_image = cv2.imread(png_ref_path)

                    if ref_image.shape == image.shape:

                        changes_flag = True

                        diff = cv2.absdiff(ref_image, image)
                        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY)[1]
                        thresh = cv2.cvtColor(thresh, cv2.COLOR_BGR2GRAY)
                        total_pixels = cv2.countNonZero(thresh)
                        parts = png_ref.split("_")

                        if (total_pixels == 0) and (left == int(parts[0])):
                            changes_flag = False
                            break

        if changes_flag:
            counts_of_mistackes = counts_of_mistackes + 10
            check_image[top:bottom, left:right] = [0, 0, 0]

        i += 1
    conf = 1 - (counts_of_mistackes * 1.5) / len(text_areas)

    if conf < 0:
        conf = 0
    os.remove(png_path)
    cv2.imwrite(png_path, check_image)
    #os.remove(png_path)

    return conf


import time

def visual_check(check_elm):
    ref_dir = f"./sber_ref_easyocr/"
    check_path = check_elm
    start_time = time.time()
    #create_references(ref_dir)# Время выполнения create_references: 757.5192 секунд
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Время выполнения create_references: {elapsed_time:.4f} секунд")

    start_time = time.time()
    result = verification_check(check_path, ref_dir)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Время выполнения verification_check: {elapsed_time:.4f} секунд")
    # print(result)

    return [result, elapsed_time]
