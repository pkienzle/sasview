

############################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#If you use DANSE applications to do scientific research that leads to 
#publication, we ask that you acknowledge the use of the software with the 
#following sentence:
#This work benefited from DANSE software developed under NSF award DMR-0520547. 
#copyright 2008,2009 University of Tennessee
#############################################################################

# Known issue: reader not compatible with multiple SASdata entries
# within a single SASentry. Will raise a runtime error.

#TODO: check that all vectors are written only if they have at 
#    least one non-empty value
#TODO: Writing only allows one SASentry per file.
#     Would be best to allow multiple entries.
#TODO: Store error list
#TODO: Allow for additional meta data for each section
#TODO: Notes need to be implemented. They can be any XML 
#    structure in version 1.0
#      Process notes have the same problem.
#TODO: Unit conversion is not complete (temperature units are missing)


import logging
import numpy
import os
import sys
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.dataFitting import Data2D
from DataLoader.data_info import Collimation
from DataLoader.data_info import Detector
from DataLoader.data_info import Process
from DataLoader.data_info import Aperture
from lxml import etree
import xml.dom.minidom

has_converter = True
try:
    from data_util.nxsunit import Converter
except:
    has_converter = False

STATE_NS = "State/1.0"

def write_node(doc, parent, name, value, attr={}):
    """
    :param doc: document DOM
    :param parent: parent node
    :param name: tag of the element
    :param value: value of the child text node
    :param attr: attribute dictionary
    
    :return: True if something was appended, otherwise False
    """
    if value is not None:
        node = doc.createElement(name)
        node.appendChild(doc.createTextNode(str(value)))
        for item in attr:
            node.setAttribute(item, attr[item])
        parent.appendChild(node)
        return True
    return False

def get_content(location, node):
    """
    Get the first instance of the content of a xpath location.
    
    :param location: xpath location
    :param node: node to start at
    
    :return: Element, or None
    """
    nodes = node.xpath(location, namespaces={'ns': STATE_NODE})
    
    if len(nodes)>0:
        return nodes[0]
    else:
        return None

def get_float(location, node):
    """
    Get the content of a node as a float 
    
    :param location: xpath location
    :param node: node to start at
    """
    nodes = node.xpath(location, namespaces={'ns': STATE_NODE})
    
    value = None
    attr = {}
    if len(nodes) > 0:
        try:
            value = float(nodes[0].text)   
        except:
            # Could not pass, skip and return None
            msg = "state_reader.get_float: could not "
            msg += " convert '%s' to float" % nodes[0].text
            logging.error(msg)
        if nodes[0].get('unit') is not None:
            attr['unit'] = nodes[0].get('unit')
    return value, attr

            
