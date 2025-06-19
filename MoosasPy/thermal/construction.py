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
        UFactor = float(UFactor)
        if _type == 'window':
            SHGC = .48 if SHGC is None else SHGC
            layer = MoosasSettings(glzDefault, UFactor=np.round(UFactor,2), Name='g_' + generate_code(4),Solar_Heat_Gain_Coefficient=SHGC)
        else:
            layer = MoosasSettings(opaqueMassDefault, Conductivity=np.round(UFactor*0.1,2), Name='m_' + generate_code(4))
        return cls(layer)

    @classmethod
    def fromIDFConstructionList(cls,idf,idfObject):
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
        super().applyToIDF(idf, rename)
        for layer in self.layers:
            layer.applyToIDF(idf, rename)
