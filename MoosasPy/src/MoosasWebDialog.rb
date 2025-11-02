
class MoosasWebDialog
    Ver='0.6.3'
    class << self
        attr_reader :dialog
    end


    VIEW_FOLDER = MPath::UI
    if $language == 'Chinese'
        PLUGIN_MAIN_PAGE_URL = VIEW_FOLDER + "/main.htm"
    else
        PLUGIN_MAIN_PAGE_URL = VIEW_FOLDER + "/main_english.htm"
    end

    @width = MoosasUtils.is_unix() == true ? MoosasConstant::MAC_UI_WIDTH : MoosasConstant::WIN_UI_WIDTH
    @height = MoosasUtils.is_unix() == true ? MoosasConstant::MAC_UI_HEIGHT : MoosasConstant::WIN_UI_HEIGHT
    @dialog = UI::HtmlDialog.new(
        {
          :dialog_title => "MOOSAS Ver.0.6.1",
          :preferences_key => "PkpmMoosasPlugin",
          :scrollable => true,
          :resizable => true,
          :width =>  @width,
          :height => @height,
          :left => MoosasConstant::UI_X,
          :top => MoosasConstant::UI_Y,
          :min_width => 50,
          :min_height => 50,
          :max_width =>2000,
          :max_height => 2000,
          :style => UI::HtmlDialog::STYLE_DIALOG
    })
    @dialog.set_file(PLUGIN_MAIN_PAGE_URL)
    @long_message = nil  #用于传递‘大’数据

    def self.show_ui(tab=nil)
    # """
    # Function
    # --------
    # Displays the user interface dialog and initializes related components, including action callbacks and weather data reset.
    # Optionally navigates to a specified tab if provided.
    # 
    # Parameters
    # ----------
    # tab : str or nil, optional
    # The name of the tab to display after showing the UI. If nil, no tab is selected automatically. Default is nil.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It performs side effects such as displaying the UI dialog, setting up callbacks,
    # and optionally switching to a specified tab.
    # """
        p "Expired after: #{MoosasLock.remain_time()} days"

        @dialog.add_action_callback("call") { |action_context, param1|
            receive(param1.to_s)
        }

        @dialog.add_action_callback("longMessage") { |action_context, param1|
            @long_message = param1
            p @long_message
        }

        #@dialog.set_size(@width,@height)
        MoosasUtils.is_unix ? @dialog.show_modal : @dialog.show
        #@dialog.set_position(MoosasConstant::UI_X,MoosasConstant::UI_Y)
        MoosasWeather.reset_weather_data_to_ui()
        if tab!=nil
            self.send("show_tab",tab)
        end
    end

    def self.get_long_value(element_id)
    # """
    # Function
    # --------
    # Retrieves the long value of a specified element from the dialog.
    # 
    # Parameters
    # ----------
    # element_id : int or string
    # The identifier of the element whose value is to be retrieved.
    # 
    # Returns
    # -------
    # int or nil
    # The long integer value of the specified element, or nil if the element
    # does not exist or no value is set.
    # """
        return @dialog.get_element_value(element_id)
    end


    def self.receive(message)
    # """
    # Function
    # --------
    # Processes an incoming message from a web interface and executes corresponding commands
    # based on the command type. This method acts as a router for various application-level
    # operations such as analysis, rendering, model manipulation, and settings update.
    # 
    # Parameters
    # ----------
    # message : str
    # A string message received from the web dialog, formatted as a command followed by
    # optional parameters, separated by the payload delimiter (`|`). The first part is
    # the command name; subsequent parts contain parameter data, often in JSON or
    # key-value format.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It performs side effects such as triggering
    # analyses, updating UI states, modifying model data, or sending responses back to
    # the web interface. If the Moosas utility is not active, the method returns early
    # with no action.
    # """
        return unless MoosasUtils.moosas_active?
        
        #p "收到来自HTML的指令: "+message
        p "收到来自HTML的指令: "+message.split('|')[0]

        array = message.split(MoosasConstant::PAYLOAD_DELIMITER)
        command = array[0]
        ori_params = array[1]
        params = array[1]==nil ? []: array[1].split(MoosasConstant::PAYLOAD_PARAMS_DELIMITER)


        case command
        when "main_analysis"
            params[0]=params[0].delete("\"").delete("{").delete("}")
            param={}
            params[0].split(",").each{|par| param[par.split(":")[0]]=par.split(":")[1]}
            #p param
            MoosasAnalysis.main_analysis(param["recognize"], param["selectBuildingType"],param["radiation"])
        when "recognize_model"
            model = MMR.recognize_floor(remodel=true)
        when "reset_ui_data"
            MoosasWeather.reset_weather_data_to_ui
            MoosasMeta.reset_saved_data
            self.send("reset_ui",$ui_settings) 
        when "render_daylight_in_skp_btn"
            MoosasDaylight.render_daylight_in_skp
        when "optmize_energy"
            if $current_model  == nil
                UI.messagebox("请先选择并识别一个建筑形体!")
                return
            end
            setting = JSON.parse(params[0])
            $moosas_energy_ga = GA.new(setting['optimizer'],setting['num_parameters'], setting['x_bounds'], setting['population_size'])
            $moosas_energy_ga.set_webdialog(self)
            $moosas_energy_ga.init
        when "update_optimize_energy"
            $moosas_energy_ga.update_generation() if $moosas_energy_ga != nil
        when "params_analysis"
            param = JSON.parse(params[0])
            type = param["type"]
            MoosasAnalysis.params_analysis(type, [param])
        when "multi_goal_params_analysis"
            param = JSON.parse(params[0])
            type = param["type"]
            MoosasAnalysis.multi_goal_params_analysis(type, [param])   
        when "update_parameter_setting"
            MoosasAnalysis.update_moosas_model_parameters_setting(params[0],params[1])
        when "visualize_entity_type"
            if $current_model == nil
                return 
            end
            MoosasRender.visualize_entity_type($current_model)
        when "visualize_one_entity_type"
            if $current_model == nil
                return 
            end
            MoosasRender.show_entity_type($current_model,params[0].to_i())
        when "disable_visualize_entity_type"
            MoosasRender.disable_visualize_entity_type($current_model)
        when "show_all_face"
            MMR.show_all_face
        when "show_space"
            MoosasRender.show_space($current_model,params[0])
        when "change_space_parameters"
            $current_model.change_space_parameters(params)
            self.send("update_model_data",$current_model.pack_data) 
            MoosasUtils.backup_setting_data()
        when "update_model_data"
            if $current_model!=nil
                model_data = $current_model.pack_data
                self.send("update_model_data",model_data) 
            end
        when "update_weather_station"
            if params[0] =="0"
                weatherstid=MoosasWeather.include_epw_file()
                MoosasWeather.update_weather_station(weatherstid)
                MoosasWeather.reset_weather_data_to_ui()
            else
                MoosasWeather.update_weather_station(params[0])
            end
        when "daylight_analysis"
            MMR.update_model
            MoosasDaylight.local_analysis_daylight($space_select_index)  if MoosasLock.valid()
        when "sunhour_analysis"
            MoosasSunHour.sunhour_analyse_grids()  if MoosasLock.valid()
        when "ventilation_analysis"
            MoosasVent.analysis()
        when "radiance_analysis"
            MoosasRadiance.calculate_radiance()
        when "change_settings"
            param = JSON.parse(params[0])
            param.keys.each{ |key|  
                $ui_settings[key] = param[key]
            }
            if $current_model !=nil
                $current_model.spaces.each{ |space|  
                    space.apply_settings(
                        MoosasStandard.search_template([
                            MoosasStandard::STANDARDNAME[$ui_settings["selectBuildingType"]],
                            MoosasStandard::STANDARDNAME[$ui_settings["selectStandard"]]
                            ])[0]
                        )
                }
                MoosasUtils.backup_setting_data()
            end

        else
            
        end
    rescue => e
        MoosasUtils.rescue_log(e)
    end


    ########################## Package and Send JSON Command to WebDialog #############################

    def self.send(command,params)
    # """
    # Function
    # --------
    # Sends a command with parameters to a dialog interface by generating a JSON string and executing it as a script.
    # 
    # Parameters
    # ----------
    # command : String
    # The command name to be sent, typically representing an action to be performed in the receiving environment.
    # params : Hash
    # A hash of parameters associated with the command, containing key-value pairs that provide additional data or options.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. In case of an exception, it logs the error and continues execution.
    # """
      begin
        json = JSON.generate({ "command" => command, "params" => params })
        script_string = "Skp.receive(eval(#{json}))"
        #p script_string
        @dialog.execute_script(script_string)
      rescue Exception => e
        MoosasUtils.rescue_log(e)
      end
    end

    def self.send_weather_data(data)
    # """
    # Function
    # --------
    # Sends weather data to a web dialog by executing a JavaScript function within the dialog's context.
    # 
    # Parameters
    # ----------
    # data : String
    # A string containing weather-related data that will be passed to the JavaScript function
    # `Skp.receive_weather_data` in the web dialog.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It executes a script asynchronously and handles errors internally.
    # 
    # Notes
    # -----
    # The method attempts to execute a JavaScript call `Skp.receive_weather_data(data)` within the context
    # of a web dialog referenced by the class variable `@dialog`. If an exception occurs during execution,
    # it prints an error message and logs the exception using `MoosasUtils.rescue_log`.
    # """
        begin
            
            #script_string = "alert(1)"
            #@dialog.execute_script(script_string)
            #script_string = "alert(\"#{data}\")"
            #@dialog.execute_script(script_string)
            script_string = "Skp.receive_weather_data(\"#{data}\")"
            @dialog.execute_script(script_string)
        rescue Exception => e
            p "Error occurs in MoosasWebDialog.send_weather_data()."
            MoosasUtils.rescue_log(e)
        end
    end

    def self.set_long_value(long_message)
    # Function:
    # Set the inner HTML of an element with ID 'long_msg' using JavaScript execution within a dialog.
    # 
    # Parameters:
    # long_message : str
    # The string content to be set as the innerHTML of the element with ID 'long_msg'.
    # 
    # Returns:
    # None
    # This method does not return any value.
        js_command = "document.getElementById('long_msg').innerHTML = #{long_message}"
        @dialog.execute_script(js_command)
    end

    
end