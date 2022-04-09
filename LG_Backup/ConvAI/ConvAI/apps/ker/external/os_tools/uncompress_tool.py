"""
/*-------------------------------------------------
* Copyright(c) 2021 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
"""
import tarfile
import os
import logging as logger
import tempfile
import shutil


def extract_compressed_files(folder_path, compressed_file_name, uncompressed_folder_name=None):
    """
    function to uncompress the model files
    Args:
        folder_path: path where the folder should be in KER code base e.g Dataset/models/SRL/
        compressed_file_name: name of the uncompressed model folder e.g.bert_en_12H_768
        uncompressed_folder_name : name to be given to the folder after unzipping
    """
    if uncompressed_folder_name is None:
        # for cases where the unzipped file name and the name of unzipped file are same
        uncompressed_folder_name = compressed_file_name
    if os.path.isdir(os.path.join(folder_path, uncompressed_folder_name)):
        # check if it is in the directory path within the codebase
        logger.info("The unzipped file " + uncompressed_folder_name + " already exists. Hence not replaced.")
        return True
    elif os.path.isdir(os.path.join(tempfile.gettempdir(), uncompressed_folder_name)):
        # check if it exists in temp directory
        logger.info("The unzipped file " + uncompressed_folder_name + " already exists in temp directory.")
        shutil.move(os.path.join(tempfile.gettempdir(), uncompressed_folder_name),
                    os.path.join(folder_path, uncompressed_folder_name))
        logger.info("Moving it to " + folder_path + uncompressed_folder_name)
        return True
    else:
        # when the file is not in both the locations unzip it
        if not os.path.isfile(os.path.join(folder_path, compressed_file_name + ".tar.gz")):
            logger.error(
                "zipped model file does not exist " + os.path.join(folder_path, compressed_file_name + ".tar.gz"))
            return False

        my_tar = tarfile.open(os.path.join(folder_path, compressed_file_name + ".tar.gz"))
        my_tar.extractall(os.path.join(folder_path, uncompressed_folder_name))
        my_tar.close()
        logger.info("Folder unzipped in " + uncompressed_folder_name)
        return True