class Reader1D:
    """
    read state of a plugin  and available data 
    
    :Dependencies:
        The CanSas reader requires PyXML 0.8.4 or later.
    """
    ## CanSAS version
    version = '1.0'
    ## File type
    type_name = "CanSAS 1D"
    ## Wildcards
    type = []

    ## List of allowed extensions
    ext = []  
    
    def __init__(self):
        ## List of errors
        self.errors = []
    
    def read(self, path):
        """ 
        Load data file
        
        :param path: file path
        
        :return: Data1D object if a single SASentry was found, 
                    or a list of Data1D objects if multiple entries were found,
                    or None of nothing was found
                    
        :raise RuntimeError: when the file can't be opened
        :raise ValueError: when the length of the data vectors are inconsistent
        """
        output = []
        if os.path.isfile(path):
            basename  = os.path.basename(path)
            root, extension = os.path.splitext(basename)
            if extension.lower() in self.ext:
                
                tree = etree.parse(path, parser=etree.ETCompatXMLParser())
                # Check the format version number
                # Specifying the namespace will take care of the file
                # format version 
                root = tree.getroot()
                
                entry_list = root.xpath('/ns:SASroot/ns:SASentry',
                                         namespaces={'ns': STATE_NODE})
                
                for entry in entry_list:
                    self.errors = []
                    sas_entry = self._parse_entry(entry)
                    sas_entry.filename = basename
                    
                    # Store loading process information
                    sas_entry.errors = self.errors
                    sas_entry.meta_data['loader'] = self.type_name
                    output.append(sas_entry)
                
        else:
            raise RuntimeError, "%s is not a file" % path
        # Return output consistent with the loader's api
        if len(output) == 0:
            #cannot return none when it cannot read 
            #return None
            raise RuntimeError, "%s cannot be read \n" % path
        elif len(output) == 1:
            return output[0]
        else:
            return output                
                
    def _parse_entry(self, dom):
        """
        Parse a SASentry
        
        :param node: SASentry node
        
        :return: Data1D object
        """
        x = numpy.zeros(0)
        y = numpy.zeros(0)
        
        data_info = Data1D(x, y)
        
        # Look up title      
        self._store_content('ns:Title', dom, 'title', data_info)
        
        # Look up run number   
        nodes = dom.xpath('ns:Run', namespaces={'ns': STATE_NODE})
        for item in nodes:    
            if item.text is not None:
                value = item.text.strip()
                if len(value) > 0:
                    data_info.run.append(value)
                    if item.get('name') is not None:
                        data_info.run_name[value] = item.get('name')
                           
        # Look up instrument name              
        self._store_content('ns:SASinstrument/ns:name', dom, 'instrument',
                             data_info)

        # Notes
        note_list = dom.xpath('ns:SASnote', namespaces={'ns': STATE_NODE})
        for note in note_list:
            try:
                if note.text is not None:
                    note_value = note.text.strip()
                    if len(note_value) > 0:
                        data_info.notes.append(note_value)
            except:
                err_mess = "state_reader.read: error processing"
                err_mess += " entry notes\n  %s" % sys.exc_value
                self.errors.append(err_mess)
                logging.error(err_mess)
        
        # Sample info ###################
        entry = get_content('ns:SASsample', dom)
        if entry is not None:
            data_info.sample.name = entry.get('name')
            
        self._store_content('ns:SASsample/ns:ID', 
                     dom, 'ID', data_info.sample)                    
        self._store_float('ns:SASsample/ns:thickness', 
                     dom, 'thickness', data_info.sample)
        self._store_float('ns:SASsample/ns:transmission', 
                     dom, 'transmission', data_info.sample)
        self._store_float('ns:SASsample/ns:temperature', 
                     dom, 'temperature', data_info.sample)
        
        nodes = dom.xpath('ns:SASsample/ns:details', 
                          namespaces={'ns': STATE_NODE})
        for item in nodes:
            try:
                if item.text is not None:
                    detail_value = item.text.strip()
                    if len(detail_value) > 0:
                        data_info.sample.details.append(detail_value)
            except:
                err_mess = "state_reader.read: error processing "
                err_mess += " sample details\n  %s" % sys.exc_value
                self.errors.append(err_mess)
                logging.error(err_mess)
        
        # Position (as a vector)
        self._store_float('ns:SASsample/ns:position/ns:x', 
                     dom, 'position.x', data_info.sample)          
        self._store_float('ns:SASsample/ns:position/ns:y', 
                     dom, 'position.y', data_info.sample)          
        self._store_float('ns:SASsample/ns:position/ns:z', 
                     dom, 'position.z', data_info.sample)          
        
        # Orientation (as a vector)
        self._store_float('ns:SASsample/ns:orientation/ns:roll', 
                     dom, 'orientation.x', data_info.sample)          
        self._store_float('ns:SASsample/ns:orientation/ns:pitch', 
                     dom, 'orientation.y', data_info.sample)          
        self._store_float('ns:SASsample/ns:orientation/ns:yaw', 
                     dom, 'orientation.z', data_info.sample)          
       
        # Source info ###################
        entry = get_content('ns:SASinstrument/ns:SASsource', dom)
        if entry is not None:
            data_info.source.name = entry.get('name')
        
        self._store_content('ns:SASinstrument/ns:SASsource/ns:radiation', 
                     dom, 'radiation', data_info.source)                    
        self._store_content('ns:SASinstrument/ns:SASsource/ns:beam_shape', 
                     dom, 'beam_shape', data_info.source)                    
        self._store_float('ns:SASinstrument/ns:SASsource/ns:wavelength', 
                     dom, 'wavelength', data_info.source)          
        self._store_float('ns:SASinstrument/ns:SASsource/ns:wavelength_min', 
                     dom, 'wavelength_min', data_info.source)          
        self._store_float('ns:SASinstrument/ns:SASsource/ns:wavelength_max', 
                     dom, 'wavelength_max', data_info.source)          
        self._store_float('ns:SASinstrument/ns:SASsource/ns:wavelength_spread', 
                     dom, 'wavelength_spread', data_info.source)    
        
        # Beam size (as a vector)   
        entry = get_content('ns:SASinstrument/ns:SASsource/ns:beam_size', dom)
        if entry is not None:
            data_info.source.beam_size_name = entry.get('name')
            
        self._store_float('ns:SASinstrument/ns:SASsource/ns:beam_size/ns:x', 
                     dom, 'beam_size.x', data_info.source)    
        self._store_float('ns:SASinstrument/ns:SASsource/ns:beam_size/ns:y', 
                     dom, 'beam_size.y', data_info.source)    
        self._store_float('ns:SASinstrument/ns:SASsource/ns:beam_size/ns:z', 
                     dom, 'beam_size.z', data_info.source)    
        
        # Collimation info ###################
        nodes = dom.xpath('ns:SASinstrument/ns:SAScollimation', 
                          namespaces={'ns': STATE_NODE})
        for item in nodes:
            collim = Collimation()
            if item.get('name') is not None:
                collim.name = item.get('name')
            self._store_float('ns:length', item, 'length', collim)  
            
            # Look for apertures
            apert_list = item.xpath('ns:aperture', namespaces={'ns': STATE_NODE})
            for apert in apert_list:
                aperture =  Aperture()
                
                # Get the name and type of the aperture
                aperture.name = apert.get('name')
                aperture.type = apert.get('type')
                    
                self._store_float('ns:distance', apert, 'distance', aperture)    
                
                entry = get_content('ns:size', apert)
                if entry is not None:
                    aperture.size_name = entry.get('name')
                
                self._store_float('ns:size/ns:x', apert, 'size.x', aperture)    
                self._store_float('ns:size/ns:y', apert, 'size.y', aperture)    
                self._store_float('ns:size/ns:z', apert, 'size.z', aperture)
                
                collim.aperture.append(aperture)
                
            data_info.collimation.append(collim)
        
        # Detector info ######################
        nodes = dom.xpath('ns:SASinstrument/ns:SASdetector',
                           namespaces={'ns': STATE_NODE})
        for item in nodes:
            
            detector = Detector()
            
            self._store_content('ns:name', item, 'name', detector)
            self._store_float('ns:SDD', item, 'distance', detector)    
            
            # Detector offset (as a vector)
            self._store_float('ns:offset/ns:x', item, 'offset.x', detector)    
            self._store_float('ns:offset/ns:y', item, 'offset.y', detector)    
            self._store_float('ns:offset/ns:z', item, 'offset.z', detector)    
            
            # Detector orientation (as a vector)
            self._store_float('ns:orientation/ns:roll',  item, 'orientation.x',
                               detector)    
            self._store_float('ns:orientation/ns:pitch', item, 'orientation.y',
                               detector)    
            self._store_float('ns:orientation/ns:yaw',   item, 'orientation.z',
                               detector)    
            
            # Beam center (as a vector)
            self._store_float('ns:beam_center/ns:x', item, 'beam_center.x',
                               detector)    
            self._store_float('ns:beam_center/ns:y', item, 'beam_center.y', 
                              detector)    
            self._store_float('ns:beam_center/ns:z', item, 'beam_center.z',
                               detector)    
            
            # Pixel size (as a vector)
            self._store_float('ns:pixel_size/ns:x', item, 'pixel_size.x',
                               detector)    
            self._store_float('ns:pixel_size/ns:y', item, 'pixel_size.y',
                               detector)    
            self._store_float('ns:pixel_size/ns:z', item, 'pixel_size.z',
                               detector)    
            
            self._store_float('ns:slit_length', item, 'slit_length', detector)
            
            data_info.detector.append(detector)    

        # Processes info ######################
        nodes = dom.xpath('ns:SASprocess', namespaces={'ns': STATE_NODE})
        for item in nodes:
            process = Process()
            self._store_content('ns:name', item, 'name', process)
            self._store_content('ns:date', item, 'date', process)
            self._store_content('ns:description', item, 'description', process)
            
            term_list = item.xpath('ns:term', namespaces={'ns': STATE_NODE})
            for term in term_list:
                try:
                    term_attr = {}
                    for attr in term.keys():
                        term_attr[attr] = term.get(attr).strip()
                    if term.text is not None:
                        term_attr['value'] = term.text.strip()
                        process.term.append(term_attr)
                except:
                    err_mess = "state_reader.read: error processing "
                    err_mess += " process term\n  %s" % sys.exc_value
                    self.errors.append(err_mess)
                    logging.error(err_mess)
            
            note_list = item.xpath('ns:SASprocessnote', 
                                   namespaces={'ns': STATE_NODE})
            for note in note_list:
                if note.text is not None:
                    process.notes.append(note.text.strip())
            
            data_info.process.append(process)
            
            
        # Data info ######################
        nodes = dom.xpath('ns:SASdata', namespaces={'ns': STATE_NODE})
        if len(nodes) > 1:
            msg = "CanSAS reader is not compatible with multiple"
            msg += " SASdata entries"
            raise RuntimeError, msg
        
        nodes = dom.xpath('ns:SASdata/ns:Idata', namespaces={'ns': STATE_NODE})

        x  = numpy.zeros(0)
        y  = numpy.zeros(0)
        dx = numpy.zeros(0)
        dy = numpy.zeros(0)
        dxw = numpy.zeros(0)
        dxl = numpy.zeros(0)
        
        for item in nodes:
            _x, attr = get_float('ns:Q', item)
            _dx, attr_d = get_float('ns:Qdev', item)
            _dxl, attr_l = get_float('ns:dQl', item)
            _dxw, attr_w = get_float('ns:dQw', item)
            if _dx == None:
                _dx = 0.0
            if _dxl == None:
                _dxl = 0.0
            if _dxw == None:
                _dxw = 0.0
                
            if attr.has_key('unit') and \
                attr['unit'].lower() != data_info.x_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_q = Converter(attr['unit'])
                        _x = data_conv_q(_x, units=data_info.x_unit)
                    except:
                        msg =  "CanSAS reader: could not convert "
                        msg += "Q unit [%s]; " 
                        msg += "expecting [%s]\n  %s" % (attr['unit'], 
                                  data_info.x_unit, sys.exc_value)
                        raise ValueError, msg
                        
                else:
                    msg = "CanSAS reader: unrecognized Q unit [%s]; "
                    msg += "expecting [%s]" % (attr['unit'], data_info.x_unit)
                    raise ValueError, msg
                        
            # Error in Q
            if attr_d.has_key('unit') and \
                attr_d['unit'].lower() != data_info.x_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_q = Converter(attr_d['unit'])
                        _dx = data_conv_q(_dx, units=data_info.x_unit)
                    except:
                        msg = "CanSAS reader: could not convert dQ unit [%s];"
                        msg += " expecting " 
                        msg += "[%s]\n  %s" % (attr['unit'],
                                                data_info.x_unit, sys.exc_value)
                        raise ValueError, msg
                        
                else:
                    msg = "CanSAS reader: unrecognized dQ unit [%s]; "
                    msg += "expecting [%s]" % (attr['unit'], data_info.x_unit)
                    raise ValueError,  msg
                        
            # Slit length
            if attr_l.has_key('unit') and \
                attr_l['unit'].lower() != data_info.x_unit.lower():
                if has_converter == True:
                    try:
                        data_conv_q = Converter(attr_l['unit'])
                        _dxl = data_conv_q(_dxl, units=data_info.x_unit)
                    except:
                        msg = "CanSAS reader: could not convert dQl unit [%s];"
                        msg += " expecting [%s]\n  %s" % (attr['unit'],
                                             data_info.x_unit, sys.exc_value)
                        raise ValueError, msg
                        
                else:
                    msg = "CanSAS reader: unrecognized dQl unit [%s];"
                    msg += " expecting [%s]" % (attr['unit'], data_info.x_unit)
                    raise ValueError, msg
                        
            # Slit width
            if attr_w.has_key('unit') and \
            attr_w['unit'].lower() != data_info.x_unit.lower():
                if has_converter == True:
                    try:
                        data_conv_q = Converter(attr_w['unit'])
                        _dxw = data_conv_q(_dxw, units=data_info.x_unit)
                    except:
                        msg = "CanSAS reader: could not convert dQw unit [%s];"
                        msg += " expecting [%s]\n  %s" % (attr['unit'], 
                                                data_info.x_unit, sys.exc_value)
                        raise ValueError, msg
                        
                else:
                    msg = "CanSAS reader: unrecognized dQw unit [%s];"
                    msg += " expecting [%s]" % (attr['unit'], data_info.x_unit)
                    raise ValueError, msg   
            _y, attr = get_float('ns:I', item)
            _dy, attr_d = get_float('ns:Idev', item)
            if _dy == None:
                _dy = 0.0
            if attr.has_key('unit') and \
            attr['unit'].lower() != data_info.y_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_i = Converter(attr['unit'])
                        _y = data_conv_i(_y, units=data_info.y_unit)
                    except:
                        msg = "CanSAS reader: could not convert I(q) unit [%s];"
                        msg += " expecting [%s]\n  %s" % (attr['unit'], 
                                            data_info.y_unit, sys.exc_value)
                        raise ValueError, msg
                else:
                    msg = "CanSAS reader: unrecognized I(q) unit [%s];"
                    msg += " expecting [%s]" % (attr['unit'], data_info.y_unit)
                    raise ValueError, msg 
                        
            if attr_d.has_key('unit') and \
            attr_d['unit'].lower() != data_info.y_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_i = Converter(attr_d['unit'])
                        _dy = data_conv_i(_dy, units=data_info.y_unit)
                    except:
                        msg = "CanSAS reader: could not convert dI(q) unit "
                        msg += "[%s]; expecting [%s]\n  %s"  % (attr_d['unit'],
                                             data_info.y_unit, sys.exc_value)
                        raise ValueError, msg
                else:
                    msg = "CanSAS reader: unrecognized dI(q) unit [%s]; "
                    msg += "expecting [%s]" % (attr_d['unit'], data_info.y_unit)
                    raise ValueError, msg
                
            if _x is not None and _y is not None:
                x  = numpy.append(x, _x)
                y  = numpy.append(y, _y)
                dx = numpy.append(dx, _dx)
                dy = numpy.append(dy, _dy)
                dxl = numpy.append(dxl, _dxl)
                dxw = numpy.append(dxw, _dxw)
                
        data_info.x = x
        data_info.y = y
        data_info.dx = dx
        data_info.dy = dy
        data_info.dxl = dxl
        data_info.dxw = dxw
        
        data_conv_q = None
        data_conv_i = None
        
        if has_converter == True and data_info.x_unit != '1/A':
            data_conv_q = Converter('1/A')
            # Test it
            data_conv_q(1.0, output.Q_unit)
            
        if has_converter == True and data_info.y_unit != '1/cm':
            data_conv_i = Converter('1/cm')
            # Test it
            data_conv_i(1.0, output.I_unit)                    
                
        if data_conv_q is not None:
            data_info.xaxis("\\rm{Q}", data_info.x_unit)
        else:
            data_info.xaxis("\\rm{Q}", 'A^{-1}')
        if data_conv_i is not None:
            data_info.yaxis("\\rm{Intensity}", data_info.y_unit)
        else:
            data_info.yaxis("\\rm{Intensity}","cm^{-1}")
        
        return data_info

    def _to_xml_doc(self, datainfo):
        """
        Create an XML document to contain the content of a Data1D
        
        :param datainfo: Data1D object
        """
        
        if not issubclass(datainfo.__class__, Data1D):
            raise RuntimeError, "The cansas writer expects a Data1D instance"
        
        doc = xml.dom.minidom.Document()
        main_node = doc.createElement("SASroot")
        main_node.setAttribute("version", self.version)
        main_node.setAttribute("xmlns", "cansas1d/%s" % self.version)
        main_node.setAttribute("xmlns:xsi",
                               "http://www.w3.org/2001/XMLSchema-instance")
        main_node.setAttribute("xsi:schemaLocation",
                               "cansas1d/%s http://svn.smallangles.net/svn/canSAS/1dwg/trunk/cansas1d.xsd" % self.version)
        
        doc.appendChild(main_node)
        
        entry_node = doc.createElement("SASentry")
        main_node.appendChild(entry_node)
        
        write_node(doc, entry_node, "Title", datainfo.title)
        for item in datainfo.run:
            runname = {}
            if datainfo.run_name.has_key(item) and \
            len(str(datainfo.run_name[item]))>1:
                runname = {'name': datainfo.run_name[item] }
            write_node(doc, entry_node, "Run", item, runname)
        
        # Data info
        node = doc.createElement("SASdata")
        entry_node.appendChild(node)
        
        for i in range(len(datainfo.x)):
            pt = doc.createElement("Idata")
            node.appendChild(pt)
            write_node(doc, pt, "Q", datainfo.x[i], {'unit':datainfo.x_unit})
            if len(datainfo.y)>=i:
                write_node(doc, pt, "I", datainfo.y[i],
                            {'unit':datainfo.y_unit})
            if datainfo.dx != None and len(datainfo.dx) >= i:
                write_node(doc, pt, "Qdev", datainfo.dx[i],
                            {'unit':datainfo.x_unit})
            if datainfo.dxl != None and len(datainfo.dxl) >= i:
                write_node(doc, pt, "dQl", datainfo.dxl[i],
                            {'unit':datainfo.x_unit})    
            if datainfo.dxw != None and len(datainfo.dxw) >= i:
                write_node(doc, pt, "dQw", datainfo.dxw[i],
                            {'unit':datainfo.x_unit})              
            if datainfo.dy != None and len(datainfo.dy) >= i:
                write_node(doc, pt, "Idev", datainfo.dy[i],
                            {'unit':datainfo.y_unit})
        #data gui info
        gui_info = doc.createElement("DataInfoGui")
        
        write_node(doc, gui_info, "group_id", 'group_id')
        for item in datainfo.group_id:
            write_node(doc, gui_info, "group_id", str(item))
        write_node(doc, gui_info, "name", datainfo.name)
        write_node(doc, gui_info, "id", datainfo.id)
        write_node(doc, gui_info, "group_id", datainfo.groud_id)
        write_node(doc, gui_info, "name", datainfo.name)
        write_node(doc, gui_info, "is_data", datainfo.is_data)
        write_node(doc, gui_info, "xtransform", datainfo.xtransform)
        write_node(doc, gui_info, "scale", datainfo.scale)
        write_node(doc, gui_info, "ytransform", datainfo.ytransform)
        write_node(doc, gui_info, "path", datainfo.path)
        node.appendChild(gui_info)
        # Sample info
        sample = doc.createElement("SASsample")
        if datainfo.sample.name is not None:
            sample.setAttribute("name", str(datainfo.sample.name))
        entry_node.appendChild(sample)
        write_node(doc, sample, "ID", str(datainfo.sample.ID))
        write_node(doc, sample, "thickness", datainfo.sample.thickness,
                   {"unit":datainfo.sample.thickness_unit})
        write_node(doc, sample, "transmission", datainfo.sample.transmission)
        write_node(doc, sample, "temperature", datainfo.sample.temperature,
                   {"unit":datainfo.sample.temperature_unit})
        
        for item in datainfo.sample.details:
            write_node(doc, sample, "details", item)
        
        pos = doc.createElement("position")
        written = write_node(doc, pos, "x", datainfo.sample.position.x,
                             {"unit":datainfo.sample.position_unit})
        written = written | write_node(doc, pos, "y",
                                       datainfo.sample.position.y,
                                       {"unit":datainfo.sample.position_unit})
        written = written | write_node(doc, pos, "z",
                                       datainfo.sample.position.z,
                                       {"unit":datainfo.sample.position_unit})
        if written == True:
            sample.appendChild(pos)
        
        ori = doc.createElement("orientation")
        written = write_node(doc, ori, "roll",
                             datainfo.sample.orientation.x,
                             {"unit":datainfo.sample.orientation_unit})
        written = written | write_node(doc, ori, "pitch",
                                       datainfo.sample.orientation.y,
                                    {"unit":datainfo.sample.orientation_unit})
        written = written | write_node(doc, ori, "yaw",
                                       datainfo.sample.orientation.z,
                                    {"unit":datainfo.sample.orientation_unit})
        if written == True:
            sample.appendChild(ori)
        
        # Instrument info
        instr = doc.createElement("SASinstrument")
        entry_node.appendChild(instr)
        
        write_node(doc, instr, "name", datainfo.instrument)
        
        #   Source
        source = doc.createElement("SASsource")
        if datainfo.source.name is not None:
            source.setAttribute("name", str(datainfo.source.name))
        instr.appendChild(source)
        
        write_node(doc, source, "radiation", datainfo.source.radiation)
        write_node(doc, source, "beam_shape", datainfo.source.beam_shape)
        size = doc.createElement("beam_size")
        if datainfo.source.beam_size_name is not None:
            size.setAttribute("name", str(datainfo.source.beam_size_name))
        written = write_node(doc, size, "x", datainfo.source.beam_size.x,
                             {"unit":datainfo.source.beam_size_unit})
        written = written | write_node(doc, size, "y",
                                       datainfo.source.beam_size.y,
                                       {"unit":datainfo.source.beam_size_unit})
        written = written | write_node(doc, size, "z",
                                       datainfo.source.beam_size.z,
                                       {"unit":datainfo.source.beam_size_unit})
        if written == True:
            source.appendChild(size)
            
        write_node(doc, source, "wavelength",
                   datainfo.source.wavelength,
                   {"unit":datainfo.source.wavelength_unit})
        write_node(doc, source, "wavelength_min",
                   datainfo.source.wavelength_min,
                   {"unit":datainfo.source.wavelength_min_unit})
        write_node(doc, source, "wavelength_max",
                   datainfo.source.wavelength_max,
                   {"unit":datainfo.source.wavelength_max_unit})
        write_node(doc, source, "wavelength_spread",
                   datainfo.source.wavelength_spread,
                   {"unit":datainfo.source.wavelength_spread_unit})
        
        #   Collimation
        for item in datainfo.collimation:
            coll = doc.createElement("SAScollimation")
            if item.name is not None:
                coll.setAttribute("name", str(item.name))
            instr.appendChild(coll)
            
            write_node(doc, coll, "length", item.length,
                       {"unit":item.length_unit})
            
            for apert in item.aperture:
                ap = doc.createElement("aperture")
                if apert.name is not None:
                    ap.setAttribute("name", str(apert.name))
                if apert.type is not None:
                    ap.setAttribute("type", str(apert.type))
                coll.appendChild(ap)
                
                write_node(doc, ap, "distance", apert.distance,
                           {"unit":apert.distance_unit})
                
                size = doc.createElement("size")
                if apert.size_name is not None:
                    size.setAttribute("name", str(apert.size_name))
                written = write_node(doc, size, "x", apert.size.x,
                                     {"unit":apert.size_unit})
                written = written | write_node(doc, size, "y", apert.size.y,
                                               {"unit":apert.size_unit})
                written = written | write_node(doc, size, "z", apert.size.z,
                                               {"unit":apert.size_unit})
                if written == True:
                    ap.appendChild(size)

        #   Detectors
        for item in datainfo.detector:
            det = doc.createElement("SASdetector")
            written = write_node(doc, det, "name", item.name)
            written = written | write_node(doc, det, "SDD", item.distance,
                                           {"unit":item.distance_unit})
            written = written | write_node(doc, det, "slit_length",
                                           item.slit_length,
                                           {"unit":item.slit_length_unit})
            if written == True:
                instr.appendChild(det)
            
            off = doc.createElement("offset")
            written = write_node(doc, off, "x", item.offset.x,
                                 {"unit":item.offset_unit})
            written = written | write_node(doc, off, "y", item.offset.y,
                                           {"unit":item.offset_unit})
            written = written | write_node(doc, off, "z", item.offset.z,
                                           {"unit":item.offset_unit})
            if written == True:
                det.appendChild(off)
            
            center = doc.createElement("beam_center")
            written = write_node(doc, center, "x", item.beam_center.x,
                                 {"unit":item.beam_center_unit})
            written = written | write_node(doc, center, "y",
                                           item.beam_center.y,
                                           {"unit":item.beam_center_unit})
            written = written | write_node(doc, center, "z",
                                           item.beam_center.z,
                                           {"unit":item.beam_center_unit})
            if written == True:
                det.appendChild(center)
                
            pix = doc.createElement("pixel_size")
            written = write_node(doc, pix, "x", item.pixel_size.x,
                                 {"unit":item.pixel_size_unit})
            written = written | write_node(doc, pix, "y", item.pixel_size.y,
                                           {"unit":item.pixel_size_unit})
            written = written | write_node(doc, pix, "z", item.pixel_size.z,
                                           {"unit":item.pixel_size_unit})
            if written == True:
                det.appendChild(pix)
                
            ori = doc.createElement("orientation")
            written = write_node(doc, ori, "roll",  item.orientation.x,
                                 {"unit":item.orientation_unit})
            written = written | write_node(doc, ori, "pitch",
                                           item.orientation.y,
                                           {"unit":item.orientation_unit})
            written = written | write_node(doc, ori, "yaw",
                                           item.orientation.z,
                                           {"unit":item.orientation_unit})
            if written == True:
                det.appendChild(ori)
                
        
        # Processes info
        for item in datainfo.process:
            node = doc.createElement("SASprocess")
            entry_node.appendChild(node)

            write_node(doc, node, "name", item.name)
            write_node(doc, node, "date", item.date)
            write_node(doc, node, "description", item.description)
            for term in item.term:
                value = term['value']
                del term['value']
                write_node(doc, node, "term", value, term)
            for note in item.notes:
                write_node(doc, node, "SASprocessnote", note)
        
        # Return the document, and the SASentry node associated with
        # the data we just wrote
        return doc, entry_node
            
    def write(self, filename, datainfo):
        """
        Write the content of a Data1D as a CanSAS XML file
        
        :param filename: name of the file to write
        :param datainfo: Data1D object
        """
        # Create XML document
        doc, sasentry = self._to_xml_doc(datainfo)
        # Write the file
        fd = open(filename, 'w')
        fd.write(doc.toprettyxml())
        fd.close()
        
    def _store_float(self, location, node, variable, storage, optional=True):
        """
        Get the content of a xpath location and store
        the result. Check that the units are compatible
        with the destination. The value is expected to
        be a float.
        
        The xpath location might or might not exist.
        If it does not exist, nothing is done
        
        :param location: xpath location to fetch
        :param node: node to read the data from
        :param variable: name of the data member to store it in [string]
        :param storage: data object that has the 'variable' data member
        :param optional: if True, no exception will be raised 
            if unit conversion can't be done

        :raise ValueError: raised when the units are not recognized
        """
        entry = get_content(location, node)
        try:
            value = float(entry.text)
        except:
            value = None
            
        if value is not None:
            # If the entry has units, check to see that they are
            # compatible with what we currently have in the data object
            units = entry.get('unit')
            if units is not None:
                toks = variable.split('.')
                exec "local_unit = storage.%s_unit" % toks[0]
                if units.lower()!=local_unit.lower():
                    if has_converter==True:
                        try:
                            conv = Converter(units)
                            exec "storage.%s = %g" % (variable,
                                            conv(value, units=local_unit))
                        except:
                            err_mess = "CanSAS reader: could not convert"
                            err_mess += " %s unit [%s]; expecting [%s]\n  %s" \
                                % (variable, units, local_unit, sys.exc_value)
                            self.errors.append(err_mess)
                            if optional:
                                logging.info(err_mess)
                            else:
                                raise ValueError, err_mess 
                    else:
                        err_mess = "CanSAS reader: unrecognized %s unit [%s];"
                        err_mess += " expecting [%s]" % (variable, 
                                                         units, local_unit)
                        self.errors.append(err_mess)
                        if optional:
                            logging.info(err_mess)
                        else:
                            raise ValueError, err_mess
                else:
                    exec "storage.%s = value" % variable
            else:
                exec "storage.%s = value" % variable
                
    def _store_content(self, location, node, variable, storage):
        """
        Get the content of a xpath location and store
        the result. The value is treated as a string.
        
        The xpath location might or might not exist.
        If it does not exist, nothing is done
        
        :param location: xpath location to fetch
        :param node: node to read the data from
        :param variable: name of the data member to store it in [string]
        :param storage: data object that has the 'variable' data member
        
        :return: return a list of errors
        """
        entry = get_content(location, node)
        if entry is not None and entry.text is not None:
            exec "storage.%s = entry.text.strip()" % variable

           

