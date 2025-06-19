
#模型识别模块
module MPath
    BASE = File.absolute_path(File.dirname(__FILE__)+"/../")+"/"
    LIB =BASE+"libs/"
    DATA = BASE+"data/"
    DB = BASE+"db/"
    TEMP = BASE+"__temp__/"
    PYTHON = BASE+"python/"
    ENERGY_PUBLIC = LIB+"energy/MoosasEnergyPublic.exe"
    ENERGY_RES = LIB+"energy/MoosasEnergyResidential.exe"
    UI = LIB + "ui/"
    RAD = LIB + "rad/"
    VENT = LIB + "vent/"
    WEATHER = DB + "weather/"
    SKY = DB + "cum_sky/"
end
