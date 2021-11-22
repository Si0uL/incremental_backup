import os, logging, sys, time, configparser
import string
import ctypes
from datetime import datetime
from shutil import copy2
from typing import Generator

logger = logging.getLogger('incr_backup')

def get_drives() -> Generator:
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            yield letter
        bitmask >>= 1

def get_drive_name(letter: str) -> str:
    volumeNameBuffer = ctypes.create_unicode_buffer(1024)
    fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)
    serial_number = None
    max_component_length = None
    file_system_flags = None

    ctypes.windll.kernel32.GetVolumeInformationW(
        ctypes.c_wchar_p(f"{letter}:\\"),
        volumeNameBuffer,
        ctypes.sizeof(volumeNameBuffer),
        serial_number,
        max_component_length,
        file_system_flags,
        fileSystemNameBuffer,
        ctypes.sizeof(fileSystemNameBuffer)
    )
    return volumeNameBuffer.value

# Ugly fix for special characters
def enc(to_be_escaped: str) -> str:
    return str(to_be_escaped.encode("utf-8"))[2:-1]

def update_repo(input_path: str, dest_path: str) -> None:
    # Copy phase
    logger.debug("STARTING COPY PHASE FOR %s", os.path.basename(input_path))
    start_time = time.time()

    errors_nb = 0
    out_dirpath, in_filepath, out_filepath = "", "", ""
    for (in_dirpath, _, filenames) in os.walk(input_path):
        out_dirpath = in_dirpath.replace(input_path, dest_path)
        if not os.path.exists(out_dirpath):
            try:
                os.mkdir(out_dirpath)
                logger.debug("Created dir: %s", enc(out_dirpath))
            except PermissionError as err:
                errors_nb += 1
                logger.error("[ERROR] Error while creating dir: %s\n%s",
                    enc(out_dirpath), err)

        for fname in filenames:
            in_filepath = os.path.join(in_dirpath, fname)
            out_filepath = os.path.join(out_dirpath, fname)
            if (not os.path.exists(out_filepath)) or \
                os.path.getmtime(in_filepath) > os.path.getmtime(out_filepath):
                try:
                    copy2(in_filepath, out_filepath)
                    logger.debug("Copied %s to %s", enc(in_filepath),
                        enc(out_filepath))
                except PermissionError as err:
                    errors_nb += 1
                    logger.error("[ERROR] Error while copying %s to %s\n%s",
                        enc(in_filepath), enc(out_filepath), err)
    logger.debug("ENDED COPY PHASE FOR %s", os.path.basename(input_path))
    logger.info("Copy phase duration: %s",
        time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

    # Removal phase
    logger.debug("STARTING REMOVAL PHASE FOR %s", os.path.basename(input_path))
    start_time = time.time()

    dirs_to_rm, files_to_rm = [], []
    for (out_dirpath, _, filenames) in os.walk(dest_path):
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
            logger.debug("Removed file: %s", enc(fpath))
        except (PermissionError, OSError) as err:
            errors_nb += 1
            logger.error("[ERROR] Error while trying to remove file: %s\n%s",
                enc(fpath), err)
    for dpath in reversed(dirs_to_rm):
        time.sleep(0.1)
        try:
            os.rmdir(dpath)
            logger.debug("Removed dir: %s", enc(dpath))
        except (PermissionError, OSError) as err:
            errors_nb += 1
            logger.debug("[ERROR] Error while removing dir: %s\n%s", enc(dpath),
                err)

    logger.debug("ENDED REMOVAL PHASE FOR %s", os.path.basename(input_path))
    logger.info("Removal phase duration: %s",
        time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

    if errors_nb > 0:
        logger.warning("%s/ sync. ended with %d errors, check log file for more details\n",
                        os.path.basename(input_path), errors_nb)
    else:
        logger.info("%s/ synchronization finished successfully.\n", os.path.basename(input_path))

if __name__ == '__main__':

    log_idx = 1
    log_file_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        datetime.today().strftime("%Y%m%d") + "-1.log"
    )
    while os.path.exists(log_file_path):
        log_idx += 1
        log_file_path = f"{log_file_path.split('-')[0]}-{log_idx}.log"

    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini'))

    main_out_path = config['OUTPUT']['path']
    if 'drive_name' in config['OUTPUT']:
        found_letter = None
        target_name = config['OUTPUT']['drive_name']
        for drive_letter in get_drives():
            name = get_drive_name(drive_letter)
            if name == target_name:
                found_letter = drive_letter
        assert found_letter, f"Couldn't find drive {target_name}"
        logger.debug("Automatically found driver letter %s: for drive %s",
                     found_letter, target_name)
        # Replace path letter with found one
        main_out_path = found_letter + main_out_path[1:]

    if not os.path.isdir(main_out_path):
        logger.error("Output_Path %s is not a directory", enc(main_out_path))
        sys.exit()

    for target_dir in config['INPUT']:
        in_path = config['INPUT'][target_dir]
        out_path = os.path.join(main_out_path, os.path.basename(in_path))
        if not os.path.isdir(in_path):
            logger.error("input_path %s is not a directory", enc(in_path))
        else:
            logger.info("working on: %s/", os.path.basename(in_path))
            update_repo(in_path, out_path)

    logger.info("All folders synchronized, you can close me!")
    # freeze output for windows usage
    _ = input()
