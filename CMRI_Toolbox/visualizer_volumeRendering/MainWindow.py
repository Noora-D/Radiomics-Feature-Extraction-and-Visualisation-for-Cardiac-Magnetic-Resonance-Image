import math
import time
import os

import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkUtils import *
from config import *
from pyradiomics import *
from pyradiomics_batch import *
from pyradiomics_voxel import *




class MainWindow(QtWidgets.QMainWindow, QtWidgets.QApplication):
    def __init__(self, app):
        self.app = app
        QtWidgets.QMainWindow.__init__(self, None)

        # base setup
        self.renderer, self.frame, self.vtk_widget, self.interactor, self.render_window = self.setup()
        self.brain, self.mask = setup_brain(self.renderer, self.app.BRAIN_FILE), setup_mask(self.renderer,
                                                                                            self.app.MASK_FILE)
        # 标签数量
        self.n_labels = int(self.mask.reader.GetOutput().GetScalarRange()[1])
        #print(self.n_labels)

        # 选择体渲染和面渲染的选择框
        self.volume_rendering_cb = self.add_volume_rendering()
        self.mesh_model_cb = self.add_mesh_model()

        # setup brain projection and slicer
        self.brain_image_prop = setup_projection(self.brain, self.renderer)
        self.brain_slicer_props = setup_slicer(self.renderer, self.brain)  # causing issues with rotation
        self.slicer_widgets = []

        # brain pickers
        self.brain_threshold_sp = self.create_new_picker(self.brain.scalar_range[1], self.brain.scalar_range[0], 5.0,
                                                         sum(self.brain.scalar_range) / 2, self.brain_threshold_vc)
        self.brain_opacity_sp = self.create_new_picker(1.0, 0.0, 0.1, BRAIN_OPACITY, self.brain_opacity_vc)
        self.brain_smoothness_sp = self.create_new_picker(1000, 100, 100, BRAIN_SMOOTHNESS, self.brain_smoothness_vc)
        self.brain_lut_sp = self.create_new_picker(3.0, 0.0, 0.1, 2.0, self.lut_value_changed)
        self.brain_projection_cb = self.add_brain_projection()
        self.brain_slicer_cb = self.add_brain_slicer()

        # mask pickers
        self.mask_opacity_sp = self.create_new_picker(1.0, 0.0, 0.1, MASK_OPACITY, self.mask_opacity_vc)
        self.mask_smoothness_sp = self.create_new_picker(1000, 100, 100, MASK_SMOOTHNESS, self.mask_smoothness_vc)
        self.mask_label_cbs = []
        self.mask_label_opacity_sp = []  # !!!!label的透明度
        for i in range(0, self.n_labels):
            self.mask_label_opacity_sp.append(self.create_new_picker_1(1.0, 0.0, 0.1, LABEL_OPACITY))
        for i in range(0, self.n_labels):
            self.mask_label_cbs.append(QtWidgets.QCheckBox("Label {}".format(i + 1)))  # QCheckBox是选项按钮MASK_COLORS[i]
            self.mask_label_opacity_sp[i].valueChanged.connect(lambda _, index = i:self.mask_label_opacity_vc(index))

        # create grid for all widgets
        self.grid = QtWidgets.QGridLayout()

        # 文件选择框
        self.directory_name_1 = QtWidgets.QLineEdit()
        self.directory_name_2 = QtWidgets.QLineEdit()
        self.directory_image = QtWidgets.QLineEdit()
        self.directory_mask = QtWidgets.QLineEdit()
        self.directory_name_3 = QtWidgets.QLineEdit()

        #featureextraction_widget
        self.ImageTypes = QtWidgets.QComboBox()
        self.ImageTypes.addItems(['Original', 'Wavelet', 'LoG', 'Square', 'SqureRoot', 'Logarithm', 'Exponential', 'Gradient'])
        self.FeatureClass = QtWidgets.QComboBox()
        self.FeatureClass.addItems(['firstorder', 'shape', 'glcm', 'glrlm', 'glszm', 'gldm', 'ngtdm', 'all'])
        self.Label_1 = QtWidgets.QComboBox()
        self.Label_1.addItems(['LV endocardium', 'LV myocardium', 'Scar', 'RV endocardium', 'RV myocardium', 'Papillary muscles','Aorta','All'])
        self.binWidth = QtWidgets.QDoubleSpinBox()
        self.binWidth.setMaximum(100)  # 设置最大值
        self.binWidth.setMinimum(0)  # 设置最小值
        self.binWidth.setSingleStep(0.1)  # 设置步长
        self.binWidth.setValue(25)  # 设置数值，当设置的数值超过指定的小数位置时会四舍五入，如果设置的值超过了最大值或最小值，最终会显示最大值或最小值

        # featureexVisualisation_widget
        self.KernelRadius = QtWidgets.QDoubleSpinBox()
        self.KernelRadius.setMaximum(100)  # 设置最大值
        self.KernelRadius.setMinimum(1)  # 设置最小值
        self.KernelRadius.setSingleStep(1)  # 设置步长
        self.KernelRadius.setValue(1)  # 设置数值，当设置的数值超过指定的小数位置时会四舍五入，如果设置的值超过了最大值或最小值，最终会显示最大值或最小值
        self.maskedKernel = QtWidgets.QComboBox()
        self.maskedKernel.addItems(['True', 'False'])
        self.initValue = QtWidgets.QDoubleSpinBox()
        self.initValue.setMaximum(100)  # 设置最大值
        self.initValue.setMinimum(0)  # 设置最小值
        self.initValue.setSingleStep(0.1)  # 设置步长
        self.initValue.setValue(0)  # 设置数值，当设置的数值超过指定的小数位置时会四舍五入，如果设置的值超过了最大值或最小值，最终会显示最大值或最小值
        self.Label_2 = QtWidgets.QComboBox()
        self.Label_2.addItems(['LV endocardium', 'LV myocardium', 'Scar', 'RV endocardium', 'RV myocardium', 'Papillary muscles','Aorta'])
        self.categories = {'firstorder': ['Energy', 'TotalEnergy', 'Entropy', 'Minimum', '10Percentile', '90Percentile', 'Maximum', 'Mean', 'Median', 'InterquartileRange', 'Range', 'MeanAbsoluteDeviation', 'RobustMeanAbsoluteDeviation', 'RootMeanSquared', 'Kurtosis', 'Variance', 'Uniformity'],
                           'glcm': ['Autocorrelation', 'ClusterProminence', 'ClusterTendency', 'Contrast', 'DifferenceAverage', 'DifferenceEntropy', 'DifferenceVariance', 'JointEnergy', 'JointEntropy', 'Imc2', 'Idm', 'Idmn', 'Id', 'Idn', 'InverseVariance', 'MaximumProbability', 'SumAverage', 'SumEntropy', 'SumSquares'],
                           'glrlm': ['ShortRunEmphasis', 'LongRunEmphasis', 'GrayLevelNonUniformity', 'GrayLevelNonUniformityNormalized', 'RunLengthNonUniformity', 'RunLengthNonUniformityNormalized', 'RunPercentage', 'GrayLevelVariance', 'RunVariance', 'RunEntropy', 'LowGrayLevelRunEmphasis', 'HighGrayLevelRunEmphasis', 'ShortRunLowGrayLevelEmphasis', 'ShortRunHighGrayLevelEmphasis', 'LongRunLowGrayLevelEmphasis', 'LongRunHighGrayLevelEmphasis'],
                           'glszm': ['SmallAreaEmphasis', 'LargeAreaEmphasis', 'GrayLevelNonUniformity', 'GrayLevelNonUniformityNormalized', 'SizeZoneNonUniformity', 'SizeZoneNonUniformityNormalized', 'ZonePercentage', 'GrayLevelVariance', 'ZoneVariance', 'ZoneEntropy', 'LowGrayLevelZoneEmphasis', 'HighGrayLevelZoneEmphasis', 'SmallAreaLowGrayLevelEmphasis', 'SmallAreaHighGrayLevelEmphasis', 'LargeAreaLowGrayLevelEmphasis', 'LargeAreaHighGrayLevelEmphasis'],
                           'gldm': ['SmallDependenceEmphasis', 'LargeDependenceEmphasis', 'GrayLevelNonUniformity', 'DependenceNonUniformity', 'DependenceNonUniformityNormalized', 'GrayLevelVariance', 'DependenceVariance', 'DependenceEntropy', 'LowGrayLevelEmphasis', 'HighGrayLevelEmphasis', 'SmallDependenceLowGrayLevelEmphasis', 'SmallDependenceHighGrayLevelEmphasis', 'LargeDependenceLowGrayLevelEmphasis', 'LargeDependenceHighGrayLevelEmphasis'],
                           'ngtdm': ['Coarseness', 'Contrast', 'Busyness', 'Complexity', 'Strength']}
        self.class_combobox = QtWidgets.QComboBox()
        self.item_combobox = QtWidgets.QComboBox()
        self.class_combobox.setEditable(False)
        self.item_combobox.setEditable(False)
        self.Fileformat = QtWidgets.QComboBox()
        self.Fileformat.addItems(['nrrd','nii','nii.gz','mha','mhd'])


        # add each widget
        self.add_vtk_window_widget()
        self.add_brain_settings_widget()
        self.add_mask_settings_widget()
        self.add_views_widget()
        self.add_featureextraction_widget()
        self.add_featureVisualisation_widget()

        #  set layout and show
        self.render_window.Render()
        self.setWindowTitle(APPLICATION_TITLE)
        self.frame.setLayout(self.grid)
        self.setCentralWidget(self.frame)
        self.set_axial_view()
        self.interactor.Initialize()
        self.show()

    @staticmethod
    def setup():
        """
        Create and setup the base vtk and Qt objects for the application
        """
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(200/255, 200/255, 200/255)
        renderer.SetBackground2(0, 0, 0)
        renderer.SetGradientBackground(1)
        frame = QtWidgets.QFrame()
        vtk_widget = QVTKRenderWindowInteractor()
        interactor = vtk_widget.GetRenderWindow().GetInteractor()
        render_window = vtk_widget.GetRenderWindow()

        frame.setAutoFillBackground(True)
        vtk_widget.GetRenderWindow().AddRenderer(renderer)
        render_window.AddRenderer(renderer)
        interactor.SetRenderWindow(render_window)
        interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

        # required to enable overlapping actors with opacity < 1.0
        # this is causing some issues with flashing objects
        # render_window.SetAlphaBitPlanes(1)
        # render_window.SetMultiSamples(0)
        # renderer.UseDepthPeelingOn()
        # renderer.SetMaximumNumberOfPeels(2)

        return renderer, frame, vtk_widget, interactor, render_window

    def lut_value_changed(self):
        lut = self.brain.image_mapper.GetLookupTable()
        new_lut_value = self.brain_lut_sp.value()
        lut.SetValueRange(0.0, new_lut_value)
        lut.Build()
        self.brain.image_mapper.SetLookupTable(lut)
        self.brain.image_mapper.Update()
        self.render_window.Render()

    def add_brain_slicer(self):
        slicer_cb = QtWidgets.QCheckBox("Slicer")
        slicer_cb.clicked.connect(self.brain_slicer_vc)
        return slicer_cb

    def add_vtk_window_widget(self):
        base_brain_file = os.path.basename(self.app.BRAIN_FILE)
        base_mask_file = os.path.basename(self.app.MASK_FILE)
        object_title = "Cardiac Image: {0}           Mask: {1}".format(base_brain_file,base_mask_file)
        object_group_box = QtWidgets.QGroupBox(object_title)
        object_layout = QtWidgets.QVBoxLayout()
        object_layout.addWidget(self.vtk_widget)
        object_group_box.setLayout(object_layout)
        self.grid.addWidget(object_group_box, 0, 2, 5, 5)
        # must manually set column width for vtk_widget to maintain height:width ratio
        self.grid.setColumnMinimumWidth(2, 700)

    def add_brain_settings_widget(self):
        brain_group_box = QtWidgets.QGroupBox("Image Settings")
        brain_group_layout = QtWidgets.QGridLayout()
        #brain_group_layout.addWidget(QtWidgets.QLabel("Image Threshold \n(min: {0:.2f},max: {1:.2f})".format(self.brain.scalar_range[0],self.brain.scalar_range[1])), 0, 0)
        #brain_group_layout.addWidget(QtWidgets.QLabel("Image Opacity\n(min:0,max:1)"), 1, 0)
        #brain_group_layout.addWidget(QtWidgets.QLabel("Image Smoothness\n(min:100,max:1000)"), 2, 0)
        #brain_group_layout.addWidget(QtWidgets.QLabel("Image Intensity"), 3, 0)
        #brain_group_layout.addWidget(self.brain_threshold_sp, 0, 1, 1, 2)
        #brain_group_layout.addWidget(self.brain_opacity_sp, 1, 1, 1, 2)
        #brain_group_layout.addWidget(self.brain_smoothness_sp, 2, 1, 1, 2)
        #brain_group_layout.addWidget(self.brain_lut_sp, 3, 1, 1, 2)
        brain_group_layout.addWidget(QtWidgets.QLabel("Rendering Setting"), 0, 0)
        brain_group_layout.addWidget(self.volume_rendering_cb, 1, 0)
        brain_group_layout.addWidget(self.mesh_model_cb, 1, 1)
        brain_group_layout.addWidget(self.create_new_separator(), 2, 0, 1, 3)
        brain_group_layout.addWidget(self.brain_projection_cb, 3, 0)
        brain_group_layout.addWidget(self.brain_slicer_cb, 3, 1)
        brain_group_layout.addWidget(self.create_new_separator(), 4, 0, 1, 3)
        brain_group_layout.addWidget(QtWidgets.QLabel("Axial Slice"), 5, 0)
        brain_group_layout.addWidget(QtWidgets.QLabel("Coronal Slice"), 6, 0)
        brain_group_layout.addWidget(QtWidgets.QLabel("Sagittal Slice"), 7, 0)

        # order is important
        slicer_funcs = [self.axial_slice_changed, self.coronal_slice_changed, self.sagittal_slice_changed]
        current_label_row = 5
        # data extent is array [xmin, xmax, ymin, ymax, zmin, zmax)
        # we want all the max values for the range
        extent_index = 5
        for func in slicer_funcs:
            slice_widget = QtWidgets.QSlider(Qt.Qt.Horizontal)
            slice_widget.setDisabled(True)
            self.slicer_widgets.append(slice_widget)
            brain_group_layout.addWidget(slice_widget, current_label_row, 1, 1, 2)
            slice_widget.valueChanged.connect(func)
            slice_widget.setRange(self.brain.extent[extent_index - 1], self.brain.extent[extent_index])
            slice_widget.setValue(self.brain.extent[extent_index] / 2)
            current_label_row += 1
            extent_index -= 2

        brain_group_box.setLayout(brain_group_layout)
        self.grid.addWidget(brain_group_box, 0, 0, 1, 2)

    def axial_slice_changed(self):
        pos = self.slicer_widgets[0].value()
        self.brain_slicer_props[0].SetDisplayExtent(self.brain.extent[0], self.brain.extent[1], self.brain.extent[2],
                                                    self.brain.extent[3], pos, pos)
        self.render_window.Render()

    def coronal_slice_changed(self):
        pos = self.slicer_widgets[1].value()
        self.brain_slicer_props[1].SetDisplayExtent(self.brain.extent[0], self.brain.extent[1], pos, pos,
                                                    self.brain.extent[4], self.brain.extent[5])
        self.render_window.Render()

    def sagittal_slice_changed(self):
        pos = self.slicer_widgets[2].value()
        self.brain_slicer_props[2].SetDisplayExtent(pos, pos, self.brain.extent[2], self.brain.extent[3],
                                                    self.brain.extent[4], self.brain.extent[5])
        self.render_window.Render()

    def add_mask_settings_widget(self):
        mask_settings_group_box = QtWidgets.QGroupBox("Mask Settings")
        mask_settings_layout = QtWidgets.QGridLayout()
        mask_settings_layout.addWidget(QtWidgets.QLabel("Mask Opacity\n(min:0,max:1)"), 0, 0)
        mask_settings_layout.addWidget(QtWidgets.QLabel("Mask Smoothness\n(min:100,max:1000)"), 1, 0)
        mask_settings_layout.addWidget(self.mask_opacity_sp, 0, 1)
        mask_settings_layout.addWidget(self.mask_smoothness_sp, 1, 1)
        mask_multi_color_radio = QtWidgets.QRadioButton("Multi Color")
        mask_multi_color_radio.setChecked(True)
        mask_multi_color_radio.clicked.connect(self.mask_multi_color_radio_checked)
        mask_single_color_radio = QtWidgets.QRadioButton("Single Color")
        mask_single_color_radio.clicked.connect(self.mask_single_color_radio_checked)
        mask_settings_layout.addWidget(mask_multi_color_radio, 2, 0)
        mask_settings_layout.addWidget(mask_single_color_radio, 2, 1)
        mask_settings_layout.addWidget(self.create_new_separator(), 3, 0, 1, 2)
        mask_settings_layout.addWidget(QtWidgets.QLabel("Label"), 4, 0)
        mask_settings_layout.addWidget(QtWidgets.QLabel("Label Opacity\n(min:0,max:1)"), 4, 1)


        c_col, c_row = 0, 5  # c_row must always be (+1) of last row
        for i in range(1, self.n_labels+1):
            #self.mask_label_cbs.append(QtWidgets.QCheckBox("{}".format(LABEL_NAME[i-1])))
            #self.mask_label_cbs.append(QtWidgets.QCheckBox("Label {}".format(i)))
            mask_settings_layout.addWidget(self.mask_label_cbs[i - 1], c_row, c_col)
            c_row = c_row + 1 if c_col == 1 else c_row
            c_col = 0 if c_col == 1 else 1
            mask_settings_layout.addWidget(self.mask_label_opacity_sp[i - 1], c_row, c_col)
            c_row = c_row + 1 if c_col == 1 else c_row
            c_col = 0 if c_col == 1 else 1

        mask_settings_group_box.setLayout(mask_settings_layout)
        self.grid.addWidget(mask_settings_group_box, 1, 0, 2, 2)

        for i, cb in enumerate(self.mask_label_cbs):
            if i < len(self.mask.labels) and self.mask.labels[i].actor:
                cb.setChecked(True)
                cb.clicked.connect(self.mask_label_checked)
            else:
                cb.setDisabled(True)

    def add_views_widget(self):
        axial_view = QtWidgets.QPushButton("Axial")
        coronal_view = QtWidgets.QPushButton("Coronal")
        sagittal_view = QtWidgets.QPushButton("Sagittal")
        views_box = QtWidgets.QGroupBox("Views")
        views_box_layout = QtWidgets.QVBoxLayout()
        views_box_layout.addWidget(axial_view)
        views_box_layout.addWidget(coronal_view)
        views_box_layout.addWidget(sagittal_view)
        views_box.setLayout(views_box_layout)
        self.grid.addWidget(views_box, 3, 0, 2, 2)
        axial_view.clicked.connect(self.set_axial_view)
        coronal_view.clicked.connect(self.set_coronal_view)
        sagittal_view.clicked.connect(self.set_sagittal_view)
        
    def add_featureextraction_widget(self):
        featureextraction_group_box = QtWidgets.QGroupBox("Radiomics Feature Extraction")
        featureextraction_layout = QtWidgets.QGridLayout()  # QGridlayout以方格的形式管理窗口部件

        featureextraction_layout.addWidget(QtWidgets.QLabel("Image Types"), 0, 0)
        featureextraction_layout.addWidget(self.ImageTypes, 0, 1)

        featureextraction_layout.addWidget(QtWidgets.QLabel("Feature class"), 1, 0)
        featureextraction_layout.addWidget(self.FeatureClass,1,1)

        featureextraction_layout.addWidget(QtWidgets.QLabel("Label"), 2, 0)
        featureextraction_layout.addWidget(self.Label_1, 2, 1)

        featureextraction_layout.addWidget(QtWidgets.QLabel("binWidth"), 3, 0)
        featureextraction_layout.addWidget(self.binWidth, 3, 1)

        featureextraction_layout.addWidget(QtWidgets.QLabel("Exporting files to"), 4, 0)
        #filename_line = QtWidgets.QLineEdit()
        button_file = QtWidgets.QPushButton("Choose")
        button_file.clicked.connect(self.filename)
        featureextraction_layout.addWidget(self.directory_name_1, 4, 1)
        featureextraction_layout.addWidget(button_file, 4, 2)
        button_export = QtWidgets.QPushButton("Export")
        button_export.clicked.connect(self.ExportFeature)
        featureextraction_layout.addWidget(button_export, 5, 2)

        # 批量提取部分
        #featureextraction_layout.addWidget(self.create_new_separator(), 6, 0, 1, 2)
        title = QtWidgets.QLabel("Batch Extraction")
        featureextraction_layout.addWidget(title, 6, 0)
        title.setFixedHeight(15)
        featureextraction_layout.addWidget(QtWidgets.QLabel("Image Folder:"), 7, 0)
        image_buttom = QtWidgets.QPushButton("Choose")
        image_buttom.clicked.connect(self.imageFolder)
        featureextraction_layout.addWidget(self.directory_image, 7, 1)
        featureextraction_layout.addWidget(image_buttom, 7, 2)
        featureextraction_layout.addWidget(QtWidgets.QLabel("Mask Folder:"), 8, 0)
        mask_buttom = QtWidgets.QPushButton("Choose")
        mask_buttom.clicked.connect(self.maskFolder)
        featureextraction_layout.addWidget(self.directory_mask, 8, 1)
        featureextraction_layout.addWidget(mask_buttom, 8, 2)
        featureextraction_layout.addWidget(QtWidgets.QLabel("Exporting files to"), 9, 0)
        button_file_batch = QtWidgets.QPushButton("Choose")
        button_file_batch.clicked.connect(self.filename_2)
        featureextraction_layout.addWidget(self.directory_name_2, 9, 1)
        featureextraction_layout.addWidget(button_file_batch, 9, 2)
        button_batch_export = QtWidgets.QPushButton("Export")
        button_batch_export.clicked.connect(self.ExportFeature_batch)
        featureextraction_layout.addWidget(button_batch_export, 10, 2)

        featureextraction_group_box.setLayout(featureextraction_layout)  # 设置布局
        self.grid.addWidget(featureextraction_group_box, 0, 7, 2, 2)  # 添加一个QWidget到布局

    def ExportFeature(self):
        self.process_changes()
        IT = self.ImageTypes.currentText()
        FC = self.FeatureClass.currentText()
        Label = self.Label_1.currentIndex()
        Label = int(Label)+1
        Label_name = self.Label_1.currentText()
        BW = self.binWidth.value()
        path = self.directory_name_1.text()
        pyradiomics_extrction(IT, FC, Label, Label_name, BW, self.app.BRAIN_FILE, self.app.MASK_FILE, path)

    def ExportFeature_batch(self):
        self.process_changes()
        IT = self.ImageTypes.currentText()
        FC = self.FeatureClass.currentText()
        Label = self.Label_1.currentIndex()
        Label = int(Label) + 1
        Label_name = self.Label_1.currentText()
        BW = self.binWidth.value()
        image_path = self.directory_image.text()
        mask_path = self.directory_mask.text()
        save_path = self.directory_name_2.text()
        pyradiomics_extrction_batch(IT, FC, Label, Label_name, BW, image_path, mask_path, save_path)

    def add_featureVisualisation_widget(self):
        featureVisualisation_group_box = QtWidgets.QGroupBox("Radiomics Feature Visualisation")
        featureVisualisation_layout = QtWidgets.QGridLayout()  # QGridlayout以方格的形式管理窗口部件

        featureVisualisation_layout.addWidget(QtWidgets.QLabel("kernelRadius"), 0, 0)
        featureVisualisation_layout.addWidget(self.KernelRadius, 0, 1)

        featureVisualisation_layout.addWidget(QtWidgets.QLabel("maskedKernel"), 1, 0)
        featureVisualisation_layout.addWidget(self.maskedKernel, 1, 1)

        featureVisualisation_layout.addWidget(QtWidgets.QLabel("initValue"), 2, 0)
        featureVisualisation_layout.addWidget(self.initValue, 2, 1)

        featureVisualisation_layout.addWidget(QtWidgets.QLabel("Label"), 3, 0)
        featureVisualisation_layout.addWidget(self.Label_2, 3, 1)

        featureVisualisation_layout.addWidget(QtWidgets.QLabel("Feature Class"), 4, 0)
        self.class_combobox.currentTextChanged.connect(self.set_category)
        self.class_combobox.addItems(sorted(self.categories.keys()))
        featureVisualisation_layout.addWidget(self.class_combobox,4, 1)
        featureVisualisation_layout.addWidget(self.item_combobox, 4, 2)

        featureVisualisation_layout.addWidget(QtWidgets.QLabel("File Format"), 5, 0)
        featureVisualisation_layout.addWidget(self.Fileformat, 5, 1)

        featureVisualisation_layout.addWidget(QtWidgets.QLabel("Exporting files to"), 6, 0)
        #filename_line = QtWidgets.QLineEdit()
        button_file = QtWidgets.QPushButton("Choose")
        button_file.clicked.connect(self.filename_3)
        featureVisualisation_layout.addWidget(self.directory_name_3, 6, 1)
        featureVisualisation_layout.addWidget(button_file, 6, 2)
        button_export = QtWidgets.QPushButton("Visualisation")
        button_export.clicked.connect(self.Visualisation_feature)
        featureVisualisation_layout.addWidget(button_export, 7, 2)

        featureVisualisation_group_box.setLayout(featureVisualisation_layout)  # 设置布局
        self.grid.addWidget(featureVisualisation_group_box, 2, 7, 5, 2)  # 添加一个QWidget到布局

    def Visualisation_feature(self):
        self.process_changes()
        kR = int(self.KernelRadius.value())
        mK = self.maskedKernel.currentText()
        iV = self.initValue.value()
        Label = self.Label_2.currentIndex()
        Label = int(Label) + 1
        Label_name = self.Label_2.currentText()
        C1 = self.class_combobox.currentIndex()
        C2 = self.item_combobox.currentText()
        format = self.Fileformat.currentText()
        save_path = self.directory_name_3.text()
        pyradiomics_extrction_voxel(kR,mK,iV,Label,Label_name,C1,C2,format,self.app.BRAIN_FILE, self.app.MASK_FILE, save_path)

    def set_category(self, text):
        self.item_combobox.clear()
        self.item_combobox.addItems(self.categories.get(text, []))

    def filename(self):
        file_name = QtWidgets.QFileDialog.getExistingDirectory(self,'open file', '')
        self.directory_name_1.setText(file_name)

    def filename_2(self):
        file_name = QtWidgets.QFileDialog.getExistingDirectory(self,'open file', '')
        self.directory_name_2.setText(file_name)

    def filename_3(self):
        file_name = QtWidgets.QFileDialog.getExistingDirectory(self,'open file', '')
        self.directory_name_3.setText(file_name)

    def imageFolder(self):
        file_name = QtWidgets.QFileDialog.getExistingDirectory(self, 'open file', '')
        self.directory_image.setText(file_name)

    def maskFolder(self):
        file_name = QtWidgets.QFileDialog.getExistingDirectory(self, 'open file', '')
        self.directory_mask.setText(file_name)

    @staticmethod
    def create_new_picker(max_value, min_value, step, picker_value, value_changed_func):
        if isinstance(max_value, int):
            picker = QtWidgets.QSpinBox()
        else:
            picker = QtWidgets.QDoubleSpinBox()

        picker.setMaximum(max_value)
        picker.setMinimum(min_value)
        picker.setSingleStep(step)
        picker.setValue(picker_value)
        picker.valueChanged.connect(value_changed_func)
        return picker

    def create_new_picker_1(self,max_value, min_value, step, picker_value):  # 创建新的勾选框
        if isinstance(max_value, int):  # 检查max_value是否为整数
            picker = QtWidgets.QSpinBox()  # 使用QSpinBox()构造计数器
        else:
            picker = QtWidgets.QDoubleSpinBox()  # 与QSpinBox()用法一致，构造计数器

        picker.setMaximum(max_value)  # 设置最大值
        picker.setMinimum(min_value)  # 设置最小值
        picker.setSingleStep(step)  # 设置步长
        picker.setValue(picker_value)  # 设置数值，当设置的数值超过指定的小数位置时会四舍五入，如果设置的值超过了最大值或最小值，最终会显示最大值或最小值
        # picker.valueChanged.connect(value_changed_func)    #值变化时的操作
        return picker

    def add_volume_rendering(self):
        volume_rendering_cb = QtWidgets.QCheckBox("volume_rendering")
        volume_rendering_cb.setChecked(True)
        volume_rendering_cb.clicked.connect(self.volume_rendering_vc)
        return volume_rendering_cb

    def volume_rendering_vc(self):

        if self.volume_rendering_cb.isChecked():  #如果被选中
            volume = self.brain.volume
            volume.SetProperty(self.brain.volumeProperty)
        elif self.volume_rendering_cb.isEnabled():
            volume = self.brain.volume
            volumeProperty = vtk.vtkVolumeProperty()
            opacityTransferFunction = vtk.vtkPiecewiseFunction()
            opacityTransferFunction.AddPoint(255.0, 0)
            volumeProperty.SetScalarOpacity(opacityTransferFunction)
            volume.SetProperty(volumeProperty)
        self.render_window.Render()    #重新渲染渲染窗口

    def add_mesh_model(self):
        mesh_model_cb = QtWidgets.QCheckBox("mesh_model")
        mesh_model_cb.setChecked(True)
        mesh_model_cb.clicked.connect(self.mesh_model_vc)
        return mesh_model_cb

    def mesh_model_vc(self):
        if self.mesh_model_cb.isChecked():  # 如果被选中
            for label in self.mask.labels:
                label.property.SetOpacity(self.mask_opacity_sp.value())  # 先获取当前设置的mask的透明度，再将该label的透明度设置为当前值
        elif self.mesh_model_cb.isEnabled():  # 未被选中
            for label in self.mask.labels:
                label.property.SetOpacity(0)  # 未选中的设置透明度为0
        self.render_window.Render()  # 重新渲染渲染窗口

    def add_brain_projection(self):
        projection_cb = QtWidgets.QCheckBox("Projection")
        projection_cb.clicked.connect(self.brain_projection_vc)
        return projection_cb

    def mask_label_checked(self):
        for i, cb in enumerate(self.mask_label_cbs):
            if cb.isChecked():
                self.mask.labels[i].property.SetOpacity(self.mask_opacity_sp.value())
            elif cb.isEnabled():  # labels without data are disabled
                self.mask.labels[i].property.SetOpacity(0)
        self.render_window.Render()

    def mask_single_color_radio_checked(self):
        for label in self.mask.labels:
            if label.property:
                label.property.SetColor(MASK_COLORS[0])
        self.render_window.Render()

    def mask_multi_color_radio_checked(self):
        for label in self.mask.labels:
            if label.property:
                label.property.SetColor(label.color)
        self.render_window.Render()

    def brain_projection_vc(self):
        projection_checked = self.brain_projection_cb.isChecked()
        self.brain_slicer_cb.setDisabled(projection_checked)  # disable slicer checkbox, cant use both at same time
        self.brain_image_prop.SetOpacity(projection_checked)
        self.render_window.Render()

    def brain_slicer_vc(self):
        slicer_checked = self.brain_slicer_cb.isChecked()

        for widget in self.slicer_widgets:
            widget.setEnabled(slicer_checked)

        self.brain_projection_cb.setDisabled(slicer_checked)  # disable projection checkbox, cant use both at same time
        for prop in self.brain_slicer_props:
            prop.GetProperty().SetOpacity(slicer_checked)
        self.render_window.Render()

    def brain_opacity_vc(self):
        opacity = round(self.brain_opacity_sp.value(), 2)
        self.brain.labels[0].property.SetOpacity(opacity)
        self.render_window.Render()

    def brain_threshold_vc(self):
        self.process_changes()
        threshold = self.brain_threshold_sp.value()
        self.brain.labels[0].extractor.SetValue(0, threshold)
        self.render_window.Render()

    def brain_smoothness_vc(self):
        self.process_changes()
        smoothness = self.brain_smoothness_sp.value()
        self.brain.labels[0].smoother.SetNumberOfIterations(smoothness)
        self.render_window.Render()

    def mask_opacity_vc(self):
        opacity = round(self.mask_opacity_sp.value(), 2)
        for i, label in enumerate(self.mask.labels):
            if label.property and self.mask_label_cbs[i].isChecked():
                label.property.SetOpacity(opacity)
        self.render_window.Render()

    def mask_label_opacity_vc(self, index):  # mask_opacity该勾选框值变化时的操作
        opacity = round(self.mask_label_opacity_sp[index].value(), 2)  # 获取当前勾选框的值，并保留两位小数
        if self.mask.labels[index].property and self.mask_label_cbs[index].isChecked():  # 检查该label有没有被选上
            self.mask.labels[index].property.SetOpacity(opacity)  # 将新的opacity传入
        self.render_window.Render()  # 重新渲染渲染窗口

    def mask_smoothness_vc(self):
        self.process_changes()
        smoothness = self.mask_smoothness_sp.value()
        for label in self.mask.labels:
            if label.smoother:
                label.smoother.SetNumberOfIterations(smoothness)
        self.render_window.Render()

    def set_axial_view(self):
        self.renderer.ResetCamera()
        fp = self.renderer.GetActiveCamera().GetFocalPoint()
        p = self.renderer.GetActiveCamera().GetPosition()
        dist = math.sqrt((p[0] - fp[0]) ** 2 + (p[1] - fp[1]) ** 2 + (p[2] - fp[2]) ** 2)
        self.renderer.GetActiveCamera().SetPosition(fp[0], fp[1], fp[2] + dist)
        self.renderer.GetActiveCamera().SetViewUp(0.0, 1.0, 0.0)
        #self.renderer.GetActiveCamera().Zoom(1.8)
        self.render_window.Render()

    def set_coronal_view(self):
        self.renderer.ResetCamera()
        fp = self.renderer.GetActiveCamera().GetFocalPoint()
        p = self.renderer.GetActiveCamera().GetPosition()
        dist = math.sqrt((p[0] - fp[0]) ** 2 + (p[1] - fp[1]) ** 2 + (p[2] - fp[2]) ** 2)
        self.renderer.GetActiveCamera().SetPosition(fp[0], fp[2] - dist, fp[1])
        self.renderer.GetActiveCamera().SetViewUp(0.0, 0.5, 0.5)
        #self.renderer.GetActiveCamera().Zoom(1.8)
        self.render_window.Render()

    def set_sagittal_view(self):
        self.renderer.ResetCamera()
        fp = self.renderer.GetActiveCamera().GetFocalPoint()
        p = self.renderer.GetActiveCamera().GetPosition()
        dist = math.sqrt((p[0] - fp[0]) ** 2 + (p[1] - fp[1]) ** 2 + (p[2] - fp[2]) ** 2)
        self.renderer.GetActiveCamera().SetPosition(fp[2] + dist, fp[0], fp[1])
        self.renderer.GetActiveCamera().SetViewUp(0.0, 0.0, 1.0)
        #self.renderer.GetActiveCamera().Zoom(1.6)
        self.render_window.Render()

    @staticmethod
    def create_new_separator():
        horizontal_line = QtWidgets.QWidget()
        horizontal_line.setFixedHeight(1)
        horizontal_line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        horizontal_line.setStyleSheet("background-color: #c8c8c8;")
        return horizontal_line

    def process_changes(self):
        for _ in range(10):
            self.app.processEvents()
            time.sleep(0.1)
