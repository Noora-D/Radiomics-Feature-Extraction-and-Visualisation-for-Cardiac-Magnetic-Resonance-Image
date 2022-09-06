# default brain settings
APPLICATION_TITLE = "Cardiac MRI 3D Visualizer and radiomics feature extraction Toolbox"
BRAIN_SMOOTHNESS = 500
BRAIN_OPACITY = 0.2
BRAIN_COLORS = [(1.0, 0.9, 0.9)]  # RGB percentages

# default mask settings
MASK_SMOOTHNESS = 500
MASK_COLORS = [(1, 0, 0),
                (0, 1, 0),
                (1, 1, 0),
                (0, 0, 1),
                (1, 0, 1),
                (0, 1, 1),
                (1, 0.5, 0.5),
                (0.5, 1, 0.5),
                (0.5, 0.5, 1)]  # RGB percentages
MASK_OPACITY = 1.0
LABEL_OPACITY = 1.0

# default label name
LABEL_NAME = ['LV endocardium',
              'LV myocardium',
              'Scar',
              'RV endocardium',
              'RV myocardium',
              'Papillary muscles',
              'Aorta']