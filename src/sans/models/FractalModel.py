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
   src\sans\models\include\fractal.h
   AND RE-RUN THE GENERATOR SCRIPT
"""

from sans.models.BaseComponent import BaseComponent
from sans.models.sans_extension.c_models import CFractalModel

def create_FractalModel():
    """
       Create a model instance
    """
    obj = FractalModel()
    # CFractalModel.__init__(obj) is called by
    # the FractalModel constructor
    return obj

class FractalModel(CFractalModel, BaseComponent):
    """ 
    Class that evaluates a FractalModel model. 
    This file was auto-generated from src\sans\models\include\fractal.h.
    Refer to that file and the structure it contains
    for details of the model.
    
    List of default parameters:

    * radius          = 5.0 [A]
    * scale           = 0.05 
    * fractal_dim     = 2.0 
    * cor_length      = 100.0 [A]
    * sldBlock        = 2e-06 [1/A^(2)]
    * sldSolv         = 6.35e-06 [1/A^(2)]
    * background      = 0.0 [1/cm]

    """
        
    def __init__(self, multfactor=1):
        """ Initialization """
        self.__dict__ = {}
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        #apply(CFractalModel.__init__, (self,)) 

        CFractalModel.__init__(self)
        self.is_multifunc = False
		        
        ## Name of the model
        self.name = "FractalModel"
        ## Model description
        self.description = """
         The scattering intensity  I(x) = P(|x|)*S(|x|) + background, where
		p(x)= scale * V * delta^(2)* F(x*radius)^(2)
		F(x) = 3*[sin(x)-x cos(x)]/x**3
		where delta = sldBlock -sldSolv.
		scale        =  scale factor * Volume fraction
		radius       =  Block radius
		fractal_dim  =  Fractal dimension
		cor_length  =  Correlation Length
		sldBlock    =  SDL block
		sldSolv  =  SDL solvent
		background   =  background
        """
       
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['radius'] = ['[A]', None, None]
        self.details['scale'] = ['', None, None]
        self.details['fractal_dim'] = ['', None, None]
        self.details['cor_length'] = ['[A]', None, None]
        self.details['sldBlock'] = ['[1/A^(2)]', None, None]
        self.details['sldSolv'] = ['[1/A^(2)]', None, None]
        self.details['background'] = ['[1/cm]', None, None]

        ## fittable parameters
        self.fixed = []
        
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
        return (create_FractalModel, tuple(), state, None, None)
        
    def clone(self):
        """ Return a identical copy of self """
        return self._clone(FractalModel())   
       	
    def run(self, x=0.0):
        """ 
        Evaluate the model
        
        :param x: input q, or [q,phi]
        
        :return: scattering function P(q)
        
        """
        return CFractalModel.run(self, x)
   
    def runXY(self, x=0.0):
        """ 
        Evaluate the model in cartesian coordinates
        
        :param x: input q, or [qx, qy]
        
        :return: scattering function P(q)
        
        """
        return CFractalModel.runXY(self, x)
        
    def evalDistribution(self, x):
        """ 
        Evaluate the model in cartesian coordinates
        
        :param x: input q[], or [qx[], qy[]]
        
        :return: scattering function P(q[])
        
        """
        return CFractalModel.evalDistribution(self, x)
        
    def calculate_ER(self):
        """ 
        Calculate the effective radius for P(q)*S(q)
        
        :return: the value of the effective radius
        
        """       
        return CFractalModel.calculate_ER(self)
        
    def calculate_VR(self):
        """ 
        Calculate the volf ratio for P(q)*S(q)
        
        :return: the value of the volf ratio
        
        """       
        return CFractalModel.calculate_VR(self)
              
    def set_dispersion(self, parameter, dispersion):
        """
        Set the dispersion object for a model parameter
        
        :param parameter: name of the parameter [string]
        :param dispersion: dispersion object of type DispersionModel
        
        """
        return CFractalModel.set_dispersion(self,
               parameter, dispersion.cdisp)
        
   
# End of file

