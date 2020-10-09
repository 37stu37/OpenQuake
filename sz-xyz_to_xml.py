# -*- coding: utf-8 -*-
"""
Spyder Editor

"""

# -*- coding: utf-8 -*-
"""
Modified on 11 Sept

Must have unzipped file. .xyz files must contain contours (lon, lat, depth)

@author: abbott
"""
"""
Functions to read in specific xyz sz contour info to create xml complex geom for
the subduction zone in OpenQuake. Data must be in format: Lon, Lat, depth.

Only works for one source at a time right now
"""

import os
from lxml import etree 
import pandas as pd
from shapely.geometry import Polygon, Point


    
sz = 'hik'
in_directory = './for_liz2'
out_directory = '.'
contour_differentiator = 'current' #'current'
out_file = sz + '-' + contour_differentiator + '-revised_geom' +'.xml'

#sz parameters by 2010 segment: 
hik10_attr = ['mag', 'occurRate', 'topDep', 'bottomDep', 'cornerpoints']

# mag, occur_rate, lon/lat/dep cornerpoints list (upper north, upper south, lower north, lower south)


hik10_src = ['HBaymax', 'HBaymin', 'Raukmax', 'Raukmin', 'Wgtnmax', 'Wgtnmin', 'All']
hik10_dict = {'HBaymax': [8.3, 0.000588235294117647, 5, 20, [(178.573, -39.268), (177.4, -40.83), (177.508, -38.784), (176.311, -40.345)]],
           'HBaymin': [8.1, 0.0007692307692307692, 5, 15, [(178.573, -39.268), (177.400, -40.830), (177.862, -38.947), (176.672, -40.508)]],
           'Raukmax': [8.3, 0.0007142857142857143, 5, 20, [(179.735, -37.713), (178.573, -39.268), (178.692, -37.229), (177.508, -38.784)]],
           'Raukmin': [8.1, 0.001, 5, 15, [(179.735, -37.713), (178.573, -39.268), (179.038, -37.392), (177.862, -38.947)]],
           'Wgtnmax': [8.4, 0.0009090909090909091, 5, 30, [(177.295, -40.705), (175.388, -42.118), (176.123, -39.798), (174.191, -41.211)]],
           'Wgtnmin': [8.1, 0.0016666666666666668, 15, 25, [(176.803, -40.340), (174.897, -41.753), (176.333, -39.979), (174.416, -41.392)]],
           'All': [9.0, 0.00017241379310344826, 5, 24, [(179.735, -37.713), (175.388, -42.118), (178.657, -37.060), (174.240, -41.464)]]}


hik10_df = pd.DataFrame(hik10_dict, index=hik10_attr)

#declare variables
depth_list = []
file_list = []
sorted_file_list = []

def splitFile(entry):
    
    return entry.split('_')

def readDirectory(in_directory, contour_differentiator):
    '''
    reads files in directory, uses differentiator (current, high, low) to
    search for appropriate contour files and record the depths that each file
    represents
    '''
    for entry in os.listdir(in_directory):
        split_file = splitFile(entry)
        if len(split_file) >= 3:
            if split_file[2] == 'contours.txt' and(split_file[1] == contour_differentiator):
                depth = -1*float(split_file[3])
                if depth not in depth_list: depth_list.append(depth)
                depth_list.sort() # sort from shallow to deep
                file_list.append(entry)
        else: pass

    
    return depth_list, file_list

def fileListByDepth(in_directory, depth_list, file_list):
    '''
    uses depth list and list of appropriate files to order the files from
    shallowest to deepest depth
    '''
    for val in depth_list:
        for entry in file_list:

            if float(splitFile(entry)[3]) == -1*val:
                sorted_file_list.append(entry)
    
    return sorted_file_list

