#!/usr/bin/env python3

# Script to generate montage of a cryo-EM image with its power spectrum and CTF estimate.
# Adapted from the ctffind_plot_results.sh script written by Alexis Rohou and Tapu Shaik.
# Uses output from CTTFFIND4 by Niko Grigorieff and Alexis Rohou.

# Reads directory containing:
# image_avrot.txt
# image.txt
# image.mrc

import os
import argparse
import io
import numpy as np
import mrcfile
import matplotlib as mpl # to prevent matplotlib from triggering X windows
mpl.use('Agg') # to prevent matplotlib from triggering X windows
import matplotlib.pyplot as plt
from PIL import Image, ImageEnhance, ImageDraw, ImageOps, ImageFont
from progress.bar import Bar

CONTRAST_FACTOR = 5
BRIGHTNESS_FACTOR = 150
BIN_FACTOR = 4
MAX_SPAT_FREQ = 0.4

def main():
    
    # parse arguments
    parser = argparse.ArgumentParser(description='Generate montage of cryo-EM image with its power spectrum and CTF estimate. Requires single-frame image.mrc file and image_avrot.txt and image.txt files from CTFFIND4.')
    parser.add_argument('-p', '--path', type=str, help='path to MRC files and avrot.txt files', required=True)
    args = parser.parse_args()
    
    # check if path exists
    if os.path.exists(args.path) == False:
        print('The path provided does not exist. Exiting.')
        exit()
    
    # format path
    path = args.path
    if path.endswith('/'):
        path = path.rstrip('/')
    
    # get list of avrot files
    files_avrot = []
    for file in os.listdir(path):
        if file.endswith("_avrot.txt"):
            files_avrot.append(file)
    
    # check that at least one avrot files found
    if (len(files_avrot) == 0):
        print("No avrot files found. Exiting.")
        exit()
    
    # create progress bar
    with Bar('Generating montage(s)', fill='-', suffix='%(percent)d%%', max=len(files_avrot)) as bar:
    
        # generate a montage for each avrot file
        for avrot in files_avrot:
        
            # get basename for MRC file and text files
            basename = avrot.strip('_avrot.txt')
        
            # load data in text files (image_avrot.txt and image.txt)
            data = load_data(path, basename)

            # load mrc file
            img_mrc = load_mrc(path + '/' + data[0])

            # make plot image
            plt.figure(figsize=(6,3))
            #plt.axes().set_aspect(0.15)
            plt.plot(data[6], data[7], 'k', label="Power spectrum")
            plt.plot(data[6], data[8], 'c', label="CTF fit")
            plt.plot(data[6], data[9], 'm', label="Quality of fit")
            plt.legend(loc="upper right")
        
            plt.xlim(0, MAX_SPAT_FREQ)
            plt.ylim(0, 1)
            plt.xlabel('Spatial frequency (1/Å)')
            plt.ylabel('Power or cross-correlation')
            plt.tight_layout()
        
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png') # save plt to image buffer
            img_plot = Image.open(img_buffer) # create image from image buffer
        
            # make panel to display file names, apix, voltage, cs, df1 and df2
            font = ImageFont.load_default()
            img_data = Image.new('RGB', (img_plot.width, 130), color = 'gray')
            draw = ImageDraw.Draw(img_data)
            draw.text((10,10), 'MRC file:        ' + data[0])
            draw.text((10,20), 'avrot text file: ' + data[1])
            draw.text((10,30), 'text file:       ' + data[2])
            draw.text((10,40), 'Pixel size (Å): ' + str(data[3]))
            draw.text((10,50), 'Voltage (kV): ' + str(data[4]))
            draw.text((10,60), 'Cs (mm): ' + str(data[5]))
            draw.text((10,70), 'Df1 (Å): ' + str(data[10]))
            draw.text((10,80), 'Df2 (Å): ' + str(data[11]))
            draw.text((10,90), 'Azimuth (°): ' + str(data[12]))
            draw.text((10,100), 'Cross correlation score: ' + str(data[13]))
            draw.text((10,110), 'Spacing up to which CTF rings were fit successfully (Å): ' + str(data[14]))
        
            # make montage
            scale_factor = float(img_plot.width / img_mrc.width) # assumes mrc img is bigger than plot image
            img_mrc = img_mrc.resize((int(img_mrc.width * scale_factor), int(img_mrc.height * scale_factor)), Image.LANCZOS) # resize mrc image
    
            margin = 5
            width = margin + img_mrc.width + margin
            height = margin + img_mrc.height + img_plot.height + img_data.height + margin
            montage = Image.new('RGB', (width, height), '#FFF')
            montage.paste(img_mrc,(margin,margin))
            montage.paste(img_plot,(margin,img_mrc.height + margin))
            montage.paste(img_data,(margin,img_mrc.height + img_plot.height + margin))
            #montage.show()
            montage.save(path + '/' + basename + '_montage.png',"png")

            img_buffer.close()
            plt.close('all')
            bar.next()
        
