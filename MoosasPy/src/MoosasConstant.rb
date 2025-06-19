
module MoosasConstant
    p 'MoosasConstant Ver.0.6.1'


    PLUGIN_MENU_STRING ="Moosas"

    PLUGIN_DEBUG = true

    PAYLOAD_DELIMITER = "|"
    PAYLOAD_PARAMS_DELIMITER = "~"

    WIN_UI_WIDTH = 2000
    WIN_UI_HEIGHT = 2000
    WIN_REPORT_UI_WIDTH = 600
    WIN_REPORT_UI_HEIGHT = 800

    MAC_UI_WIDTH  = 800
    MAC_UI_HEIGHT   = 900
    MAC_REPORT_UI_WIDTH  = 600
    MAC_REPORT_UI_HEIGHT = 800

    UI_X = 1100
    UI_Y = 100


    INCH_METER_MULTIPLIER = 0.0254
    INCH_METER_MULTIPLIER_SQR = 0.0254 * 0.0254
    MATERIAL_ALPHA_THRESHOLD = 0.99


    ENTITY_WALL             = 0
    ENTITY_INTERNAL_WALL    = 3
    ENTITY_GLAZING          = 1
    ENTITY_INTERNAL_GLAZING = 5
    ENTITY_SKY_GLAZING      = 6
    ENTITY_ROOF             = 2
    ENTITY_FLOOR            = 4
    ENTITY_GROUND_FLOOR     = 8
    ENTITY_SHADING          = 16
    ENTITY_PARTY_WALL       = 32
    ENTITY_DOOR             = 64
    ENTITY_IGNORE           = -2
    ENTITY_SURROUNDING      = -1

    ORIENTATION_SOUTH = 0
    ORIENTATION_WEST = 1
    ORIENTATION_NORTH = 2
    ORIENTATION_EAST = 3
    ORIENTATION_ROOF = 4
    ORIENTATION_ALL = 8

end

#全局变量，存储模型
$current_model = nil
$model_updated_number = 0 #标志模型识别的顺序号
$rad_lib = nil
$energy_lib = nil
#$language = 'Chinese'
if $language == 'Chinese'
    $ui_settings ={
            "selectCity"=>"545110",
            "selectBuildingType"=>"居住建筑",
            "selectStandard"=>"近零能耗建筑技术标准 GB/T 51350-2019",
            "recognize"=>true,
            "radiation"=>true
        }
else
    $ui_settings ={
            "selectCity"=>"545110",
            "selectBuildingType"=>"Residence",
            "selectStandard"=>"GB/T 51350-2019", # Technical standard for nearly zero energy buildings 
            "recognize"=>true,
            "radiation"=>true
        }
end
$template = nil
$weather = nil

