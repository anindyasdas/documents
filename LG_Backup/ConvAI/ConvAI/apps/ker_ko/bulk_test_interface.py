from knowledge_extraction.server import flask_main
import argparse
import os

if __name__ == "__main__":
    default_path = "./dataset/bulk_test_data/"
    default_file_name = "test.csv"

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_filepath", "-i",
                        type=str,
                        default=default_file_name,
                        help="Specify input file name to do inference in  csv format")
    p_args = parser.parse_args()
    file_path = default_path + p_args.input_filepath
    if not os.path.exists(file_path):
        print('Input file '+file_path+' does not exist or is incorrect')
        sys.exit(0)
    flask_main.test_report(file_path)