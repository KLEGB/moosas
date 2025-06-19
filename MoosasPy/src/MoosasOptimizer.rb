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

        @has_init_controller = true
    end

    def self.show_ui(optimizer="optimizer_thu_env_cn")

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
        fn = Time.new
        fn = fn.to_s
        fn = fn[0,19].gsub(":","_").gsub(" ","_")
        @record_file_name = File.join(ENV['Home'], 'Desktop', "MOOSAS优化数据记录#{fn}.txt")
    end

    def self.nasg2_ready()
        js_command = "nasg2_ready()"
        @dialog.execute_script(js_command)
    end

end