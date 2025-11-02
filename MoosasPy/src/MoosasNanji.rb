class MoosasNanji
    Ver='0.0.0'
    class << self
    end

    def self.input_box
    # Function:
    # Displays an input dialog box to collect climate and internal load parameters for Antarctic building conditions.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # Array: An array of strings containing user-input values corresponding to the following prompts:
    # - "人员密度:" (Occupant density)
    # - "新风量:" (Fresh air volume)
    # - "灯光密度:" (Lighting density)
    # - "设备能耗密度:" (Equipment energy consumption density)
    # - "室外平均温度:" (Average outdoor temperature)
    # - "极端低温:" (Extreme low temperature)
    # - "大风天气:" (High wind conditions)
    # - "太阳辐射:" (Solar radiation)
    # - "有效天空温度:" (Effective sky temperature)
    # - "极昼极夜现象:" (Polar day and night phenomenon)
    # - "降雨量:" (Precipitation)
    # Returns nil if the user cancels the input dialog.

        prompts = ["人员密度:","新风量:","灯光密度:","设备能耗密度:","室外平均温度:","极端低温:","大风天气:","太阳辐射:","有效天空温度:","极昼极夜现象:","降雨量:"]
        defaults = ["","","","","","","","","","",""]
        input = UI.inputbox(prompts, defaults, "请输入南极气候参数和建筑内扰")
    end

end