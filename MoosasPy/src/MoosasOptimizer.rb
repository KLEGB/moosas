class MoosasOptimizer
    Ver='0.6.1'

    class << self
        attr_reader :dialog
    end

    @dialog = UI::HtmlDialog.new({
        :dialog_title => "MOOSAS建筑性能优化设计",
        :preferences_key => "MoosasOptimizer",
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
    
    @has_init_controller = false

    @nsga2 = nil

    @record_file_name = nil

    def self.init_controller()
    # """
    # Function
    # --------
    # Initializes the controller by setting the initialization flag.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value.
    # """

        @has_init_controller = true
    end

    def self.show_ui(optimizer="optimizer_thu_env_cn")
    # """
    # Function
    # --------
    # show_ui
    # Displays a user interface dialog for interacting with an optimization process.
    # Sets up action callbacks to handle various UI events such as receiving messages,
    # starting optimization, updating generation count, and visualizing models.
    # 
    # Parameters
    # ----------
    # optimizer : str, optional
    # The name of the optimizer configuration to load. This determines which UI file (HTML)
    # is loaded from the MPath::UI directory. Default is "optimizer_thu_env_cn".
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It initializes the UI, sets up callbacks,
    # and displays the dialog modally or non-modally depending on the operating system.
    # """

        @dialog.set_file(MPath::UI + optimizer + ".htm")

        self.init_controller if not @has_init_controller

        @dialog.add_action_callback("say") { |action_context, param1|
            receive(param1.to_s)
        }

        @dialog.add_action_callback("start") { |action_context,json|
            setting = JSON.parse(json)
            p "using optimizer #{setting['optimizer']}"
            self.set_record_filename()
            @nsga2  = NSGA2.new(setting['optimizer'],setting['num_parameters'], setting['x_bounds'], setting['num_objectives'],setting['population_size'],setting['obj_preferences'],setting['open_preference'])
            
        }

        @dialog.add_action_callback("update_generation") { |action_context,i_generations|
            @nsga2.update_generation(i_generations.to_i)
        }

        @dialog.add_action_callback("show_model") { |action_context,x|
            params = x.split(",")
            x = []
            params.each do |i|
                x.push(i.to_f())
            end
            p x

            MoosasShapeGenerator.generate_thu_env_building(x)
            #MoosasShapeGenerator.generate_xuduo_building(x)
        }

        MoosasUtils.is_unix ? @dialog.show_modal : @dialog.show
    end


    def self.update_view(data)
    # """
    # Function
    # --------
    # Updates the UI view with provided data and logs the update to a file.
    # 
    # Parameters
    # ----------
    # data : Hash or Array
    # The data structure containing information to be sent to the UI. It will be
    # converted to a JSON string and passed to the JavaScript function for updating
    # the interface.
    # 
    # Returns
    # -------
    # nil
    # This method does not return a value. It performs side effects by executing
    # a JavaScript command in the dialog and appending the JSON data to a log file.
    # """
        json = JSON.generate(data)
        js_command = "update_ui(eval(#{json}))"
        @dialog.execute_script(js_command)

        #写到指定文件中
        File.open(@record_file_name, 'a') { |f| 
            f.write(json)
            f.write("\r\n") 
        }
    end

    def self.set_record_filename
    # Function:
    # Sets the record file name based on the current timestamp and stores it in the class variable `@record_file_name`.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # String: The generated file path assigned to `@record_file_name`, combining the user's Desktop directory with a timestamped filename in the format "MOOSAS优化数据记录YYYY_MM_DD_HH_MM_SS.txt".
        fn = Time.new
        fn = fn.to_s
        fn = fn[0,19].gsub(":","_").gsub(" ","_")
        @record_file_name = File.join(ENV['Home'], 'Desktop', "MOOSAS优化数据记录#{fn}.txt")
    end

    def self.nasg2_ready()
    # Function:
    # Execute the 'nasg2_ready' JavaScript function within the dialog context.
    # 
    # Parameters:
    # js_command : String
    # A string containing the JavaScript command to be executed, specifically 'nasg2_ready()'.
    # 
    # Returns:
    # The return value of the executed JavaScript command, as returned by the dialog's execute_script method.
        js_command = "nasg2_ready()"
        @dialog.execute_script(js_command)
    end

end