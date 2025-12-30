from .settings import MoosasSettings
from ..utils import generate_code,np

glzDefault = {
    'key': 'WindowMaterial:SimpleGlazingSystem',
    'Name': 'Gls_Simple',
    'UFactor': 1.4,  # W/m2-k
    'Solar_Heat_Gain_Coefficient': .48,  # SHGC
    'Visible_Transmittance': .744  # VLT
}
opaqueMassDefault = {
    'key': 'Material',
    'Name': 'Mass_Simple',
    'Roughness':'Rough',
    'Thickness': .1,  # m
    'Conductivity': .05,  # W/m-k
    'Density': 2400,  # kg/m3
    'Specific_Heat': 1400,  # J/kg-K
    'Thermal_Absorptance': .9,
    'Solar_Absorptance': .6,
    'Visible_Absorptance': .6,
}
constructionDefault = {
    'key': 'Construction',
    'Name':'',
    'Outside_Layer': ''
}


class Construction(MoosasSettings):
    __slot__ = ['layers', 'UFactor', 'type']

    def __init__(self, *layers: MoosasSettings, _name=None):
        """
        Initialize a new instance with given layers and optional name.
        
        Parameters
        ----------
        layers : MoosasSettings
            Variable number of MoosasSettings instances representing the layers.
            At least one layer must be provided.
        _name : str, optional
            Name to assign to the instance. If not provided, a 4-character 
            alphanumeric code is generated automatically.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
        self.layers = layers
        if 'Window' in layers[0].params['key'] or 'WINDOW' in layers[0].params['key']:
            self.type = 'window'
        else:
            self.type = 'opaque'
        _name = str(generate_code(4)) if _name is None else _name
        super().__init__(constructionDefault, Name=_name, Outside_Layer=layers[0].params['Name'])
        if len(layers) > 1:
            for lay in range(1, len(layers)):
                self.params[f'Layer_{lay + 1}'] = layers[lay].params['Name']
        if self.type == 'window':
            self.UFactor = layers[0].params['UFactor']
        else:
            try:
                RValue = sum([lay.params['Thickness'] / lay.params['Conductivity'] for lay in self.layers])
            except:
                raise Exception(self.layers)
            self.UFactor = 1 / RValue

    @classmethod
    def create(cls, _type, UFactor,SHGC=None):
        """
        Create a MoosasSettings instance based on the specified type and U-factor.
        
        Parameters
        ----------
        cls : type
            The class invoking the method (used for returning an instance of the class).
        _type : str
            The type of element to create; either 'window' or another type for opaque materials.
        UFactor : float or str
            The U-factor value; will be converted to float and rounded to 2 decimal places.
        SHGC : float, optional
            Solar Heat Gain Coefficient, required only for 'window' type. 
            Defaults to 0.48 if not provided and _type is 'window'.
        
        Returns
        -------
        object
            An instance of cls initialized with the created MoosasSettings layer.
        """
        UFactor = float(UFactor)
        if _type == 'window':
            SHGC = .48 if SHGC is None else SHGC
            layer = MoosasSettings(glzDefault, UFactor=np.round(UFactor,2), Name='g_' + generate_code(4),Solar_Heat_Gain_Coefficient=SHGC)
        else:
            layer = MoosasSettings(opaqueMassDefault, Conductivity=np.round(UFactor*0.1,2), Name='m_' + generate_code(4))
        return cls(layer)

    @classmethod
    def fromIDFConstructionList(cls,idf,idfObject):
        """
        Create a class instance from an IDF construction list.
        
        Parameters
        ----------
        idf : IDF
            The IDF object containing the building energy model data.
        idfObject : IDFSurfaceObject
            The IDF object representing the construction to be processed.
        
        Returns
        -------
        cls or None
            An instance of the class constructed from the provided IDF construction list,
            or None if any layer material cannot be found or is invalid.
        """
        cons = MoosasSettings.fromIdfObject(idfObject)
        # searching the layer objects
        outLayer = cons.params['Outside_Layer']
        for glsMaterial in idf.idfobjects['WindowMaterial:SimpleGlazingSystem']:
            if glsMaterial.Name == outLayer:
                outLayer = glsMaterial
                return cls(MoosasSettings.fromIdfObject(outLayer),_name=cons.params['Name'])
        layers = [outLayer]
        for i in range(2,10):
            if 'Layer_' + str(i) in cons.params.keys():
                if cons.params['Layer_' + str(i)] != '':
                    layers.append(cons.params['Layer_' + str(i)])
        for opaqueMaterial in idf.idfobjects['Material']:
            for j in range(len(layers)):
                if opaqueMaterial.Name == layers[j]:
                    layers[j] = opaqueMaterial
        for l in layers:
            if isinstance(l,str):
                return None
        return cls(*[MoosasSettings.fromIdfObject(l) for l in layers],_name=cons.params['Name'])


    def applyToIDF(self, idf, rename: dict = None):
        """
        Apply modifications to the IDF object and propagate to all layers.
        
        Parameters
        ----------
        idf : IDFSurface
            The IDF surface object to which modifications are applied.
        rename : dict, optional
            A dictionary mapping old names to new names for renaming references in the IDF.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        super().applyToIDF(idf, rename)
        for layer in self.layers:
            layer.applyToIDF(idf, rename)

airBoundaryDefault ={
    'key': "Construction:AirBoundary",
    "Name": "Generic Air Boundary"
}