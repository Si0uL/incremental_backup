import os, logging, sys, time
from shutil import copy2

INPUT_PATH = "D:\\Louis"
OUTPUT_PATH = "G:\\Louis_backup"

# Ugly fix for special characters
def enc(string):
    return str(string.encode("utf-8"))[2:-1]

if len(sys.argv) < 2:
    print("usage: {} <logfile>".format(sys.argv[0]))
    sys.exit()

logging.basicConfig(format='%(asctime)s %(message)s', filename=sys.argv[1],
    level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

if not os.path.isdir(INPUT_PATH):
    print("INPUT_PATH {} is not a directory".format(INPUT_PATH))
    sys.exit()

if not os.path.isdir(OUTPUT_PATH):
    print("OUTPUT_PATH {} is not a directory".format(OUTPUT_PATH))
    sys.exit()

# Copy phase
logging.info("STARTING COPY PHASE")
start_time = time.time()

errors_nb = 0
out_dirpath, in_filepath, out_filepath = "", "", ""
for (in_dirpath, dirnames, filenames) in os.walk(INPUT_PATH):
    out_dirpath = in_dirpath.replace(INPUT_PATH, OUTPUT_PATH)
    if not os.path.exists(out_dirpath):
        try:
            os.mkdir(out_dirpath)
            logging.debug("Created dir: %s", enc(out_dirpath))
        except PermissionError as err:
            errors_nb += 1
            logging.debug("[ERROR] Error while creating dir: %s\n%s",
                enc(out_dirpath), err)

    for fname in filenames:
        in_filepath = os.path.join(in_dirpath, fname)
        out_filepath = os.path.join(out_dirpath, fname)
        if (not os.path.exists(out_filepath)) or \
            os.path.getmtime(in_filepath) > os.path.getmtime(out_filepath):
            try:
                copy2(in_filepath, out_filepath)
                logging.debug("Copied %s to %s", enc(in_filepath),
                    enc(out_filepath))
            except PermissionError as err:
                errors_nb += 1
                logging.error("[ERROR] Error while copying %s to %s\n%s",
                    enc(in_filepath), enc(out_filepath), err)
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
    try:
        os.remove(fpath)
        logging.debug("Removed file: %s", enc(fpath))
    except PermissionError as err:
        errors_nb += 1
        logging.error("[ERROR] Error while trying to remove file: %s\n%s",
            enc(fpath), err)
for dpath in reversed(dirs_to_rm):
    time.sleep(0.1)
    try:
        os.rmdir(dpath)
        logging.debug("Removed dir: %s", enc(dpath))
    except (PermissionError, OSError) as err:
        errors_nb += 1
        logging.debug("[ERROR] Error while removing dir: %s\n%s", enc(dpath),
            err)

logging.info("ENDED REMOVAL PHASE")
logging.info("Removal phase duration: %s",
    time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

if errors_nb > 0:
    print("[WARNING] Script ended with {} errors, check log file for more details".format(
        errors_nb))
