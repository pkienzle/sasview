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
   src\sans\models\include\SquareWell.h
   AND RE-RUN THE GENERATOR SCRIPT
"""

from sans.models.BaseComponent import BaseComponent
from sans.models.sans_extension.c_models import CSquareWellStructure

def create_SquareWellStructure():
    """
       Create a model instance
    """
    obj = SquareWellStructure()
    # CSquareWellStructure.__init__(obj) is called by
    # the SquareWellStructure constructor
    return obj

class SquareWellStructure(CSquareWellStructure, BaseComponent):
    """ 
    Class that evaluates a SquareWellStructure model. 
    This file was auto-generated from src\sans\models\include\SquareWell.h.
    Refer to that file and the structure it contains
    for details of the model.
    
    List of default parameters:

    * effect_radius   = 50.0 [A]
    * volfraction     = 0.04 
    * welldepth       = 1.5 [kT]
    * wellwidth       = 1.2 

    """
        
    def __init__(self, multfactor=1):
        """ Initialization """
        self.__dict__ = {}
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        #apply(CSquareWellStructure.__init__, (self,)) 

        CSquareWellStructure.__init__(self)
        self.is_multifunc = False
		        
        ## Name of the model
        self.name = "SquareWellStructure"
        ## Model description
        self.description = """
         Structure Factor for interacting particles:             .
		
		The interaction potential is
		
		U(r)= inf   , r < 2R
		= -d    , 2R <= r <=2Rw
		= 0     , r >= 2Rw
		
		R: effective radius (A)of the particle
		v: volume fraction
		d: well depth
		w: well width; multiples of the
		particle diameter
		
		Ref: Sharma, R. V.; Sharma,
		K. C., Physica, 1977, 89A, 213.
        """
       
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['effect_radius'] = ['[A]', None, None]
        self.details['volfraction'] = ['', None, None]
        self.details['welldepth'] = ['[kT]', None, None]
        self.details['wellwidth'] = ['', None, None]

        ## fittable parameters
        self.fixed = ['effect_radius.width']
        
        ## non-fittable parameters
        self.non_fittable = []
        
        ## parameters with orientation
        self.orientation_params = []

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
        return (create_SquareWellStructure, tuple(), state, None, None)
        
    def clone(self):
        """ Return a identical copy of self """
        return self._clone(SquareWellStructure())   
       	
    def run(self, x=0.0):
        """ 
        Evaluate the model
        
        :param x: input q, or [q,phi]
        
        :return: scattering function P(q)
        
        """
        return CSquareWellStructure.run(self, x)
   
    def runXY(self, x=0.0):
        """ 
        Evaluate the model in cartesian coordinates
        
        :param x: input q, or [qx, qy]
        
        :return: scattering function P(q)
        
        """
        return CSquareWellStructure.runXY(self, x)
        
    def evalDistribution(self, x):
        """ 
        Evaluate the model in cartesian coordinates
        
        :param x: input q[], or [qx[], qy[]]
        
        :return: scattering function P(q[])
        
        """
        return CSquareWellStructure.evalDistribution(self, x)
        
    def calculate_ER(self):
        """ 
        Calculate the effective radius for P(q)*S(q)
        
        :return: the value of the effective radius
        
        """       
        return CSquareWellStructure.calculate_ER(self)
        
    def calculate_VR(self):
        """ 
        Calculate the volf ratio for P(q)*S(q)
        
        :return: the value of the volf ratio
        
        """       
        return CSquareWellStructure.calculate_VR(self)
              
    def set_dispersion(self, parameter, dispersion):
        """
        Set the dispersion object for a model parameter
        
        :param parameter: name of the parameter [string]
        :param dispersion: dispersion object of type DispersionModel
        
        """
        return CSquareWellStructure.set_dispersion(self,
               parameter, dispersion.cdisp)
        
   
# End of file

