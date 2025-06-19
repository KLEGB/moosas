class MoosasNanji
    Ver='0.0.0'
    class << self
    end

    def self.input_box

        prompts = ["人员密度:","新风量:","灯光密度:","设备能耗密度:","室外平均温度:","极端低温:","大风天气:","太阳辐射:","有效天空温度:","极昼极夜现象:","降雨量:"]
        defaults = ["","","","","","","","","","",""]
        input = UI.inputbox(prompts, defaults, "请输入南极气候参数和建筑内扰")
    end

end