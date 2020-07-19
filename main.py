import os, logging, sys, time, configparser
from datetime import datetime
from shutil import copy2

# Ugly fix for special characters
def enc(string):
    return str(string.encode("utf-8"))[2:-1]

def update_repo(input_path, dest_path):
    # Copy phase
    logging.info(f"STARTING COPY PHASE FOR {os.path.basename(input_path)}")
    start_time = time.time()

    errors_nb = 0
    out_dirpath, in_filepath, out_filepath = "", "", ""
    for (in_dirpath, dirnames, filenames) in os.walk(input_path):
        out_dirpath = in_dirpath.replace(input_path, dest_path)
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
    logging.info(f"ENDED COPY PHASE FOR {os.path.basename(input_path)}")
    logging.info("Copy phase duration: %s\n",
        time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

    # Removal phase
    logging.info(f"STARTING REMOVAL PHASE FOR {os.path.basename(input_path)}")
    start_time = time.time()

    dirs_to_rm, files_to_rm = [], []
    for (out_dirpath, dirnames, filenames) in os.walk(dest_path):
        in_dirpath = out_dirpath.replace(dest_path, input_path)
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

    logging.info(f"ENDED REMOVAL PHASE FOR {os.path.basename(input_path)}")
    logging.info("Removal phase duration: %s\n\n",
        time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

    if errors_nb > 0:
        print(f"[WARNING] {os.path.basename} sync. ended with {errors_nb} errors, " + \
            "check log file for more details")

if __name__ == '__main__':

    log_idx = 1
    log_file_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        datetime.today().strftime("%Y%m%d") + "-1.log"
    )
    while os.path.exists(log_file_path):
        log_idx += 1
        log_file_path = log_file_path[:-5] + str(log_idx) + '.log'

    logging.basicConfig(format='%(asctime)s %(message)s', filename=log_file_path,
        level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini'))

    main_out_path = config['OUTPUT']['path']
    if not os.path.isdir(main_out_path):
        print(f"Output_Path {enc(main_out_path)} is not a directory")
        sys.exit()

    for dir in config['INPUT']:
        in_path = config['INPUT'][dir]
        if not os.path.isdir(in_path):
            print(f"input_path {enc(in_path)} is not a directory")
            logging.error("input_path %s is not a directory", enc(in_path))
            continue

        out_path = os.path.join(main_out_path, os.path.basename(in_path))
        update_repo(in_path, out_path)
