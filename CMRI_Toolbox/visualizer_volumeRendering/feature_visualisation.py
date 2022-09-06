import vtkmodules.all as vtk
from vtkmodules.util.vtkImageImportFromArray import *
#from vtk.util.vtkImageImportFromArray import *
#import vtk
import SimpleITK as sitk
import numpy as np


def visualisation(filepath):
    path = filepath
    ds = sitk.ReadImage(filepath)  # 读取nii数据的第一个函数sitk.ReadImage
    spacing = ds.GetSpacing()  # 三维数据的间隔
    origin = ds.GetOrigin()

    data = sitk.GetArrayFromImage(ds)  # 把itk.image转为array

    img_arr = vtkImageImportFromArray()  # 创建一个空的vtk类-----vtkImageImportFromArray
    img_arr.SetArray(data)  # 把array_data塞到vtkImageImportFromArray（array_data）
    img_arr.SetDataSpacing(spacing)  # 设置spacing
    img_arr.SetDataOrigin(origin)  # 设置vtk数据的坐标系原点
    img_arr.Update()

    srange = [np.min(data), np.max(data)]
    min = srange[0]
    max = srange[1]
    diff = max - min
    inter = 4096 / diff
    shift = -min

    shifter = vtk.vtkImageShiftScale()  # 对偏移和比例参数来对图像数据进行操作 数据转换，之后直接调用shifter
    shifter.SetShift(shift)
    shifter.SetScale(inter)
    shifter.SetOutputScalarTypeToUnsignedShort()
    shifter.SetInputData(img_arr.GetOutput())
    shifter.ReleaseDataFlagOff()
    shifter.Update()

    volumeMapper = vtk.vtkGPUVolumeRayCastMapper()  # 映射器volumnMapper使用vtk的管线投影算法
    volumeMapper.SetInputData(shifter.GetOutput())

    volumeProperty = vtk.vtkVolumeProperty()  # 创建vtk属性存放器,向属性存放器中存放颜色和透明度
    volumeProperty.SetInterpolationTypeToLinear()  # 设置体绘制的属性设置，决定体绘制的渲染效果
    volumeProperty.ShadeOn()  # 打开或者关闭阴影
    volumeProperty.SetAmbient(0.4)  # 设置环境光系数
    volumeProperty.SetDiffuse(0.6)  # 漫反射，设置散射光系数
    volumeProperty.SetSpecular(0.2)  # 镜面反射，设置反射光系数

    # 设置梯度不透明属性
    tfun = vtk.vtkPiecewiseFunction()  # 不透明度传输函数---放在tfun
    tfun.AddPoint(1129, 0)
    tfun.AddPoint(1300.0, 0.7)
    tfun.AddPoint(1600.0, 0.75)
    tfun.AddPoint(2000.0, 0.8)
    tfun.AddPoint(2200.0, 0.85)
    tfun.AddPoint(2500.0, 0.9)
    tfun.AddPoint(2800.0, 0.95)
    tfun.AddPoint(3000.0, 1)  # 0.18
    # tfun.AddPoint(70,0)
    # tfun.AddPoint(90,0.4)
    # tfun.AddPoint(180,0.6)
    volumeProperty.SetScalarOpacity(tfun)

    # volumeGradientOpacity = vtk.vtkPiecewiseFunction()
    # volumeGradientOpacity.AddPoint(10, 0.0)
    # volumeGradientOpacity.AddPoint(90, 0.5)
    # volumeGradientOpacity.AddPoint(100, 1.0)
    # volumeProperty.SetGradientOpacity(volumeGradientOpacity)

    # print(img_arr.GetOutput().GetPointData().GetScalars().GetRange()[0])
    # print(img_arr.GetOutput().GetPointData().GetScalars().GetRange()[1])
    # print(img_arr.GetOutput().GetPointData().GetScalars().GetRange())
    # print(shifter.GetScale())

    color = vtk.vtkColorTransferFunction()
    color.AddRGBPoint(300, 160 / 255, 32 / 255, 240 / 255)
    color.AddRGBPoint(600.0, 25 / 255, 25 / 255, 122 / 255)
    color.AddRGBPoint(1280.0, 0, 0, 1)
    color.AddRGBPoint(1680.0, 0, 1, 1)
    color.AddRGBPoint(1960.0, 0, 1, 0)
    color.AddRGBPoint(2200.0, 1, 1, 0)
    color.AddRGBPoint(2500.0, 1, 0.6, 0)
    color.AddRGBPoint(3024.0, 1, 0, 0)

    # color.AddRGBPoint(0.0, 0, 0, 1)
    # color.AddRGBPoint(432, 0.1, 0.5, 1)
    # color.AddRGBPoint(864, 0, 1, 1)
    # color.AddRGBPoint(1296, 0.6, 0.98, 0.6)
    # color.AddRGBPoint(1728, 0.19, 0.8,0.19)
    # color.AddRGBPoint(2160, 1, 1,0)
    # color.AddRGBPoint(2592, 1, 0.6, 0)
    # color.AddRGBPoint(3024, 1, 0, 0)

    # color.AddRGBPoint(0.0, 0.5, 0.0, 0.0)
    # color.AddRGBPoint(600.0, 1.0, 255, 0.5)
    # color.AddRGBPoint(1280.0, 0.9, 0.2, 255)
    # color.AddRGBPoint(1960.0, 255, 0.27, 0.1)
    # color.AddRGBPoint(2200.0, 0.9, 0.2, 0.3)
    # color.AddRGBPoint(2500.0, 1, 0.5, 0.5)
    # color.AddRGBPoint(3024.0, 0.5, 0.5, 0.5)

    # color.AddRGBPoint(0.0, 0, 0, 1)
    # color.AddRGBPoint(1, 0, 1, 0)
    # color.AddRGBPoint(2, 1, 1.0, 0)
    # color.AddRGBPoint(3, 1, 0.6, 0)
    # color.AddRGBPoint(4, 1, 0, 0)
    volumeProperty.SetColor(color)

    volume = vtk.vtkVolume()  # 和vtkActor作用一致
    volume.SetMapper(volumeMapper)
    volume.SetProperty(volumeProperty)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1, 1, 1)
    renderer.AddVolume(volume)

    scalarRange = img_arr.GetOutput().GetPointData().GetScalars().GetRange()
    lut = vtk.vtkLookupTable()
    lut.SetHueRange(0.7,0)
    lut.SetAlphaRange(1.0, 1.0)
    lut.SetValueRange(1, 1)
    lut.SetSaturationRange(1, 1)
    lut.SetRange(scalarRange)
    lut.Build()

    scalarBar = vtk.vtkScalarBarActor()  # 设置color_bar
    scalarBar.SetLookupTable(lut)
    scalarBar.SetTitle("feature")
    scalarBar.SetNumberOfLabels(5)  # 设置要显示的刻度标签数。自己设定色带的位置
    scalarBar.SetMaximumNumberOfColors(10)
    scalarBar.GetLabelTextProperty().SetColor(0, 0, 0)
    scalarBar.GetTitleTextProperty().SetColor(0, 0, 0)
    scalarBar.SetWidth(0.1)
    scalarBar.SetHeight(0.3)
    renderer.AddActor2D(scalarBar)

    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetSize(600, 600)
    renderWindow.Render()
    renderWindow.SetWindowName('VolumeRenderingApp')

    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)
    renderWindowInteractor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
    renderWindowInteractor.Initialize()
    renderWindowInteractor.Start()



