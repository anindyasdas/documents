"""
/*-------------------------------------------------
* Copyright(c) 2020 by LG Electronics.
* Confidential and Proprietary All Rights Reserved.
*-------------------------------------------------*/
@author: anusha.kamath@lge.com
"""
import pandas as pd
from os.path import splitext as os_spt
import sys

from . import constants


def read_input(path, header=0, delimiter=" "): # pragma: no cover
    """
    Generic function to read inputs
    Args:
        path: input file path
        header : None if no header , row number if there is a header in input data
        delimiter: delimiter character if it is a delimited file
    Returns: A dataframe of the read file
    """
    ext = os_spt(path)[1]
    if ext == ".csv":
        df = pd.read_csv(path, header=header)
        return df
    elif ext == ".tsv":
        df = pd.read_csv(path, sep="\t", header=header)
        return df
    elif ext == ".txt":
        df = pd.read_csv(path, header=header, delimiter=delimiter)
        return df
    elif ext == ".xlsx":
        df = pd.read_excel(path, engine="openpyxl", header=header)
        return df
    elif ext == ".xls":
        df = pd.read_excel(path, engine="xlrd", header=header)
        return df
    else:
        raise Exception(ext + " file not supported for reading")


def write_file(data: pd.DataFrame, write_header=True, save_path="output.csv", delimiter=" "):# pragma: no cover
    """
    Generic function to write outputs
    Args:
        save_path: output file path
        write_header : None if no header , row number if there is a header in input data
        delimiter: delimiter character if it is a delimited file
    """
    ext = os_spt(save_path)[1]
    if ext == ".csv":
        data.to_csv(save_path, index=False, header=write_header)
    elif ext == ".txt":
        data.to_string(save_path, index=False, header=write_header)
    elif ext == ".tsv":
        data.to_csv(save_path, sep="\t")
    elif ext == ".xlsx":
        data.to_excel(save_path, index=False, header=write_header, engine="openpyxl")
    elif ext == ".xls":
        data.to_excel(save_path, index=False, header=write_header, engine="xlwt")
    else:
        raise Exception(ext + " file not supported for writing")


def inverse_mapping(f):
    """
    Function that reverses the keys and values of a dictionary. The keys are turned to lower case.
    Args:
        f: input dictionary

    Returns:
        key values swapped in the dictionary f

    """
    f = {v.lower(): k for k, v in f.items()}
    return f


def label_encode_input_data(df, purpose="Topic", input_column_name="Text", true_value_col_name="Label"):
    """
    Function that label encodes the target data
    Args:
        df: input dataframe
        purpose: The classifier that has to be label encoded
        input_column_name: Heading of the input column
        true_value_col_name: The heading of the column name that holds ground truth values

    Returns:
        input the x feature, label encoded target values, number of categories
    """
    reverse_dict = inverse_mapping(constants.KerMappingDictionary.MODEL_DICT_MAPPING[purpose])
    label_encoded_target = None
    try:
        label_encoded_target = df[true_value_col_name].str.lower().map(reverse_dict).to_list()
    except:
        print(" The label column should only have the following keys are categories ", reverse_dict.keys(),
              " Because you are running prediction on ", purpose, " Model")
        sys.exit()
    return df[input_column_name], label_encoded_target, len(reverse_dict)


def get_classification_report(y_true, y_pred, n_target):
    """
    Function to report the classification report like F score, Accuracy, Precession
    Args:
        y_true: ground truth value
        y_pred: predicted value by the model
        n_target: total number of categories in the classifier
    """
    from sklearn.metrics import classification_report

    cnf = classification_report(y_true, y_pred, labels=range(0, n_target))
    print(cnf)
    print("writing scores to  file")
    with open(constants.PathConstants.MODEL_PATH + "/classifier_report.txt", 'w') as f:
        f.write(str(cnf))


def get_confusion_matric(y_true, y_pred, n_target): # pragma: no cover
    """
    Function to give the confusion matrix of the report
    Args:
        y_true: ground truth value
        y_pred: predicted value by the model
        n_target: total number of categories in the classifier

    Returns:

    """
    from sklearn.metrics import confusion_matrix, accuracy_score

    cnf = confusion_matrix(y_true, y_pred, labels=range(0, n_target))
    acc_score = accuracy_score(y_true, y_pred)

    print(cnf)
    print(acc_score)
    print("writing scores to  file")
    with open(constants.PathConstants.MODEL_PATH + "/classifier_score.txt", 'w') as f:
        f.write(str(cnf))
        f.write("\n")
        f.write("Accuracy")
        f.write(str(acc_score))


def plot_history(history): # pragma: no cover
    """
    The function to plot the accuracy and loss
    Args:
        history: history object with loss and and accuracy values
    """
    import matplotlib.pyplot as plt
    plt.style.use('ggplot')

    acc = history.history['acc']
    val_acc = history.history['val_acc']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    x = range(1, len(acc) + 1)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(x, acc, 'b', label='Training acc')
    plt.plot(x, val_acc, 'r', label='Validation acc')
    plt.title('Training and validation accuracy')
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(x, loss, 'b', label='Training loss')
    plt.plot(x, val_loss, 'r', label='Validation loss')
    plt.title('Training and validation loss')
    plt.legend()
    plt.savefig(constants.PathConstants.MODEL_PATH + "/classifier_plot.png")


def preprocess_input(query):
    """
    # Temporary fix to handle queries with model number in them.
    # To be moved to the beginning of KER pipeline once all the modules can handle this
    Args:
        query: user query ,a string input

    Returns:
        string where model number is replaces with the word "appliance"

    """
    import re
    model_regex = r'([a-z]+\d+([a-z]\*|[a-z]|\*)\w*)'
    query = re.sub(model_regex, 'appliance', query, flags=re.IGNORECASE)
    return query


def shuffle_data(x_values, y_values):
    """
    function to randomly shuffle the dataset
    Args:
        x_values: X features
        y_values: y label

    Returns:
        randomly shuffled X and y values pairs
    """
    from sklearn.utils import shuffle
    return shuffle(x_values, y_values)
