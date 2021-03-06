#!/usr/bin/python3

# This script reads Matlab MAT files, each one containing a power trace,
# and saves it as a file format suited for Daredevil processing.
#
# This script can be run either invoking python
#   python3 -f mat2Daredevil
# or, if python3 is in the path described in line 1, directly:
#   ./mat2Daredevil.py

#########################################
# Libraries
#########################################
import os

#https://docs.python.org/3/library/binascii.html
import binascii

# Include library to manipulate Matlab MAT files.
# Documentation can be found at:
# https://scipy-cookbook.readthedocs.io/items/Reading_mat_files.html
from scipy.io import loadmat

# Include library to debug python scripts.
# Documentation can be found at:
# https://docs.python.org/3/library/pdb.html
import pdb                      # for python debugging. Continue with 'c'

#########################################
# folder and file definitions
#########################################

# This code expects that the incoming folder contains one file per trace, saved as MAT file, and that
# its name contains the key, plaintext and ciphertext used, in this manner:
# trace_DES__k=f49d7b07c3ee29ef_m=004c5517a01903c7_c=c2eb8188c1e11cd6.mat
INCOMING_FOLDER='/home/luciano/Documentos/ifsul/lifemed/osciloscopio-keysight/c_code/2019-03-1ktraces_mat'
# The file which will be stored the daredevil files - Will be created, if not available
OUTCOMING_FOLDER='2019-03-1ktraces_mat_processed'
TRS_FILENAME='trace-set.trs'

# daredevil files
traces_filename=OUTCOMING_FOLDER+'/'+TRS_FILENAME+'.traces'
input_filename=OUTCOMING_FOLDER+'/'+TRS_FILENAME+'.input'
config_filename=OUTCOMING_FOLDER+'/'+TRS_FILENAME+'.config'

# simple counter
ntraces=0

#########################################
# main code
#########################################

os.system('mkdir '+OUTCOMING_FOLDER)

# opens Daredevil files for editing
traces = open(traces_filename, 'ab')
tracename_file=open(input_filename, 'ab')

# loop over all files from incoming folder
for filename in os.listdir(INCOMING_FOLDER):

    if not filename.endswith(".mat"):
        print('  skipping '+filename)
        # print(os.path.join(directory, filename))
        continue

    # reading matlab files in python, using scipy:
    # https://docs.scipy.org/doc/scipy/reference/tutorial/io.html
    matfile = loadmat(INCOMING_FOLDER+'/'+filename)

    # this data will be needed to recover the original data, in read functions
    # more information on data types can be seen in:
    # https://docs.python.org/2/library/struct.html
    # This is EXACTLY the parameter we need to pass to unpack() function in order to read
    # back the data
    data_format = matfile['trace'][0].dtype.byteorder + matfile['trace'][0].dtype.char
    # this code returns a NUMPY ndarray:
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.html
    trace = matfile['trace'].tobytes()

    # parses filename separating ciphertext (c), plaintext (m) and key (k)
    init_pos=filename.find('k=')
    key=filename[init_pos+2:init_pos+18]

    init_pos=filename.find('m=')
    message=filename[init_pos+2:init_pos+18]

    init_pos=filename.find('c=')
    ciphertext=filename[init_pos+2:init_pos+18]

    # Writes the trace as daredevil expects it
    tracename_file.write(binascii.a2b_hex(message))
    traces.write(trace)

    # ensures we write the data
    tracename_file.flush
    traces.flush()

    # updates data to write to config
    ntraces +=1
    nsamples = len(trace)

    # for debug - stops at each trace processed
    #print('processing '+filename)
    #pdb.set_trace() # for debug. continue with 'c'

    # display a message each 100 traces processed
    if ntraces % 100 == 0 :# or ntraces < 10:
        print(' '+str(ntraces)+' traces processed !')
        break;

# writing config file, for Daredevil
#
# guess is 8 for DES, 16 for AES

with open(config_filename, 'w') as config:
        config.write(
"""
[Traces]
files=1
trace_type={format}
transpose=true
index=0
nsamples={nsamples}
trace={traces_filename} {ntraces} {nsamples}

[Guesses]
files=1
guess_type=u
transpose=true
guess={input_filename} {ntraces} 8

[General]
threads=8
order=1
return_type=double
algorithm=AES
position=LUT/DES_BEFORE_SBOX
round=0
bitnum=none
bytenum=all
#correct_key={key}
memory=4G
top=20
""".format(format=data_format, ntraces=ntraces, nsamples=nsamples, traces_filename=traces_filename, input_filename=input_filename, key=key))


