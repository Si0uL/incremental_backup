import os, logging, sys, time
from shutil import copy2

INPUT_PATH = ""
OUTPUT_PATH = ""

if len(sys.argv) < 2:
    print("usage: {} <logfile>".format(sys.argv[0]))

logging.basicConfig(format='%(asctime)s %(message)s', filename=sys.argv[1],
    level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

assert os.path.isdir(INPUT_PATH) and os.path.isdir(OUTPUT_PATH)

# Copy phase
logging.info("STARTING COPY PHASE")
start_time = time.time()

out_dirpath, in_filepath, out_filepath = "", "", ""
for (in_dirpath, dirnames, filenames) in os.walk(INPUT_PATH):
    out_dirpath = in_dirpath.replace(INPUT_PATH, OUTPUT_PATH)
    if not os.path.exists(out_dirpath):
        os.mkdir(out_dirpath)
        logging.debug("Created dir: %s", out_dirpath)
    for fname in filenames:
        in_filepath = os.path.join(in_dirpath, fname)
        out_filepath = os.path.join(out_dirpath, fname)
        if (not os.path.exists(out_filepath)) or \
            os.path.getmtime(in_filepath) > os.path.getmtime(out_filepath):
            copy2(in_filepath, out_filepath)
            logging.debug("Copied %s to %s", in_filepath, out_filepath)
logging.info("ENDED COPY PHASE")
logging.info("Copy phase duration: %s",
    time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

# Removal phase
logging.info("STARTING REMOVAL PHASE")
start_time = time.time()

dirs_to_rm, files_to_rm = [], []
for (out_dirpath, dirnames, filenames) in os.walk(OUTPUT_PATH):
    in_dirpath = out_dirpath.replace(OUTPUT_PATH, INPUT_PATH)
    if not os.path.exists(in_dirpath):
        dirs_to_rm.append(out_dirpath)
    for fname in filenames:
        in_filepath = os.path.join(in_dirpath, fname)
        out_filepath = os.path.join(out_dirpath, fname)
        if not os.path.exists(in_filepath):
            files_to_rm.append(out_filepath)
for fpath in files_to_rm:
    os.remove(fpath)
    logging.debug("Removed file: %s", fpath)
for dpath in reversed(dirs_to_rm):
    os.rmdir(dpath)
    logging.debug("Removed dir: %s", dpath)
    time.sleep(0.1)
logging.info("ENDED REMOVAL PHASE")
logging.info("Removal phase duration: %s",
    time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