def createSZdict(sorted_file_list, depth_list):
    """
	Function to read contour files from directory and write into
    dictionary with depth as the key, and lon, lat pairs as values.
    
	INPUT: location of files, filetype
	OUTPUT: lists of params
    """
     
    sz_conts_dict = {}
    for val in depth_list:
        sz_contour_locs = []
        for file in sorted_file_list:
            if float(splitFile(file)[3]) == -1*val:
                with open ((in_directory + '/' + file), newline='') as contfile:
        
                    for line in contfile:
                        row = line.split()
                    
                        if val == -1*float(row[2]):
                            sz_contour_locs.append(createVal(row))
                            sz_contour_locs.sort(key=lambda x:x[1]) #order list by latitude
                        else: raise Exception("depth in file dne depth in filename")
        
        # convert list of tuples to list: https://www.geeksforgeeks.org/python-convert-list-of-tuples-into-list/
        sz_contour_locs_list = [item for t in sz_contour_locs for item in t]
        # make everything in list floats: https://stackoverflow.com/questions/1614236/in-python-how-do-i-convert-all-of-the-items-in-a-list-to-floats
        sz_contour_locs_list = [float(i) for i in sz_contour_locs_list]
        # add to dictionary under depth value key
        sz_conts_dict[val] = sz_contour_locs_list

    return sz_conts_dict

def createVal(row):
    lon = row[0]
    lat = row[1]
    row_loc = (lon,lat)
    return row_loc

def insertDepths(topCoords, depth):
    clipped_cont = []
    for item in topCoords:
        clipped_cont.append(item[0])
        clipped_cont.append(item[1])
        clipped_cont.append(depth)
    
    return clipped_cont

def hik10Sources(hik10_df, sz_conts_dict, hik10_src):
    '''
    Only works for 1 source at a time.
    '''

    hik10_cont_dict = {}
    
    for key in sz_conts_dict:
        
        hik10_cont_list=[0]* hik10_df.shape[1]
        count = 0
        
        for col in hik10_df:
            src_cont_list = []
        
            hik10_poly = Polygon(hik10_df.loc['cornerpoints', col])
            
            it = iter(sz_conts_dict[key])
            
            for x in it: 
                point = (x, next(it))
                test_point = Point(point)
                if test_point.within(hik10_poly): #.contains(test_point):
                    src_cont_list.append(point)
            hik10_cont_list[count] = src_cont_list   
            count += 1
            
        hik10_cont_dict[key] = hik10_cont_list
    
    hik10_cont_df = pd.DataFrame(hik10_cont_dict, index=hik10_src)
    
    return hik10_df.append(hik10_cont_df.transpose(), sort=True)