class Reader2D:
    """
    Class to load a basic guiframe state
    """
    ## File type
    type_name = "Fitting"
    
    ## Wildcards
    type = ["Fitting files (*.fitv)|*.fitv"
            "SANSView file (*.svs)|*.svs"]
    ## List of allowed extensions
    ext=['.fitv', '.FITV', '.svs', 'SVS']   
    
    def __init__(self):
        CansasReader.__init__(self)
        """
        Initialize the call-back method to be called
        after we load a file
        
        :param call_back: call-back method
        :param cansas:  True = files will be written/read in CanSAS format
                        False = write CanSAS format
            
        """
        ## Call back method to be executed after a file is read
        #self.call_back = call_back
        ## CanSAS format flag
        self.cansas = cansas
        self.state = None
        
    def read(self, path):
        """ 
        Load a new P(r) inversion state from file
        
        :param path: file path
        
        """
        if self.cansas == True:
            return self._read_cansas(path)
     
    def _to_xml_doc(self, datainfo):
        """
        Create an XML document to contain the content of a Data2D
        
        :param datainfo: Data2D object
        
        """
        if not issubclass(datainfo.__class__, Data2D):
            raise RuntimeError, "The cansas writer expects a Data2D instance"
        
        doc = xml.dom.minidom.Document()
        main_node = doc.createElement("SASroot")
        main_node.setAttribute("version", self.version)
        main_node.setAttribute("xmlns", "cansas1d/%s" % self.version)
        main_node.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        main_node.setAttribute("xsi:schemaLocation", "cansas1d/%s http://svn.smallangles.net/svn/canSAS/1dwg/trunk/cansas1d.xsd" % self.version)
        
        doc.appendChild(main_node)
        
        entry_node = doc.createElement("SASentry")
        main_node.appendChild(entry_node)
       
        write_node(doc, entry_node, "Title", datainfo.title)
        if datainfo is not None:
            write_node(doc, entry_node, "data_class", datainfo.__class__.__name__)
        for item in datainfo.run:
            runname = {}
            if datainfo.run_name.has_key(item) and len(str(datainfo.run_name[item]))>1:
                runname = {'name': datainfo.run_name[item] }
            write_node(doc, entry_node, "Run", item, runname)
        # Data info
        new_node = doc.createElement("SASdata")
        entry_node.appendChild(new_node)
        for item in list_of_data_2d_attr:
            element = doc.createElement(item[0])
            exec "element.setAttribute(item[0], str(datainfo.%s))"%(item[1])
            new_node.appendChild(element)
            
        for item in list_of_data2d_values:
            root_node = doc.createElement(item[0])
            new_node.appendChild(root_node)
            
            exec "temp_list = datainfo.%s"%item[1]

            if temp_list is None or len(temp_list)== 0:
                element = doc.createElement(item[0])
                exec "element.appendChild(doc.createTextNode(str(%s)))"%temp_list
                root_node.appendChild(element)
            else:
                for value in temp_list:
                    element = doc.createElement(item[0])
                    exec "element.setAttribute(item[0], str(%s))"%value
                    root_node.appendChild(element)
       
        # Sample info
        sample = doc.createElement("SASsample")
        if datainfo.sample.name is not None:
            sample.setAttribute("name", str(datainfo.sample.name))
        entry_node.appendChild(sample)
        write_node(doc, sample, "ID", str(datainfo.sample.ID))
        write_node(doc, sample, "thickness", datainfo.sample.thickness, {"unit":datainfo.sample.thickness_unit})
        write_node(doc, sample, "transmission", datainfo.sample.transmission)
        write_node(doc, sample, "temperature", datainfo.sample.temperature, {"unit":datainfo.sample.temperature_unit})
        
        for item in datainfo.sample.details:
            write_node(doc, sample, "details", item)
        
        pos = doc.createElement("position")
        written = write_node(doc, pos, "x", datainfo.sample.position.x, {"unit":datainfo.sample.position_unit})
        written = written | write_node(doc, pos, "y", datainfo.sample.position.y, {"unit":datainfo.sample.position_unit})
        written = written | write_node(doc, pos, "z", datainfo.sample.position.z, {"unit":datainfo.sample.position_unit})
        if written == True:
            sample.appendChild(pos)
        
        ori = doc.createElement("orientation")
        written = write_node(doc, ori, "roll",  datainfo.sample.orientation.x, {"unit":datainfo.sample.orientation_unit})
        written = written | write_node(doc, ori, "pitch", datainfo.sample.orientation.y, {"unit":datainfo.sample.orientation_unit})
        written = written | write_node(doc, ori, "yaw",   datainfo.sample.orientation.z, {"unit":datainfo.sample.orientation_unit})
        if written == True:
            sample.appendChild(ori)
        
        # Instrument info
        instr = doc.createElement("SASinstrument")
        entry_node.appendChild(instr)
        
        write_node(doc, instr, "name", datainfo.instrument)
        
        #   Source
        source = doc.createElement("SASsource")
        if datainfo.source.name is not None:
            source.setAttribute("name", str(datainfo.source.name))
        instr.appendChild(source)
        
        write_node(doc, source, "radiation", datainfo.source.radiation)
        write_node(doc, source, "beam_shape", datainfo.source.beam_shape)
        size = doc.createElement("beam_size")
        if datainfo.source.beam_size_name is not None:
            size.setAttribute("name", str(datainfo.source.beam_size_name))
        written = write_node(doc, size, "x", datainfo.source.beam_size.x, {"unit":datainfo.source.beam_size_unit})
        written = written | write_node(doc, size, "y", datainfo.source.beam_size.y, {"unit":datainfo.source.beam_size_unit})
        written = written | write_node(doc, size, "z", datainfo.source.beam_size.z, {"unit":datainfo.source.beam_size_unit})
        if written == True:
            source.appendChild(size)
            
        write_node(doc, source, "wavelength", datainfo.source.wavelength, {"unit":datainfo.source.wavelength_unit})
        write_node(doc, source, "wavelength_min", datainfo.source.wavelength_min, {"unit":datainfo.source.wavelength_min_unit})
        write_node(doc, source, "wavelength_max", datainfo.source.wavelength_max, {"unit":datainfo.source.wavelength_max_unit})
        write_node(doc, source, "wavelength_spread", datainfo.source.wavelength_spread, {"unit":datainfo.source.wavelength_spread_unit})
        
        #   Collimation
        for item in datainfo.collimation:
            coll = doc.createElement("SAScollimation")
            if item.name is not None:
                coll.setAttribute("name", str(item.name))
            instr.appendChild(coll)
            
            write_node(doc, coll, "length", item.length, {"unit":item.length_unit})
            
            for apert in item.aperture:
                ap = doc.createElement("aperture")
                if apert.name is not None:
                    ap.setAttribute("name", str(apert.name))
                if apert.type is not None:
                    ap.setAttribute("type", str(apert.type))
                coll.appendChild(ap)
                
                write_node(doc, ap, "distance", apert.distance, {"unit":apert.distance_unit})
                
                size = doc.createElement("size")
                if apert.size_name is not None:
                    size.setAttribute("name", str(apert.size_name))
                written = write_node(doc, size, "x", apert.size.x, {"unit":apert.size_unit})
                written = written | write_node(doc, size, "y", apert.size.y, {"unit":apert.size_unit})
                written = written | write_node(doc, size, "z", apert.size.z, {"unit":apert.size_unit})
                if written == True:
                    ap.appendChild(size)

        #   Detectors
        for item in datainfo.detector:
            det = doc.createElement("SASdetector")
            written = write_node(doc, det, "name", item.name)
            written = written | write_node(doc, det, "SDD", item.distance, {"unit":item.distance_unit})
            written = written | write_node(doc, det, "slit_length", item.slit_length, {"unit":item.slit_length_unit})
            if written == True:
                instr.appendChild(det)
            
            off = doc.createElement("offset")
            written = write_node(doc, off, "x", item.offset.x, {"unit":item.offset_unit})
            written = written | write_node(doc, off, "y", item.offset.y, {"unit":item.offset_unit})
            written = written | write_node(doc, off, "z", item.offset.z, {"unit":item.offset_unit})
            if written == True:
                det.appendChild(off)
            
            center = doc.createElement("beam_center")
            written = write_node(doc, center, "x", item.beam_center.x, {"unit":item.beam_center_unit})
            written = written | write_node(doc, center, "y", item.beam_center.y, {"unit":item.beam_center_unit})
            written = written | write_node(doc, center, "z", item.beam_center.z, {"unit":item.beam_center_unit})
            if written == True:
                det.appendChild(center)
                
            pix = doc.createElement("pixel_size")
            written = write_node(doc, pix, "x", item.pixel_size.x, {"unit":item.pixel_size_unit})
            written = written | write_node(doc, pix, "y", item.pixel_size.y, {"unit":item.pixel_size_unit})
            written = written | write_node(doc, pix, "z", item.pixel_size.z, {"unit":item.pixel_size_unit})
            if written == True:
                det.appendChild(pix)
                
            ori = doc.createElement("orientation")
            written = write_node(doc, ori, "roll",  item.orientation.x, {"unit":item.orientation_unit})
            written = written | write_node(doc, ori, "pitch", item.orientation.y, {"unit":item.orientation_unit})
            written = written | write_node(doc, ori, "yaw",   item.orientation.z, {"unit":item.orientation_unit})
            if written == True:
                det.appendChild(ori)
                
        # Processes info
        for item in datainfo.process:
            node = doc.createElement("SASprocess")
            entry_node.appendChild(node)

            write_node(doc, node, "name", item.name)
            write_node(doc, node, "date", item.date)
            write_node(doc, node, "description", item.description)
            for term in item.term:
                value = term['value']
                del term['value']
                write_node(doc, node, "term", value, term)
            for note in item.notes:
                write_node(doc, node, "SASprocessnote", note)
        # Return the document, and the SASentry node associated with
        # the data we just wrote
        return doc, entry_node
   
    def _parse_state(self, entry, NODE_NAME= 'state'):
        """
        Read a fit result from an XML node
        
        :param entry: XML node to read from 
        
        :return: PageState object
        """
        # Create an empty state
        state = None   
        # Locate the P(r) node
        try:
            nodes = entry.xpath('ns:%s' % NODE_NAME, namespaces={'ns': STATE_NODE})
            if nodes !=[]:
                # Create an empty state
                state =  PageState()
                state.fromXML(node=nodes[0])
        except:
            logging.info("XML document does not contain fitting information.\n %s" % sys.exc_value)
            
        return state
    
   
                    
    def _parse_entry(self, dom):
        """
        Parse a SASentry
        
        :param node: SASentry node
        
        :return: Data1D/Data2D object
        
        """
        node = dom.xpath('ns:data_class', namespaces={'ns': STATE_NODE})
        if not node or node[0].text.lstrip().rstrip() != "Data2D":
            return CansasReader._parse_entry(self, dom)
        
        #Parse 2D
        data_info = Data2D()
        
        # Look up title      
        self._store_content('ns:Title', dom, 'title', data_info)
        
        # Look up run number   
        nodes = dom.xpath('ns:Run', namespaces={'ns': STATE_NODE})
        for item in nodes:    
            if item.text is not None:
                value = item.text.strip()
                if len(value) > 0:
                    data_info.run.append(value)
                    if item.get('name') is not None:
                        data_info.run_name[value] = item.get('name')
                           
        # Look up instrument name              
        self._store_content('ns:SASinstrument/ns:name', dom, 'instrument', data_info)

        # Notes
        note_list = dom.xpath('ns:SASnote', namespaces={'ns': STATE_NODE})
        for note in note_list:
            try:
                if note.text is not None:
                    note_value = note.text.strip()
                    if len(note_value) > 0:
                        data_info.notes.append(note_value)
            except:
                err_mess = "state_reader.read: error processing entry notes\n  %s" % sys.exc_value
                self.errors.append(err_mess)
                logging.error(err_mess)
        
        # Sample info ###################
        entry = get_content('ns:SASsample', dom)
        if entry is not None:
            data_info.sample.name = entry.get('name')
            
        self._store_content('ns:SASsample/ns:ID', 
                     dom, 'ID', data_info.sample)                    
        self._store_float('ns:SASsample/ns:thickness', 
                     dom, 'thickness', data_info.sample)
        self._store_float('ns:SASsample/ns:transmission', 
                     dom, 'transmission', data_info.sample)
        self._store_float('ns:SASsample/ns:temperature', 
                     dom, 'temperature', data_info.sample)
        
        nodes = dom.xpath('ns:SASsample/ns:details', namespaces={'ns': STATE_NODE})
        for item in nodes:
            try:
                if item.text is not None:
                    detail_value = item.text.strip()
                    if len(detail_value) > 0:
                        data_info.sample.details.append(detail_value)
            except:
                err_mess = "state_reader.read: error processing sample details\n  %s" % sys.exc_value
                self.errors.append(err_mess)
                logging.error(err_mess)
        
        # Position (as a vector)
        self._store_float('ns:SASsample/ns:position/ns:x', 
                     dom, 'position.x', data_info.sample)          
        self._store_float('ns:SASsample/ns:position/ns:y', 
                     dom, 'position.y', data_info.sample)          
        self._store_float('ns:SASsample/ns:position/ns:z', 
                     dom, 'position.z', data_info.sample)          
        
        # Orientation (as a vector)
        self._store_float('ns:SASsample/ns:orientation/ns:roll', 
                     dom, 'orientation.x', data_info.sample)          
        self._store_float('ns:SASsample/ns:orientation/ns:pitch', 
                     dom, 'orientation.y', data_info.sample)          
        self._store_float('ns:SASsample/ns:orientation/ns:yaw', 
                     dom, 'orientation.z', data_info.sample)          
       
        # Source info ###################
        entry = get_content('ns:SASinstrument/ns:SASsource', dom)
        if entry is not None:
            data_info.source.name = entry.get('name')
        
        self._store_content('ns:SASinstrument/ns:SASsource/ns:radiation', 
                     dom, 'radiation', data_info.source)                    
        self._store_content('ns:SASinstrument/ns:SASsource/ns:beam_shape', 
                     dom, 'beam_shape', data_info.source)                    
        self._store_float('ns:SASinstrument/ns:SASsource/ns:wavelength', 
                     dom, 'wavelength', data_info.source)          
        self._store_float('ns:SASinstrument/ns:SASsource/ns:wavelength_min', 
                     dom, 'wavelength_min', data_info.source)          
        self._store_float('ns:SASinstrument/ns:SASsource/ns:wavelength_max', 
                     dom, 'wavelength_max', data_info.source)          
        self._store_float('ns:SASinstrument/ns:SASsource/ns:wavelength_spread', 
                     dom, 'wavelength_spread', data_info.source)    
        
        # Beam size (as a vector)   
        entry = get_content('ns:SASinstrument/ns:SASsource/ns:beam_size', dom)
        if entry is not None:
            data_info.source.beam_size_name = entry.get('name')
            
        self._store_float('ns:SASinstrument/ns:SASsource/ns:beam_size/ns:x', 
                     dom, 'beam_size.x', data_info.source)    
        self._store_float('ns:SASinstrument/ns:SASsource/ns:beam_size/ns:y', 
                     dom, 'beam_size.y', data_info.source)    
        self._store_float('ns:SASinstrument/ns:SASsource/ns:beam_size/ns:z', 
                     dom, 'beam_size.z', data_info.source)    
        
        # Collimation info ###################
        nodes = dom.xpath('ns:SASinstrument/ns:SAScollimation', namespaces={'ns': STATE_NODE})
        for item in nodes:
            collim = Collimation()
            if item.get('name') is not None:
                collim.name = item.get('name')
            self._store_float('ns:length', item, 'length', collim)  
            
            # Look for apertures
            apert_list = item.xpath('ns:aperture', namespaces={'ns': STATE_NODE})
            for apert in apert_list:
                aperture =  Aperture()
                
                # Get the name and type of the aperture
                aperture.name = apert.get('name')
                aperture.type = apert.get('type')
                    
                self._store_float('ns:distance', apert, 'distance', aperture)    
                
                entry = get_content('ns:size', apert)
                if entry is not None:
                    aperture.size_name = entry.get('name')
                
                self._store_float('ns:size/ns:x', apert, 'size.x', aperture)    
                self._store_float('ns:size/ns:y', apert, 'size.y', aperture)    
                self._store_float('ns:size/ns:z', apert, 'size.z', aperture)
                
                collim.aperture.append(aperture)
                
            data_info.collimation.append(collim)
        
        # Detector info ######################
        nodes = dom.xpath('ns:SASinstrument/ns:SASdetector', namespaces={'ns': STATE_NODE})
        for item in nodes:
            
            detector = Detector()
            
            self._store_content('ns:name', item, 'name', detector)
            self._store_float('ns:SDD', item, 'distance', detector)    
            
            # Detector offset (as a vector)
            self._store_float('ns:offset/ns:x', item, 'offset.x', detector)    
            self._store_float('ns:offset/ns:y', item, 'offset.y', detector)    
            self._store_float('ns:offset/ns:z', item, 'offset.z', detector)    
            
            # Detector orientation (as a vector)
            self._store_float('ns:orientation/ns:roll',  item, 'orientation.x', detector)    
            self._store_float('ns:orientation/ns:pitch', item, 'orientation.y', detector)    
            self._store_float('ns:orientation/ns:yaw',   item, 'orientation.z', detector)    
            
            # Beam center (as a vector)
            self._store_float('ns:beam_center/ns:x', item, 'beam_center.x', detector)    
            self._store_float('ns:beam_center/ns:y', item, 'beam_center.y', detector)    
            self._store_float('ns:beam_center/ns:z', item, 'beam_center.z', detector)    
            
            # Pixel size (as a vector)
            self._store_float('ns:pixel_size/ns:x', item, 'pixel_size.x', detector)    
            self._store_float('ns:pixel_size/ns:y', item, 'pixel_size.y', detector)    
            self._store_float('ns:pixel_size/ns:z', item, 'pixel_size.z', detector)    
            
            self._store_float('ns:slit_length', item, 'slit_length', detector)
            
            data_info.detector.append(detector)    

        # Processes info ######################
        nodes = dom.xpath('ns:SASprocess', namespaces={'ns': STATE_NODE})
        for item in nodes:
            process = Process()
            self._store_content('ns:name', item, 'name', process)
            self._store_content('ns:date', item, 'date', process)
            self._store_content('ns:description', item, 'description', process)
            
            term_list = item.xpath('ns:term', namespaces={'ns': STATE_NODE})
            for term in term_list:
                try:
                    term_attr = {}
                    for attr in term.keys():
                        term_attr[attr] = term.get(attr).strip()
                    if term.text is not None:
                        term_attr['value'] = term.text.strip()
                        process.term.append(term_attr)
                except:
                    err_mess = "state_reader.read: error processing process term\n  %s" % sys.exc_value
                    self.errors.append(err_mess)
                    logging.error(err_mess)
            
            note_list = item.xpath('ns:SASprocessnote', namespaces={'ns': STATE_NODE})
            for note in note_list:
                if note.text is not None:
                    process.notes.append(note.text.strip())
            
            data_info.process.append(process)
            
            
        # Data info ######################
        nodes = dom.xpath('ns:SASdata', namespaces={'ns': STATE_NODE})
        if len(nodes)>1:
            raise RuntimeError, "CanSAS reader is not compatible with multiple SASdata entries"
       
        for entry in nodes:
            for item in list_of_data_2d_attr:
                #get node
                node = get_content('ns:%s'%item[0], entry)
                exec "data_info.%s = parse_entry_helper(node, item)"%(item[1])
                    
            for item in list_of_data2d_values:
                field = get_content('ns:%s'%item[0], entry)
                list = []
                if field is not None:
                    list = [parse_entry_helper(node, item) for node in field]
                exec "data_info.%s = numpy.array(list)"%item[0]
        
        return data_info

    def _read_cansas(self, path):
        """ 
        Load data and P(r) information from a CanSAS XML file.
        
        :param path: file path
        
        :return: Data1D object if a single SASentry was found, 
                    or a list of Data1D objects if multiple entries were found,
                    or None of nothing was found
                    
        :raise RuntimeError: when the file can't be opened
        :raise ValueError: when the length of the data vectors are inconsistent
        
        """
        output = []
        basename  = os.path.basename(path)
        root, extension = os.path.splitext(basename)
        ext = extension.lower()
        try:
            if os.path.isfile(path):
                
                #TODO: eventually remove the check for .xml once
                # the P(r) writer/reader is truly complete.
                if  ext in self.ext or \
                    ext == '.xml':
                    
                    tree = etree.parse(path, parser=etree.ETCompatXMLParser())
                    # Check the format version number
                    # Specifying the namespace will take care of the file format version 
                    root = tree.getroot()
                    entry_list = root.xpath('ns:SASentry', namespaces={'ns': STATE_NODE})
                    for entry in entry_list:   
                        try:
                            sas_entry = self._parse_entry(entry)
                        except:
                            raise
                        fitstate = self._parse_state(entry)
                        
                        #state could be None when .svs file is loaded
                        #in this case, skip appending to output
                        if fitstate != None:
                            sas_entry.meta_data['fitstate'] = fitstate
                            sas_entry.filename = fitstate.file
                            output.append(sas_entry)
            else:
                self.call_back(format=ext)
                raise RuntimeError, "%s is not a file" % path

            # Return output consistent with the loader's api
            if len(output)==0:
                self.call_back(state=None, datainfo=None,format=ext)
                return None
            else:
                for ind in range(len(output)):
                    # Call back to post the new state
                    state = output[ind].meta_data['fitstate']
                    t = time.localtime(state.timestamp)
                    time_str = time.strftime("%b %d %H:%M", t)
                    # Check that no time stamp is already appended
                    max_char = state.file.find("[")
                    if max_char < 0:
                        max_char = len(state.file)
                    original_fname = state.file[0:max_char]
                    state.file = original_fname +' [' + time_str + ']'
                   
                        
                    if state is not None and state.is_data is not None:
                        exec 'output[%d].is_data = state.is_data'% ind 
                     
                    output[ind].filename = state.file
                    state.data = output[ind]
                    state.data.name = output[ind].filename #state.data_name
                    state.data.id = state.data_id
                    if state.is_data is not None:
                        state.data.is_data = state.is_data
                    if output[ind].run_name is not None and\
                        len(output[ind].run_name) != 0 :
                        name = output[ind].run_name
                    else: 
                        name=original_fname
                    state.data.group_id = name
                    #store state in fitting
                    self.call_back(state=state, datainfo=output[ind],format=ext)
                    self.state= state
                return output
              
        except:
            #self.call_back(format=ext)
            self.state= state
            raise
           
    def write(self, filename, datainfo=None, fitstate=None):
        """
        Write the content of a Data1D as a CanSAS XML file only for standalone
        
        :param filename: name of the file to write
        :param datainfo: Data1D object
        :param fitstate: PageState object
        
        """
        # Sanity check
        if self.cansas == True:
            
            # Add fitting information to the XML document
            doc = self.write_toXML(datainfo, fitstate)
            # Write the XML document
            fd = open(filename, 'w')
            fd.write(doc.toprettyxml())
            fd.close()
        else:
            fitstate.toXML(file=filename)
        
    def write_toXML(self, datainfo=None, state=None):
        """
        Write toXML, a helper for write() , could be used by guimanager._on_save()
        
        : return: xml doc
        """

        if state.data is None:
            data = Data2D()  
        else:  
            #make sure title and data run is filled up.
            if state.data.title == None or state.data.title=='':
                 state.data.title = state.data.name
            if state.data.run_name == None or state.data.run_name=={}: 
                state.data.run = [str(state.data.name)]
                state.data.run_name[0] = state.data.name
            doc, sasentry = self._to_xml_doc(data)
           

        if state is not None:
            state.toXML(doc=doc, file=data.name, entry_node=sasentry)
            
        return doc 
  
