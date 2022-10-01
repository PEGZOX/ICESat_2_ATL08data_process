import h5py  # 导入工具包
import os
import openpyxl
import datetime
import pandas as pd
import osgeo.ogr as ogr
import osgeo.osr as osr

#本程序用于批量提取ATL08数据中的冠层高程信息

data_path = 'E:\ICESat-2通用处理程序\data'  #待处理ATL08数据的文件夹路径
output_excel_path = 'E:\ICESat-2通用处理程序\output_excel'#提取的excel结果保存路径
output_shp_path = 'E:\ICESat-2通用处理程序\output_shp'#excel转为矢量结果的保存路径
beams=['gt1l','gt2l','gt3l','gt1r','gt2r','gt3r']#待提取的beam的名字

#遍历所有HDF5数据
for hdf5_file in os.listdir(data_path): 
    try:
        f = h5py.File(os.path.join(data_path,hdf5_file), 'r')  # 打开h5文件
        print('正在处理文件：' + str(hdf5_file))
    except:
        print('there is an h5 read error')
    else:
        #遍历所有需要提取的beam
        for beam in beams:
            # 这里因为有些ATL08数据的beam不全，需要跳过
            try:
                gt = f[str(beam)]
                land_segments = gt['land_segments']
            except:
                print('there is an beam error')
            else:
                #获取ATL08数据中需要的属性
                canopy = land_segments['canopy']
                terrain = land_segments['terrain']

                lat = land_segments['latitude']
                lon = land_segments['longitude']
                rgt = land_segments['rgt']
                beam_list = [str(beam) for i in lat]
                cloud_flag_atm = land_segments['cloud_flag_atm']

                time_str = str(hdf5_file)[6:14]
                time_nor = [time_str for i in lat]

                h_canopy_rel = canopy['h_canopy']
                h_canopy_abs = canopy['h_canopy_abs']
                h_canopy_uncertainty = canopy['h_canopy_uncertainty']
                h_surf = terrain['h_te_best_fit']

                #创建新的数据结构来存储数据
                newdata_dic = {
                    'latitude':lat,
                    'longitude':lon,
                    'rgt':rgt,
                    'beam':beam_list,
                    'cloud_flag':cloud_flag_atm,
                    'time':time_nor,
                    'h_canopy_rel':h_canopy_rel,
                    'h_canopy_abs':h_canopy_abs,
                    'h_canopy_uncertainty':h_canopy_uncertainty,
                    'h_surf':h_surf
                }

                newdata = pd.DataFrame(newdata_dic)
                # newdata = newdata[float(newdata.h_canopy_rel)<10000]
                record_list=[]

                #剔除树高大于10000的噪声点
                for i in range(len(lat)):
                    if(float(newdata.h_canopy_rel[i])>10000):
                        record_list.append(i)
                newdata = newdata.drop(record_list)

                #输出excel结果
                output_excel_name = os.path.join(output_excel_path,str(time_str)+'_'+str(beam)+'.xlsx')
                newdata.to_excel(output_excel_name)


                #根据excel生成矢量结果
                output_shp_name = os.path.join(output_shp_path, str(time_str) + '_' + str(beam) + '.shp')
                driver = ogr.GetDriverByName('ESRI Shapefile')
                data_source = driver.CreateDataSource(output_shp_name)

                proj = osr.SpatialReference()
                proj.ImportFromEPSG(4326)
                layer = data_source.CreateLayer(str(time_str) + '_' + str(beam),proj,ogr.wkbPoint)


                #创建字段
                field_name = ogr.FieldDefn("Latitude",ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                field_name = ogr.FieldDefn("Longitude", ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                field_name = ogr.FieldDefn("RGT", ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                field_name = ogr.FieldDefn("Beam", ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                field_name = ogr.FieldDefn("Cloud_flag", ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                field_name = ogr.FieldDefn("Time", ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                field_name = ogr.FieldDefn("H_canopy_r", ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                field_name = ogr.FieldDefn("H_canopy_a", ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                field_name = ogr.FieldDefn("H_canopy_u", ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                field_name = ogr.FieldDefn("H_surf", ogr.OFTString)
                field_name.SetWidth(20)
                layer.CreateField(field_name)

                for p in range(len(lat)):
                    if p in record_list:
                        continue
                    # print(p)
                    feature = ogr.Feature(layer.GetLayerDefn())

                    feature.SetField('Latitude',str(lat[p]))
                    feature.SetField('Longitude', str(lon[p]))
                    feature.SetField('RGT', str(rgt[p]))
                    feature.SetField('Beam', str(beam_list[p]))
                    feature.SetField('Cloud_flag', str(cloud_flag_atm[p]))
                    feature.SetField('Time', str(time_nor[p]))
                    feature.SetField('H_canopy_r', str(h_canopy_rel[p]))
                    feature.SetField('H_canopy_a', str(h_canopy_abs[p]))
                    feature.SetField('H_canopy_u', str(h_canopy_uncertainty[p]))
                    feature.SetField('H_surf', str(h_surf[p]))

                    point = ogr.Geometry(ogr.wkbPoint)
                    point.AddPoint(float(lon[p]),float(lat[p]))
                    feature.SetGeometry(point)
                    layer.CreateFeature(feature)
                    feature.Destroy()
                data_source.Destroy()

