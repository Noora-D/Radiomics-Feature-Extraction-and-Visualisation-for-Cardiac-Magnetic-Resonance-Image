import six
import os  # needed navigate the system to get the input data
import SimpleITK as sitk
import radiomics
from radiomics import featureextractor  # This module is used for interaction with pyradiomics
import pandas as pd
import win32api,win32con
from feature_visualisation import *

def pyradiomics_extrction_voxel(kR,mK,iV,Label,Label_name,C1,C2,format,image_path,mask_path,save_path):
    KernelRadius = kR
    maskedKernel = mK
    initValue = iV
    Label = Label
    LN = Label_name
    feature_1 = C1
    feature_2 = C2
    file_format = format
    #print(KernelRadius,maskedKernel,initValue,Label,feature_1,feature_2)
    I_path = image_path
    M_path = mask_path
    #save_path = save_path
    # 1.Setting up data
    img = sitk.ReadImage(I_path)
    mask = sitk.ReadImage(M_path)
    S_path = save_path
    # 2.Instantiating the extractor

    # 2.1 defult
    # extractor = featureextractor.RadiomicsFeatureExtractor()
    # print('Extraction parameters:\n\t', extractor.settings)
    # print('Enabled filters:\n\t', extractor.enabledImagetypes)
    # print('Enabled features:\n\t', extractor.enabledFeatures)

    # 2.2 hard-coded settings:
    # First define the settings
    settings = {}
    # Voxel-based specific settings
    settings['kernelRadius'] = KernelRadius  # defult value is 1,integer, specifies the size of the kernel to use as the radius from the center voxel.
    settings['maskedKernel'] = maskedKernel #defult value is True,boolean, specifies whether to mask the kernel with the overall mask.
    settings['initValue'] = initValue #float, value to use for voxels outside the ROI, or voxels where calculation failed. If set to nan, 3D slicer will treat them as transparent voxels
    settings['voxelBatch'] = 1000  # integer > 0, this value controls the maximum number of voxels that are calculated in one batch.only by not providing it is the default value of -1 used (which means: all voxels in 1 batch).

    # Instantiate the extractor
    extractor = featureextractor.RadiomicsFeatureExtractor(**settings)  # ** 'unpacks' the dictionary in the function call
    extractor.disableAllFeatures()
    if feature_1 == 0:
        extractor.enableFeaturesByName(firstorder=[feature_2])
    elif feature_1 == 1:
        extractor.enableFeaturesByName(glcm=[feature_2])
    elif feature_1 == 2:
        extractor.enableFeaturesByName(gldm=[feature_2])
    elif feature_1 == 3:
        extractor.enableFeaturesByName(glrlm=[feature_2])
    elif feature_1 == 4:
        extractor.enableFeaturesByName(glszm=[feature_2])
    elif feature_1 == 5:
        extractor.enableFeaturesByName(ngtdm=[feature_2])

    # print('Extraction parameters:\n\t', extractor.settings)
    # print('Enabled filters:\n\t', extractor.enabledImagetypes)  # Still the default parameters
    # print('Enabled features:\n\t', extractor.enabledFeatures)  # Still the default parameters

    # 3.Extract features
    # voxel-based

    result = extractor.execute(img, mask, voxelBased=True, label=Label)

    for key, val in six.iteritems(result):
        if isinstance(val, sitk.Image):  # Feature map
            sitk.WriteImage(val, S_path + '\\' + key + '_' + LN + '.' + file_format, True)
            #sitk.WriteImage(val, S_path +'\\' + key + '_' + LN + '.nrrd', True)

    win32api.MessageBox(0, "Feature extraction completed","Information", win32con.MB_OK)

    featuremap_path = S_path +'\\' + key + '_' + LN + '.' + file_format
    featuremap_path = featuremap_path.replace('/', '\\')
    print(featuremap_path)
    visualisation(featuremap_path)