if __name__ == "__main__":
    state = PageState(parent=None)
    #state.toXML()
    """
    
    file = open("test_state", "w")
    pickle.dump(state, file)
    print pickle.dumps(state)
    state.data_name = "hello---->"
    pickle.dump(state, file)
    file = open("test_state", "r")
    new_state= pickle.load(file)
    print "new state", new_state
    new_state= pickle.load(file)
    print "new state", new_state
    #print "state", state
    """
    import bsddb
    import pickle
    db= bsddb.btopen('file_state.db', 'c')
    val = (pickle.dumps(state), "hello", "hi")
    db['state1']= pickle.dumps(val)
    print pickle.loads(db['state1'])
    state.data_name = "hello---->22"
    db['state2']= pickle.dumps(state)
    state.data_name = "hello---->2"
    db['state3']= pickle.dumps(state)
    del db['state3']
    state.data_name = "hello---->3"
    db['state4']= pickle.dumps(state)
    new_state = pickle.loads(db['state1'])
    #print db.last()
    db.set_location('state2')
    state.data_name = "hello---->5"
    db['aastate5']= pickle.dumps(state)
    db.keys().sort()
    print pickle.loads(db['state2'])
  
    db.close() 

    logging.basicConfig(level=logging.ERROR,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='state_reader.log',
                        filemode='w')
    reader = Reader()
    print reader.read("../test/cansas1d.xml")
    #print reader.read("../test/latex_smeared.xml")
    
    
                        