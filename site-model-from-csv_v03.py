# -*- coding: utf-8 -*-
"""
Spyder Editor

"""

# -*- coding: utf-8 -*-
"""
Modified on 9 June 2020

Must have header info. Columns must be Lon, Lat, Vs30, Z2.5, Z1.0 in that order.

@author: abbott
"""
"""
Functions to read in specific csv site model info to create xml site model for
OpenQuake. Header line must exist, data must be in format: Lon, Lat, Vs30, Z2.5,
Z1.0
"""

from lxml import etree 
import csv
import math

    
model = 'Minerva_all'
csv_site_info_directory = './all_NZ'
out_directory = './all_NZ'
#csv_site_info = 'test.csv'
csv_site_info = 'Grid_join_WGS84_Z1_Z2p5.csv'
out_filename = model + '_site-model.xml'

def isFloat(value):
    try:
        float(value)
        return True
    except ValueError: "Can't convert to float, skipping"
    return False

def readSiteCsv(csv_site_info_directory, csv_site_info):
    """
	Function to read in site model, turn into dictionary with lat and lon
    as keys, site parameter values as values.
    
	INPUT: csv with site info 
	OUTPUT: lists of params
    """
	
    params_dict = {}
    #lon, lat = 0., 0.
	
    with open ((csv_site_info_directory + '/' + csv_site_info), newline='') as csvfile:
        sitereader = csv.reader(csvfile, delimiter = ',')
        
        # Skip header row
        sitereader.__next__()

        for row in sitereader:
            
            # record params in variable for clarity
            lon = row[0]
            lat = row[1]
            vs30 = float(row[2])
            # using California calc from Campbell & Bozorgnia 2014
            z2pt5 = math.exp(7.089 - 1.144 * math.log(vs30))
            # using calc from Chiou & Youngs 2008
            z1pt0 = math.exp(28.5 - (3.82 / 8.0) * math.log(vs30**8 + 378.7**8))

            # Only add key to dictionary if site params can become floats
            if isFloat(lon) & isFloat(lat) & isFloat(vs30) & isFloat(z2pt5) & isFloat(z1pt0):
                if (float(lon) < 180) & (float(lon) > -180) & (float(lat) < 90) & (float(lon) > -90):
                    params_dict.update({(lon, lat): (vs30, z1pt0, z2pt5)})
    
    return params_dict

'''
def getMinMax(params_dict):
    
    minLon = min(params_dict, key=lambda k: params_dict[k][0])[0]
    maxLon = max(params_dict, key=lambda k: params_dict[k][0])[0]
    minLat = min(params_dict, key=lambda k: params_dict[k][1])[1]
    maxLat = max(params_dict, key=lambda k: params_dict[k][1])[1]
    
    return minLon, maxLon, minLat, maxLat
'''

def site2nrml(model, params_dict):
    
    """
    Function to take params read into dict from csv and returns
    site model file in xml
    INPUT: site parameters lists
    OUTPUT: nrml site model file
    """ 
    """
    # Some XML definitions
    NAMESPACE = 'http://openquake.org/xmlns/nrml/0.4'
    GML_NAMESPACE = 'http://www.opengis.net/gml'
    SERIALIZE_NS_MAP = {None: NAMESPACE, 'gml': GML_NAMESPACE}   
    gml_ns = SERIALIZE_NS_MAP['gml']
    """
    
    # Head matter    
    root = etree.Element(_tag='nrml', nsmap={'gml': 'http://www.opengis.net/gml'})
    root.set('xmlns', 'http://openquake.org/xmlns/nrml/0.4')
    root.append(etree.Comment('%s' % '%s site model' %(model)))
    

    # Define Site Model Name    
    sMod = etree.SubElement(root, "siteModel")
    sMod.set('name', model + ' Site Model')
    
    # Define sub element
    
    for key in params_dict:
        
        site = etree.SubElement(sMod, "site")
        site.set('lon', '%s' % key[0])
        site.set('lat', '%s' % key[1])
        site.set('vs30', '%s' % params_dict[key][0])
        site.set('vs30Type', '%s' % 'inferred')
        site.set('z1pt0', '%s' % '%3.3f' % float(params_dict[key][1]))
        site.set('z2pt5', '%s' % '%3.3f' % float(params_dict[key][2]))
        
    #print(getMinMax(params_dict))
 
    # Form tree and write to xml
    root_tree = etree.ElementTree(root)
    outFile = open((out_directory + '/' + out_filename), 'wb')
    root_tree.write(outFile, encoding="utf-8", xml_declaration=True, pretty_print=True)       

if __name__ == "__main__":
    
    params_dict = readSiteCsv(csv_site_info_directory, csv_site_info)
    site2nrml(model, params_dict)
    
    print("finished!")