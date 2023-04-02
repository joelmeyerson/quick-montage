#!/usr/bin/env python3

"""Quick Montage
This script produces a montage of a cryo-EM image with its power spectrum and CTF 
estimate. It runs in batch mode and will process all available date in the target 
direction. The script was adapted from the ctffind_plot_results.sh script written 
by Alexis Rohou and Tapu Shaik and uses output from CTTFFIND4 written by 
Niko Grigorieff and Alexis Rohou.

Usage:
    python montage.py -p /path/to/target/directory/

Inputs:
    image.mrc
    image_avrot.txt
    image.txt
"""

import argparse
import io
import os
import sys

import mrcfile
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from progress.bar import Bar

from constants import (
    CONTRAST_FACTOR,
    BRIGHTNESS_FACTOR,
    BIN_FACTOR,
    MAX_SPAT_FREQ,
    MARGIN,
)

matplotlib.use("Agg")  # Prevent matplotlib from triggering X windows.


def main():
    parser = argparse.ArgumentParser(
        description="Generate a montage of a cryo-EM image with its power spectrum and CTF estimate."
    )
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        help="The path to .mrc, _avrot.txt, and .txt files",
        required=True,
    )
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print("The path provided does not exist. Exiting.")
        sys.exit()

    path = args.path.rstrip("/")  # If the path has a trailing forward slash remove it.
    mrc_files = tuple(
        sorted([file for file in os.listdir(path) if file.endswith(".mrc")])
    )
    avrot_txt_files = tuple(
        sorted([file for file in os.listdir(path) if file.endswith("_avrot.txt")])
    )
    txt_files = tuple(
        sorted(
            [
                file
                for file in os.listdir(path)
                if file.endswith(".txt") and "avrot" not in file
            ]
        )
    )

    if not len(mrc_files) == len(avrot_txt_files) == len(txt_files):
        print(
            f"The script detected {len(mrc_files)} .mrc files, "
            f"{len(avrot_txt_files)} _avrot.txt, and {len(txt_files)} .txt files. "
            "Please make sure that the numbers are equal."
        )
        sys.exit()

    with Bar(
        "Generating montage(s)",
        fill="-",
        suffix="%(percent)d%%",
        max=len(avrot_txt_files),
    ) as bar:
        for idx in range(len(mrc_files)):
            validate_inputs(mrc_files[idx], avrot_txt_files[idx], txt_files[idx])

            basename = mrc_files[idx].rstrip(".mrc")
            avrot_txt_data = load_avrot_txt_data(path, avrot_txt_files[idx])
            txt_data = load_txt_data(path, txt_files[idx])
            img_mrc = load_mrc(f"{path}/{avrot_txt_data['mrc_name']}")

            plt.figure(figsize=(6, 3))
            # plt.axes().set_aspect(0.15)
            plt.plot(
                avrot_txt_data["spat_freq"],
                avrot_txt_data["rot_avg_ps"],
                "k",
                label="Power spectrum",
            )
            plt.plot(
                avrot_txt_data["spat_freq"],
                avrot_txt_data["ctf_fit"],
                "c",
                label="CTF fit",
            )
            plt.plot(
                avrot_txt_data["spat_freq"],
                avrot_txt_data["cross_corr"],
                "m",
                label="Quality of fit",
            )
            plt.legend(loc="upper right")
            plt.xlim(0, MAX_SPAT_FREQ)
            plt.ylim(0, 1)
            plt.xlabel("Spatial frequency (1/Å)")
            plt.ylabel("Power or cross-correlation")
            plt.tight_layout()

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png")  # Save plt to image buffer.
            img_plot = Image.open(img_buffer)  # Create image from image buffer.

            # font = ImageFont.load_default()
            img_data = Image.new("RGB", (img_plot.width, 130), color="gray")
            draw = ImageDraw.Draw(img_data)
            draw.text((10, 10), "MRC file:        " + avrot_txt_data["mrc_name"])
            draw.text((10, 20), "avrot text file: " + avrot_txt_data["avrot_txt_file"])
            draw.text((10, 30), "text file:       " + txt_data["txt_file"])
            draw.text((10, 40), "Pixel size (Å): " + str(avrot_txt_data["apix"]))
            draw.text((10, 50), "Voltage (kV): " + str(avrot_txt_data["kv"]))
            draw.text((10, 60), "Cs (mm): " + str(avrot_txt_data["cs"]))
            draw.text((10, 70), "Df1 (Å): " + str(txt_data["df1"]))
            draw.text((10, 80), "Df2 (Å): " + str(txt_data["df2"]))
            draw.text((10, 90), "Azimuth (°): " + str(txt_data["azimuth"]))
            draw.text(
                (10, 100),
                "Cross correlation score: " + str(txt_data["cross_corr_score"]),
            )
            draw.text(
                (10, 110),
                "Spacing up to which CTF rings were fit successfully (Å): "
                + str(txt_data["spacing"]),
            )

            # Assume mrc img is bigger than plot image.
            scale_factor = float(img_plot.width / img_mrc.width)
            # Resize mrc image.
            img_mrc = img_mrc.resize(
                (int(img_mrc.width * scale_factor), int(img_mrc.height * scale_factor)),
                Image.LANCZOS,
            )

            width = MARGIN + img_mrc.width + MARGIN
            height = (
                MARGIN + img_mrc.height + img_plot.height + img_data.height + MARGIN
            )
            montage = Image.new("RGB", (width, height), "#FFF")
            montage.paste(img_mrc, (MARGIN, MARGIN))
            montage.paste(img_plot, (MARGIN, img_mrc.height + MARGIN))
            montage.paste(img_data, (MARGIN, img_mrc.height + img_plot.height + MARGIN))
            # montage.show()
            montage.save(path + "/" + basename + "_montage.png", "png")

            img_buffer.close()
            plt.close("all")
            bar.next()