# function to load image_avrot.txt and image.txt data
def load_data(path, basename):
    
    # load avrot.txt data
    avrot_file = path + '/' + basename + '_avrot.txt'
    
    # check if file exists
    if os.path.exists(avrot_file) == False:
        print('\n')
        print('The file ' + str(avrot_file) + ' does not exist. Exiting.')
        exit()
    
    line_cnt = 0
    with open(avrot_file, "r") as file:
        for line in file:
            line_cnt += 1

            # get mrc name
            # must remove trailing space from string
            if (line_cnt == 2):
                mrc_name = line.split(";")[0].split('/')[-1].strip()

            # get imaging parameters
            if (line_cnt == 3):
                apix = float(line.split(";")[0].split(':')[-1].split()[0])
                kv = float(line.split(";")[1].split(':')[-1].split()[0])
                cs = float(line.split(";")[2].split(':')[-1].split()[0])

            # get spatial frequency (1/Angstroms)
            if (line_cnt == 6):
                vals = line.split()
                spat_freq = []
                for i in vals:
                    spat_freq.append(float(i))

            # get 1D rotational average of spectrum (assuming no astigmatism)
            if (line_cnt == 7):
                vals = line.split()
                rot_avg_ps_astig = []
                for i in vals:
                    rot_avg_ps_astig.append(float(i))

            # get 1D rotational average of spectrum
            if (line_cnt == 8):
                vals = line.split()
                rot_avg_ps = []
                for i in vals:
                    rot_avg_ps.append(float(i))

            # get CTF fit
            if (line_cnt == 9):
                vals = line.split()
                ctf_fit = []
                for i in vals:
                    ctf_fit.append(float(i))

            # get cross-correlation between spectrum and CTF fit
            if (line_cnt == 10):
                vals = line.split()
                cross_corr = []
                for i in vals:
                    cross_corr.append(float(i))
                
        # load image.txt data
        txt_file = path + '/' + basename + '.txt'
        
        # check if file exists
        if os.path.exists(txt_file) == False:
            print('\n')
            print('The file ' + str(txt_file) + ' does not exist. Exiting.')
            exit()
        
        line_cnt = 0
        with open(txt_file, "r") as file:
            for line in file:
                line_cnt += 1

                # get estimated ctf parameters
                if (line_cnt == 6):
                    df1 = float(line.split()[1])
                    df2 = float(line.split()[2])
                    azimuth = float(line.split()[3])
                    cross_corr_score = float(line.split()[5])
                    spacing = float(line.split()[6])
         
    avrot_txt_name = basename + '_avrot.txt'
    txt_name = basename + '.txt'
    
    return [mrc_name, avrot_txt_name, txt_name, apix, kv, cs, spat_freq, rot_avg_ps, ctf_fit, cross_corr, df1, df2, azimuth, cross_corr_score, spacing]

# function to load mrc file
def load_mrc(mrc_img):
    
    # check if file exists
    if os.path.exists(mrc_img) == False:
        print('\n')
        print('The file ' + str(mrc_img) + ' does not exist. Exiting.')
        exit()
    
    mrc = mrcfile.open(mrc_img, mode=u'r', permissive=False, header_only=False)

    # verify image is 2D
    if mrc.data.ndim > 2:
        print("Images must be flat (Z = 1). Cannot process multi-layer images.")
        exit()

    # process image
    img_array = np.flip(mrc.data, axis=0)
    mrc.close()
    img_array = img_array + abs(img_array.min()) # make all 32 bit floating point pixel values >= 0
    img_array /= img_array.max() # normalize all pixels between 0 and 1
    img_array *= 255 # normalize all pixels between 0 and 255

    img = Image.fromarray(img_array).convert("L")
    img = ImageEnhance.Contrast(img).enhance(CONTRAST_FACTOR)
    img = ImageEnhance.Contrast(img).enhance(BRIGHTNESS_FACTOR)
    img = img.reduce(BIN_FACTOR)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    #img = ImageOps.mirror(img)

    return img
    #img.save("./img.png")

if __name__ == "__main__":
    main()