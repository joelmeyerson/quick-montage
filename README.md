## Quick Montage
Generate a montage showing a cryo-EM image with its associated power spectrum and CTF estimate. As inputs the script takes an MRC image file and raw text outputs from CTFFIND4. Process a batch by putting multiple sets of inputs in the target directly.

For each montage the following inputs must be provided in the target directory.

`image_avrot.txt` text file with data to be plotted (from CTFFIND4)

`image.txt` text file with CTF parameters (from CTFFIND4)

`image.mrc` image file used by CTFFIND4 to generate the CTF estimate

### Conda environment
Setup for a conda environment to run the script.

`conda create -n montage` # create environment

`conda install -n montage numpy matplotlib pillow progress` # install packages

`conda install -c conda-forge -n montage mrcfile` # install mrcfile package

`conda activate montage` # activate environment

### Running the script
Command to run the script. The progress of batch processing will be printed to the console.

`python montage.py -p /path/to/target/directory/`

### Example montage
![alt text](https://github.com/joelmeyerson/quick-montage/blob/main/image_montage.png?raw=true)
