import unittest

from ker.pkr.src.knowledge_extraction.src.docextraction.xml_extractor import XMLExtractor


class TestDocumentExtract(unittest.TestCase):


    def test_model_str(self):
        """
        Validating the model no extraction logic
        """
        obj = XMLExtractor()
        test_str = 'LP0820WSR LP1020WSR LP1220GSR LP1420BSR LP1420BHR'
        model_no_list = obj._get_regex_model_list(test_str)
        print(model_no_list)
        assert model_no_list == ['LP0820W*', 'LP1020W*', 'LP1220G*', 'LP1420B*', 'LP1420B*']

        test_str = 'WT7305C*'
        model_no_list = obj._get_regex_model_list(test_str)
        print(model_no_list)
        assert model_no_list == ['WT7305C*']

        test_str = 'SRFVC2406*'
        model_no_list = obj._get_regex_model_list(test_str)
        print(model_no_list)
        assert model_no_list == ['SRFVC2406*']

        test_str = 'LRFDS3006*/LRFVS3006*/LRFVC2406*/LRFXC2406*/LRFDS3016*/LRFXC2416*/LRFDC2406*'
        model_no_list = obj._get_regex_model_list(test_str)
        # print(model_no_list)
        assert model_no_list == ['LRFDS3006*', 'LRFVS3006*', 'LRFVC2406*',
                                 'LRFXC2406*','LRFDS3016*','LRFXC2416*','LRFDC2406*'],model_no_list

        test_str = 'LMWS27626* / LMWC23626*'
        model_no_list = obj._get_regex_model_list(test_str)
        print(model_no_list)
        assert model_no_list == ['LMWS27626*','LMWC23626*']

        test_str = 'LFXS26973* / LFXC22526* / LFXS28968* / LMXS28626* / LMXS28636* / LMRS28626* / LFXS26566* / ' \
                   'LFXS28566* '
        model_no_list = obj._get_regex_model_list(test_str)
        print(model_no_list)
        assert model_no_list == ['LFXS26973*', 'LFXC22526*', 'LFXS28968*', 'LMXS28626*', 'LMXS28636*',
                                 'LMRS28626*', 'LFXS26566*', 'LFXS28566*']

    def test_extraction(self):
        """
        validating the extracted content manually by writing the extracted
        content to a file
        """
        trob_xml_extract = XMLExtractor.get_section(r"<path_to_xml>\us_main.book.xml", "TROUBLESHOOTING")
        json_data = trob_xml_extract.get_troubleshooting_data()
        with open('troubleshooting_data.json','w') as f:
            f.write(str(json_data))