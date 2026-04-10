
#模型识别模块
module MPath
    BASE = File.absolute_path(File.dirname(__FILE__)+"/../")+"/"
    LIB =BASE+"libs/"
    DATA = BASE+"data/"
    DB = BASE+"db/"
    TEMP = BASE+"__temp__/"
    PYTHON = BASE+"python/"
    EXE_SUFFIX = Gem.win_platform? ? ".exe" : ""
    ENERGY_PUBLIC = LIB+"energy/MoosasEnergyPublic"+EXE_SUFFIX
    ENERGY_RES = LIB+"energy/MoosasEnergyResidential"+EXE_SUFFIX
    UI = LIB + "ui/"
    RAD = LIB + "rad/"
    VENT = LIB + "vent/"
    WEATHER = DB + "weather/"
    SKY = DB + "cum_sky/"
end
