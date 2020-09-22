# Example

This is an example for running parallelized jobs with 2 input and 2 output values with a python application with the PCR framework.

# Perquisites
* the infrastructure is set up
* the AWS CLI is available locally and configured with credentials that allow access to the infrastructure
* Docker is available locally
* the name of the S3 job bucket is known

# Usage

## 1. Preparation
1. Copy the example folder to your machine.  (optional)
2. Create and activate a python environment. (optional)
3. Install the PCR package, e.g. with
    * `pip install -e git+git@gitlab.lrz.de:000000003B9B9936/pcr.git#egg=PCR`
    * or `pip install -e .` (when in project directory)


## 2. Create the docker application
1. open the `worker` folder in your command line
2. run the docker commands to build, tag and push the image (see `README.md` in project folder)

## 3. Start a job with the python script
1. read the `start_job.py` script
2. follow the instructions and start a job with the script
