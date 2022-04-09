"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: purnanaga.nalluri@lge.com
"""

import os
import shutil
import re
import logging as logger
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))))
import params as cs

# Get the image data folder path from config file
IMAGE_FOLDER_PATH, IP_ADDR, PORT_NUMBER = cs.get_image_db_path()


class ImageHandlingInterface(object):
    
    def _get_relative_file_path_template(self, product_type,  part_no, section, sub_section):
        return os.path.join(product_type,  part_no, section, sub_section)

    def _normalize_path_names(self, path_name):
        """
        Function to normalise path names
        """
        normalized_path_name = path_name.strip().lower()
        # Remove any stars and replace them with _
        normalized_path_name = re.sub(r'\W+', '_', normalized_path_name)

        return normalized_path_name

    def get_image_information(self, product_type, section, sub_section, part_no, image_content):
        """
        Function to copy the image to the relative path from absolute location and give the final image information
        like its name and relative path, size and type
        Args:
            product_type: the type of product Ex: refrigerator, washing machine etc .,
            section: Section from the manual content like operation, safety etc.,
            sub_section: name of the subsection like control panel, checklist etc.,
            part_no: the part number of the manual
            image_content: dictionary containing absolute file path, size and image type

        Returns:
            A tuple containing image name and final image content with relative file path
            DATA_NOT_FOUND if the file is not available
        """

        # Check if the image path is valid path and get the name of the image
        file_path_local = image_content[cs.ExtractionConstants.FILE_PATH]

        final_response = {}

        # CHECK IF THE FILE_PATH_LOCAL IS A VALID FILE
        if os.path.isfile(file_path_local):
            logger.debug("Inside image handling interface : Source Image file exists")
            # Get the image name
            _, image_file_name = os.path.split(file_path_local)

            # MAKE THE DIRECTORIES IN THE FORM: product_type/part_no/topic/
            relative_file_path = self._get_relative_file_path_template(
                product_type=self._normalize_path_names(product_type),
                section=self._normalize_path_names(section),
                sub_section=self._normalize_path_names(sub_section),
                part_no=part_no)
            # CREATE A FOLDER PATH INSIDE IMAGE_FOLDER_PATH WITH THE ABOVE relative_file_path
            if not os.path.exists(os.path.join(IMAGE_FOLDER_PATH, relative_file_path)):
                os.makedirs(os.path.join(IMAGE_FOLDER_PATH, relative_file_path))
            # Check if the file already exists

            # Copy the file to the new the relative path location
            copy_src = file_path_local
            copy_dst = os.path.join(IMAGE_FOLDER_PATH, relative_file_path)

            # Check if the file already there with the same name
            if os.path.isfile(os.path.join(copy_dst, image_file_name)):
                logger.info(
                    "Inside image handling interface : Image is available in relative path")
                final_relative_path = os.path.join(copy_dst, image_file_name)
            else:
                logger.info(
                    "Inside image handling interface : Image is not available in relative path :Copying Source to ImageDB")
                final_relative_path = shutil.copy(copy_src, copy_dst)

            final_relative_path = os.path.relpath(final_relative_path, IMAGE_FOLDER_PATH)

            logger.info(
                "Inside image handling interface : relative path " + str(final_relative_path))

            # SEND BACK THE FINAL IMAGE NAME AND CONTENT
            final_image_content = image_content.copy()
            # To remove any path related discrepancies when populated to Neo4j
            final_relative_path = final_relative_path.replace(os.path.sep, '/')
            final_image_content[cs.ExtractionConstants.FILE_PATH] = final_relative_path

            final_response[cs.resp_code] = cs.ResponseCode.SUCCESS
            final_response[cs.resp_data] = {}
            final_response[cs.resp_data][cs.IMAGE_NAME] = image_file_name
            final_response[cs.resp_data][cs.IMAGE_CONTENT] = final_image_content
            return final_response
        else:
            logger.debug("Inside image handling interface : Image not exist")
            final_response[cs.resp_code] = cs.ResponseCode.DATA_NOT_FOUND
            final_response[cs.resp_data] = "Image path is not valid from extraction"
            return final_response


if __name__ == '__main__':
    # logger configuration
    logger.basicConfig(level=logger.INFO,
                       format="%(asctime)s.%(msecs)03d %(levelname)s: %("
                              "funcName)s() %(message)s",
                       datefmt='%Y-%m-%d,%H:%M:%S')

    im_obj = ImageHandlingInterface()

    image_content_temp = {
        "file_path": "C:/Users/purnanaga.nalluri/Desktop/image_to_binary/operation_control_panel_features.png",
        "size": 18768,
        "file_type": "png"
    }

    print(
        im_obj.get_image_information("washing machine", "operation", "control panel", "MFL69497029",
                                     image_content_temp))
