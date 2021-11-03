## Quick Montage
Generate a montage of a cryo-EM image with its associated power spectrum and CTF estimate. Uses an MRC image file and raw text output of CTFFIND4 as inputs. Process a batch by putting multiple files in the target directly.

For each montage the following inputs must be provided in the target directory.

`image_avrot.txt` text file with data to be plotted

`image.txt` text file with CTF parameters

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
