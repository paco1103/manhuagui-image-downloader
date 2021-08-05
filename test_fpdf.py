from fpdf import FPDF
import os
from PIL import Image

img_dir_path = './test/'
img_path_list = (img_dir_path + img for img in list(os.listdir(img_dir_path)))

pdf_padding = 4

pdf = FPDF()
for img_path in img_path_list:
    image = Image.open(img_path)
    width, height = image.size

    # convert pixel in mm with 1px=0.264583 mm
    width, height = (i * 0.264583 for i in image.size)

    # # given we are working with A4 format size 
    # pdf_size = {'P': {'w': 210, 'h': 297}, 'L': {'w': 297, 'h': 210}}

    # # get page orientation from image size 
    # orientation = 'P' if width < height else 'L'

    # #  make sure image size is not greater than the pdf format size
    # width = width if width < pdf_size[orientation]['w'] else pdf_size[orientation]['w']
    # height = height if height < pdf_size[orientation]['h'] else pdf_size[orientation]['h']

    pdf.add_page(orientation=orientation)

    #TODO image rotate and save by image type
    image = image.rotate(45)
    pdf.image(image, pdf_padding, pdf_padding, width-pdf_padding*2, height-pdf_padding*2)
    
pdf.output("file.pdf", "F")