def src2nrml(sz, hik10_df, depth_list, out_file):
    
    """
    Function to take params read into dict from csv and returns
    site model file in xml
    INPUT: site parameters lists
    OUTPUT: nrml site model file
    """ 

    # Some XML definitions
    NAMESPACE = 'http://openquake.org/xmlns/nrml/0.4'
    GML_NAMESPACE = 'http://www.opengis.net/gml'
    SERIALIZE_NS_MAP = {None: NAMESPACE, 'gml': GML_NAMESPACE}   
    gml_ns = SERIALIZE_NS_MAP['gml']
    
    # Head matter    
    root = etree.Element(_tag='nrml', nsmap={'gml': 'http://www.opengis.net/gml'})
    root.set('xmlns', 'http://openquake.org/xmlns/nrml/0.4')
    root.append(etree.Comment('%s' % sz + ' sz sources from contour files'))

    # Define Source Model Name    
    sMod = etree.SubElement(root, "sourceModel")
    sMod.set('name', 'Seismic Source Model')    
    j = 0 # source id counter
    i = 0 # will eventually need to iterate through cols in dataframe

    for col in hik10_df:
        #create list that says whether contour is empty or not
        notempty = [True]*len(depth_list)
        for ix in range(0,len(depth_list)):
            if not hik10_df.loc[depth_list[ix]][i]:
                notempty[ix] = False
                if ix != 0 and notempty[ix -1]:
                    bottom_ix = ix-1
        
        if True not in notempty:
            print("PROBLEM - need to skip & throw exception eventually")
        else:
            top_ix = notempty.index(True)
        if False not in notempty:
            bottom_ix = len(depth_list)
        
        if top_ix == bottom_ix: print(hik10_df.columns.values[i])
    
        # Define Fault Source Type   
        fS = etree.SubElement(sMod, "characteristicFaultSource")
        fS.set('id', '%s' % str(j))
        j+=1
        #fS.set('name', '%s' % faultData[i][0])
    
        fS.set('name', '%s' % sz + str(hik10_df.columns.values[i])) 

        #fS.set('tectonicRegion', '%s' % faultData[i][1])
        fS.set('tectonicRegion', '%s' % 'Subduction Interface')
                
        # Set MFD and rates
        # FIX ME - currently hardcoded to be pure characteristic
        # add module in function readNSHMFlt to take char mag and output dist
        # then here, loop over the data like coords
        MFD = etree.SubElement(fS, 'incrementalMFD')
        MFD.set('minMag', '%s' % hik10_df.loc['mag'][i])
        MFD.set('binWidth', '0.1')
                
        # Set occurence rates
        rates = etree.SubElement(MFD, 'occurRates')
        rates.text = '%s' % str(hik10_df.loc['occurRate'][i])        
        # Set rake (Taken from fault sense in NSHM fault file)
        rake = etree.SubElement(fS, 'rake')
        rake.text = '%s' % 90        
                
        # Fault Type        
        surf = etree.SubElement(fS, 'surface')
                
        cfg = etree.SubElement(surf, 'complexFaultGeometry')
        
        # top edge
        cfte = etree.SubElement(cfg, 'faultTopEdge')                 
        gmlLS = etree.SubElement(cfte, '{%s}LineString' % gml_ns)
        gmlPos = etree.SubElement(gmlLS, '{%s}posList' % gml_ns)
        
        topCoords = hik10_df.loc[depth_list[top_ix]][i]
        top_cont = insertDepths(topCoords, depth_list[top_ix])
        gmlPos.text = ' '.join([str("%.3f" % x) for x in top_cont])
    
    
        # intermediate edges
        for d in depth_list[top_ix+1:bottom_ix]:
            cfie = etree.SubElement(cfg, 'intermediateEdge')
            gmlLS = etree.SubElement(cfie, '{%s}LineString' % gml_ns)
            gmlPos = etree.SubElement(gmlLS, '{%s}posList' % gml_ns)
            intCoords = hik10_df.loc[d][i]
            int_cont = insertDepths(intCoords, d)
            gmlPos.text = ' '.join([str("%.3f" % x) for x in int_cont])
                   
        cfbe = etree.SubElement(cfg, 'faultBottomEdge')
                        
        # bottom edge 
        gmlLS = etree.SubElement(cfbe, '{%s}LineString' % gml_ns)
        gmlPos = etree.SubElement(gmlLS, '{%s}posList' % gml_ns)                
        bottomCoords = hik10_df.loc[depth_list[bottom_ix]][i]
        bot_cont = insertDepths(bottomCoords, depth_list[bottom_ix])
        gmlPos.text = ' '.join([str("%.3f" % x) for x in bot_cont])
        
        i += 1
    # Form Tree and Write to XML
    root_tree = etree.ElementTree(root)

    nrml_file = open(out_file, 'wb')	
    root_tree.write(nrml_file, encoding="utf-8", xml_declaration=True, pretty_print=True)     

if __name__ == "__main__":
    
    depth_list, file_list = readDirectory(in_directory, contour_differentiator)
    sorted_file_list = fileListByDepth(in_directory, depth_list, file_list)
    sz_conts_dict = createSZdict(sorted_file_list, depth_list)
    hik10_df = hik10Sources(hik10_df, sz_conts_dict, hik10_src)

    src2nrml(sz, hik10_df, depth_list, out_file)

    print("finished!")