class MoosasMap
    p 'MoosasMap Ver.0.6.1'

    class << self
        attr_reader :dialog
    end

    @dialog = UI::HtmlDialog.new({
        :dialog_title => "MOOSAS地图数据",
        :preferences_key => "MoosasMap",
        :scrollable => false,
        :resizable => false,
        :width =>  1150,
        :height => 920,
        :left => 50,
        :top => 50,
        :min_width => 50,
        :min_height => 50,
        :style => UI::HtmlDialog::STYLE_DIALOG
    })


    def self.show_ui()

        @dialog.set_file("http://www.moosas.cn/3dmap/skp")

        @dialog.add_action_callback("importUrbanBldsData") { |action_context,json_data|
            p "importUrbanBldsData"
            #p json_data
            MoosasUrban.load_osm_building_from_json(json_data)
        }

        MoosasUtils.is_unix ? @dialog.show_modal : @dialog.show

    end

    def self.get_long_value(element_id)
        return @dialog.get_element_value(element_id)
    end


end
