class SpecKeyExtractor(object):
    """
    class used to frame the specification keyword based on main speckey
    """

    KEY = "key"
    DIMENSION = "dimension"
    WATER_PRS = "water pressure"
    TEMP = "temperature"
    GAS_REQ = "gas requirements"
    PWR_CNS = "power consumption"
    SIDE = "side"
    WIDTH = "width"
    HEIGHT = "height"
    DEPTH = "depth"
    OPEN_STS = "open status"
    SIDE_STS = "side status"
    RANGE = "range"
    TYPE = "type"
    BTR_RUN_TIME = "battery run time"

    def extract_spec_key(self, resp):
        """
        Used to handle all types of main spec key to extract specification keyword
        Args:
            resp:response from retrival engine
        return:
            framed spec key
        """
        print(resp[self.KEY])
        key = resp[self.KEY]
        if key == self.DIMENSION:
            return self._extract_dimension(resp)
        elif (key == self.WATER_PRS) or (key == self.TEMP):
            return self._extract_water_pr_temp(resp)
        elif key == self.GAS_REQ:
            return self._extract_gas_req(resp)
        elif key == self.PWR_CNS:
            return self._extract_pwr_cons(resp)
        elif key == self.BTR_RUN_TIME:
            return self._extract_btry_time(resp)
        else:
            return key

    def _extract_dimension(self, resp):
        """
        extract the dimension related speck key framed
        Args:
            resp:response from retrieval engine
        return:
            framed speck key
        """
        spec_key = self.DIMENSION
        if len(resp[self.SIDE].strip()) > 0:
            if (resp[self.SIDE] == self.WIDTH) or (resp[self.SIDE] == self.HEIGHT):
                spec_key = resp[self.SIDE]
            elif resp[self.SIDE] == self.DEPTH:
                spec_key = resp[self.SIDE]
                if self.OPEN_STS in resp.keys():
                    spec_key += " " + resp[self.OPEN_STS] + " " + resp[self.SIDE_STS]
        return spec_key

    def _extract_water_pr_temp(self, resp):
        """
        extract the water pressure and temperatur related speck key framed
        Args:
            resp:response from retrieval engine
        return:
            framed speck key
        """
        spec_key = ""
        key = resp[self.KEY]
        if len(resp[self.RANGE].strip()) > 0:
            spec_key = resp[self.RANGE] + " " + key
        else:
            spec_key = key
        return spec_key

    def _extract_gas_req(self, resp):
        """
        extract the gas requirement related speck key framed
        Args:
            resp:response from retrieval engine
        return:
            framed speck key
        """
        key = resp[self.KEY]
        spec_key = resp[self.RANGE] + " " + resp[self.TYPE] + " " + key
        return spec_key

    def _extract_pwr_cons(self, resp):
        """
        extract the power management related speck key framed
        Args:
            resp:response from retrieval engine
        return:
            framed speck key
        """
        key = resp[self.KEY]
        spec_key = resp[self.RANGE] + " " + key
        return spec_key

    def _extract_btry_time(self, resp):
        """
        extract the battery time related speck key framed
        Args:
            resp:response from retrieval engine
        return:
            framed speck key
        """
        key = resp[self.KEY]
        return key


if __name__ == "__main__":
    speckey_extract = SpecKeyExtractor()
    resp = {"key": "water pressure"}
    print(speckey_extract.extract_spec_key(resp))
