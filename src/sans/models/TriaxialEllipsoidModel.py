##############################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
#
# If you use DANSE applications to do scientific research that leads to
# publication, we ask that you acknowledge the use of the software with the
# following sentence:
#
# This work benefited from DANSE software developed under NSF award DMR-0520547
#
# Copyright 2008-2011, University of Tennessee
##############################################################################

""" 
Provide functionality for a C extension model

.. WARNING::

   THIS FILE WAS GENERATED BY WRAPPERGENERATOR.PY
   DO NOT MODIFY THIS FILE, MODIFY
   src\sans\models\include\triaxial_ellipsoid.h
   AND RE-RUN THE GENERATOR SCRIPT
"""

from sans.models.BaseComponent import BaseComponent
from sans.models.sans_extension.c_models import CTriaxialEllipsoidModel

def create_TriaxialEllipsoidModel():
    """
       Create a model instance
    """
    obj = TriaxialEllipsoidModel()
    # CTriaxialEllipsoidModel.__init__(obj) is called by
    # the TriaxialEllipsoidModel constructor
    return obj

class TriaxialEllipsoidModel(CTriaxialEllipsoidModel, BaseComponent):
    """ 
    Class that evaluates a TriaxialEllipsoidModel model. 
    This file was auto-generated from src\sans\models\include\triaxial_ellipsoid.h.
    Refer to that file and the structure it contains
    for details of the model.
    
    List of default parameters:

    * scale           = 1.0 
    * semi_axisA      = 35.0 [A]
    * semi_axisB      = 100.0 [A]
    * semi_axisC      = 400.0 [A]
    * sldEll          = 1e-06 [1/A^(2)]
    * sldSolv         = 6.3e-06 [1/A^(2)]
    * background      = 0.0 [1/cm]
    * axis_theta      = 57.325 [deg]
    * axis_phi        = 57.325 [deg]
    * axis_psi        = 0.0 [deg]

    """
        
    def __init__(self, multfactor=1):
        """ Initialization """
        self.__dict__ = {}
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        #apply(CTriaxialEllipsoidModel.__init__, (self,)) 

        CTriaxialEllipsoidModel.__init__(self)
        self.is_multifunc = False
		        
        ## Name of the model
        self.name = "TriaxialEllipsoidModel"
        ## Model description
        self.description = """
        Note: During fitting ensure that the inequality A<B<C is not
		violated. Otherwise the calculation will
		not be correct.
        """
       
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale'] = ['', None, None]
        self.details['semi_axisA'] = ['[A]', None, None]
        self.details['semi_axisB'] = ['[A]', None, None]
        self.details['semi_axisC'] = ['[A]', None, None]
        self.details['sldEll'] = ['[1/A^(2)]', None, None]
        self.details['sldSolv'] = ['[1/A^(2)]', None, None]
        self.details['background'] = ['[1/cm]', None, None]
        self.details['axis_theta'] = ['[deg]', None, None]
        self.details['axis_phi'] = ['[deg]', None, None]
        self.details['axis_psi'] = ['[deg]', None, None]

        ## fittable parameters
        self.fixed = ['axis_psi.width',
                      'axis_phi.width',
                      'axis_theta.width',
                      'semi_axisA.width',
                      'semi_axisB.width',
                      'semi_axisC.width']
        
        ## non-fittable parameters
        self.non_fittable = []
        
        ## parameters with orientation
        self.orientation_params = ['axis_psi',
                                   'axis_phi',
                                   'axis_theta',
                                   'axis_psi.width',
                                   'axis_phi.width',
                                   'axis_theta.width']

        ## parameters with magnetism
        self.magnetic_params = []

        self.category = None
        self.multiplicity_info = None
        
    def __setstate__(self, state):
        """
        restore the state of a model from pickle
        """
        self.__dict__, self.params, self.dispersion = state
        
    def __reduce_ex__(self, proto):
        """
        Overwrite the __reduce_ex__ of PyTypeObject *type call in the init of 
        c model.
        """
        state = (self.__dict__, self.params, self.dispersion)
        return (create_TriaxialEllipsoidModel, tuple(), state, None, None)
        
    def clone(self):
        """ Return a identical copy of self """
        return self._clone(TriaxialEllipsoidModel())   
       	
    def run(self, x=0.0):
        """ 
        Evaluate the model
        
        :param x: input q, or [q,phi]
        
        :return: scattering function P(q)
        
        """
        return CTriaxialEllipsoidModel.run(self, x)
   
    def runXY(self, x=0.0):
        """ 
        Evaluate the model in cartesian coordinates
        
        :param x: input q, or [qx, qy]
        
        :return: scattering function P(q)
        
        """
        return CTriaxialEllipsoidModel.runXY(self, x)
        
    def evalDistribution(self, x):
        """ 
        Evaluate the model in cartesian coordinates
        
        :param x: input q[], or [qx[], qy[]]
        
        :return: scattering function P(q[])
        
        """
        return CTriaxialEllipsoidModel.evalDistribution(self, x)
        
    def calculate_ER(self):
        """ 
        Calculate the effective radius for P(q)*S(q)
        
        :return: the value of the effective radius
        
        """       
        return CTriaxialEllipsoidModel.calculate_ER(self)
        
    def calculate_VR(self):
        """ 
        Calculate the volf ratio for P(q)*S(q)
        
        :return: the value of the volf ratio
        
        """       
        return CTriaxialEllipsoidModel.calculate_VR(self)
              
    def set_dispersion(self, parameter, dispersion):
        """
        Set the dispersion object for a model parameter
        
        :param parameter: name of the parameter [string]
        :param dispersion: dispersion object of type DispersionModel
        
        """
        return CTriaxialEllipsoidModel.set_dispersion(self,
               parameter, dispersion.cdisp)
        
   
# End of file