def validate_inputs(mrc_file_name, avrot_txt_file_name, txt_file_name):
    if (
        not mrc_file_name.rstrip(".mrc")
        == avrot_txt_file_name.rstrip("_avrot.txt")
        == txt_file_name.rstrip(".txt")
    ):
        print(
            "\n\nThe following files should have matching base names but do not:"
            f"\n\n{mrc_file_name}\n{avrot_txt_file_name}\n{txt_file_name}\n\n"
            "Please check input file names to be sure they meet the input specifications. "
            "Exiting."
        )
        sys.exit()


def load_avrot_txt_data(path, avrot_txt_file):
    avrot_txt_file_lines = []
    with open(f"{path}/{avrot_txt_file}", "r") as file:
        for line in file:
            avrot_txt_file_lines.append(line)
    data = {}
    data["avrot_txt_file"] = avrot_txt_file
    data["mrc_name"] = avrot_txt_file_lines[1].split(";")[0].split("/")[-1].strip()
    data["apix"] = float(
        avrot_txt_file_lines[2].split(";")[0].split(":")[-1].split()[0]
    )
    data["kv"] = float(avrot_txt_file_lines[2].split(";")[1].split(":")[-1].split()[0])
    data["cs"] = float(avrot_txt_file_lines[2].split(";")[2].split(":")[-1].split()[0])
    data["spat_freq"] = [float(val) for val in avrot_txt_file_lines[5].split()]
    data["rot_avg_ps_astig"] = [float(val) for val in avrot_txt_file_lines[6].split()]
    data["rot_avg_ps"] = [float(val) for val in avrot_txt_file_lines[7].split()]
    data["ctf_fit"] = [float(val) for val in avrot_txt_file_lines[8].split()]
    data["cross_corr"] = [float(val) for val in avrot_txt_file_lines[9].split()]

    return data


def load_txt_data(path, txt_file):
    txt_file_lines = []
    with open(f"{path}/{txt_file}", "r") as file:
        for line in file:
            txt_file_lines.append(line)

    data = {}
    data["txt_file"] = txt_file
    data["df1"] = float(txt_file_lines[5].split()[1])
    data["df2"] = float(txt_file_lines[5].split()[2])
    data["azimuth"] = float(txt_file_lines[5].split()[3])
    data["cross_corr_score"] = float(txt_file_lines[5].split()[5])
    data["spacing"] = float(txt_file_lines[5].split()[6])

    return data


def load_mrc(mrc_img):
    mrc = mrcfile.open(mrc_img, mode="r", permissive=False, header_only=False)

    # Verify image is 2D.
    if mrc.data.ndim > 2:
        print("Images must be flat (Z = 1). Cannot process multi-layer images.")
        exit()

    img_array = np.flip(mrc.data, axis=0)
    mrc.close()
    # Make all 32 bit floating point pixel values >= 0.
    img_array = img_array + abs(img_array.min())
    # Normalize all pixels between 0 and 1.
    img_array /= img_array.max()
    # Normalize all pixels between 0 and 255.
    img_array *= 255

    img = Image.fromarray(img_array).convert("L")
    img = ImageEnhance.Contrast(img).enhance(CONTRAST_FACTOR)
    img = ImageEnhance.Contrast(img).enhance(BRIGHTNESS_FACTOR)
    img = img.reduce(BIN_FACTOR)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    # img = ImageOps.mirror(img)

    return img
    # img.save("./img.png")


if __name__ == "__main__":
    main()
