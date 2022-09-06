import six
import os  # needed navigate the system to get the input data
import SimpleITK as sitk
import radiomics
from radiomics import featureextractor  # This module is used for interaction with pyradiomics
import pandas as pd
import win32api,win32con


def pyradiomics_extrction_batch(IT,FC,Label,Label_name,BW,image_path,mask_path,save_path):
    ImageType = IT
    FeatureClass = FC
    Label = Label
    LN = Label_name
    Binwidth = BW
    I_path = image_path
    M_path = mask_path
    save_path = save_path

    # 1.Setting up data

    number = len(os.listdir(I_path))

    # 2.Instantiating the extractor
    ## 2.1 defult
    #extractor = featureextractor.RadiomicsFeatureExtractor()
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
    # print('Extraction parameters:\n\t', extractor.settings)
    # print('Enabled filters:\n\t', extractor.enabledImagetypes)  # Still the default parameters
    # print('Enabled features:\n\t', extractor.enabledFeatures)  # Still the default parameters

    # 3.Extract features
    dataA = pd.DataFrame()
    for i in range(0,number):
        image_name = os.listdir(I_path)[i]
        mask_name = os.listdir(M_path)[i]

        img = sitk.ReadImage(os.path.join(I_path, image_name))
        mask = sitk.ReadImage(os.path.join(M_path, mask_name))

        name = image_name.replace('.nii.gz', '')
        name = name.replace('_SAX', '')

        if Label == 8:
            result = extractor.execute(img, mask)
        else:
            result = extractor.execute(img, mask, label=Label)

        feature = pd.DataFrame([result])
        name = pd.DataFrame({'name': [name]})
        feature = pd.concat([name, feature], axis=1)
        dataA = pd.concat([dataA, feature])

    dataA.to_excel(save_path + "\pyradiomics_batch_result_" + LN + ".xlsx")
    #消息弹窗
    win32api.MessageBox(0, "Feature extraction completed","Information", win32con.MB_OK)

