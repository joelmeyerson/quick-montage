## Quick Montage
Generate a montage showing a cryo-EM image with its associated power spectrum and CTF estimate. As inputs the script takes an MRC image file and raw text outputs from CTFFIND4. Process a batch by putting multiple sets of inputs in the target directly.

For each montage the following inputs must be provided in the target directory.

`image.mrc` image file used by CTFFIND4 to generate the CTF estimate

`image_avrot.txt` text file with data to be plotted (from CTFFIND4)

`image.txt` text file with CTF parameters (from CTFFIND4)


### Setting up environment
Setup for a virtual environment to run the script.

`cd quick-montage` # Navigate to the project directory.

`python -m venv venv` # Create the virtual environment.

`source ./venv/bin/activate` # Activate the virtual environment.

`pip install -r requirements.txt` # Install the packages.

or

`pip install mrcfile numpy matplotlib pillow progress`


### Running the script
Use this command to run the script. The progress of batch processing will be printed to the console.

`python montage.py -p /path/to/target/directory/`

### Example montage
This is an example montage using Kv1.3/nanobody data from [Selvakumar *et al.* Nature Communications 2022](https://pubmed.ncbi.nlm.nih.gov/35788586/).

![alt text](https://github.com/joelmeyerson/quick-montage/blob/main/image_montage.png?raw=true)
