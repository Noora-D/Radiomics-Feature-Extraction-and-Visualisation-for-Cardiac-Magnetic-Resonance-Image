import six
import os  # needed navigate the system to get the input data
import SimpleITK as sitk
import radiomics
from radiomics import featureextractor  # This module is used for interaction with pyradiomics
import pandas as pd
from vtkUtils import *
from config import *
import win32api,win32con


def pyradiomics_extrction(IT,FC,Label,Label_name,BW,image_path,mask_path,save_path):
    ImageType = IT
    FeatureClass = FC
    Label = Label
    LN = Label_name
    Binwidth = BW
    I_path = image_path
    M_path = mask_path
    save_path = save_path

    # 1.Setting up data
    img = sitk.ReadImage(I_path)
    mask = sitk.ReadImage(M_path)

    # 2.Instantiating the extractor
    ## 2.1 defult
    extractor = featureextractor.RadiomicsFeatureExtractor()
    ## 2.2 hard-coded settings:
    # # First define the settings
    settings = {}
    settings['binWidth'] = Binwidth
    # settings['sigma'] = [1, 2, 3]
    #
    # # Instantiate the extractor
    extractor = featureextractor.RadiomicsFeatureExtractor(**settings)  # ** 'unpacks' the dictionary in the function call

    extractor.enableImageTypeByName(ImageType)
    if FeatureClass != "all":
        extractor.disableAllFeatures()
        extractor.enableFeatureClassByName(FeatureClass)

    #
    #print('Extraction parameters:\n\t', extractor.settings)
    #print('Enabled filters:\n\t', extractor.enabledImagetypes)  # Still the default parameters
    #print('Enabled features:\n\t', extractor.enabledFeatures)  # Still the default parameters

    # 3.Extract features
    data = pd.DataFrame()
    if Label == 8:
        result = extractor.execute(img, mask)
    else:
        result = extractor.execute(img, mask,label=Label)
    #print('Extraction parameters:\n\t', extractor.settings)
    feature = pd.DataFrame([result])
    dataA = pd.concat([data, feature])
    dataA.to_excel(save_path + "\pyradiomics_result_" + LN + ".xlsx")

    #消息弹窗
    win32api.MessageBox(0, "Feature extraction completed","Information", win32con.MB_OK)

