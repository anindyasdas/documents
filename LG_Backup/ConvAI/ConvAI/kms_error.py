
class KMSError(Exception):
    """
    A class to manage KMSError.
    """
    # define the error codes & messages here
    # AIEFW_ERROR Code 9400 ~ 9599
    # KMS ERROR : 9400 ~ 9449
    # MKG ERROR : 9450 ~ 9499
    # MMKG ERROR : 9500 ~ 9549
    # CL ERROR : 9550 ~ 9599
    # API Error Page http://collab.lge.com/main/x/lYSSQg
    kms_err_offset = 9400
    emsg_enum = {
        # KMS SUCCESS
        0: "[AIEFW] LGAI_AIEFW_KMS_SUCCESS", \
        # KMS API Error
        # HTTP 4XX STATUS Error
        10: "[AIEFW] LGAI_AIEFW_KMS_BAD_REQUEST", \
        11: "[AIEFW] LGAI_AIEFW_KMS_UNAUTHORIZED", \
        13: "[AIEFW] LGAI_AIEFW_KMS_FORBIDDEN", \
        14: "[AIEFW] LGAI_AIEFW_KMS_NOT_FOUND", \
        15: "[AIEFW] LGAI_AIEFW_KMS_METHOD_NOT_ALLOWED", \
        18: "[AIEFW] LGAI_AIEFW_KMS_REQUEST_TIMEOUT", \
        # HTTP 5XX STATUS Error
        20: "[AIEFW] LGAI_AIEFW_KMS_SERVER_ERROR", \
        22: "[AIEFW] LGAI_AIEFW_KMS_BAD_GATEWAY", \
        23: "[AIEFW] LGAI_AIEFW_KMS_SERVICE_UNAVAILABLE", \
        24: "[AIEFW] LGAI_AIEFW_KMS_GATEWAY_TIMEOUT", \
        # KMS Internal Error
        30: "[AIEFW] LGAI_AIEFW_KMS_ENGINE_INIT_ERROR", \
        31: "[AIEFW] LGAI_AIEFW_KMS_ENGINE_CONFIG_ERROR", \
        32: "[AIEFW] LGAI_AIEFW_KMS_ONTOLOGY_CONFIG_ERROR", \
        33: "[AIEFW] LGAI_AIEFW_KMS_EXTERNAL_DB_CONFIG_ERROR",\
    }

    def __init__(self, code):
        self.code = code + self.kms_err_offset
        self.emsg = self.emsg_enum[code]

    def __str__(self):
        return f'KMSError[{self.code}]: {self.emsg}'


if __name__ == "__main__":
    try:
        if True:
            raise KMSError(10)
    except KMSError as e:
        print(e)

