
module MoosasUI
    Ver='0.6.3'
    @TOOLBAR=nil
    def self.create_contexual_menus()
        unless @contextual_menu_created
            UI.add_context_menu_handler do |menu|
                menu.add_separator
                sub_menu = menu.add_submenu(MoosasConstant::PLUGIN_MENU_STRING)
                '''
                sub_menu.add_item("将面投影到oxy平面上"){
                    MoosasUtils.get_flat_plane()
                }
                '''
                sub_menu.add_item("采光计算：标注周围建筑遮挡面"){
                    MoosasDaylight.label_sourrouding_shading()
                }
                @contextual_menu_created = true
            end
        end
    end

    def self.create_menus()
        unless @menu_created
            if $language == 'Chinese'
                view_menu = UI.menu "PlugIns"
                view_menu.add_separator
                sub_menu = view_menu.add_submenu(MoosasConstant::PLUGIN_MENU_STRING)

                sub_menu.add_item("打开Moosas"){
                    MoosasWebDialog.show_ui()
                }

                sub_menu.add_item("显示Moosas工具栏"){
                    if @TOOLBAR !=nil
                        @TOOLBAR.show
                    end
                }
            else
                view_menu = UI.menu "PlugIns"
                view_menu.add_separator
                sub_menu = view_menu.add_submenu(MoosasConstant::PLUGIN_MENU_STRING)

                sub_menu.add_item("Open Moosas Interface"){
                    MoosasWebDialog.show_ui()
                }

                sub_menu.add_item("Show Moosas Toolbar"){
                    if @TOOLBAR !=nil
                        @TOOLBAR.show
                    end
                }
                
                #sub_menu.add_separator

                #sub_menu.add_item("全年太阳辐射分析") {
                #    MoosasRadiance.calculate_radiance()
                #}

                #sub_menu.add_item("日照时数分析") {
                #    MoosasSunHour.sunhour_analyse_grids()
                #}

                #sub_menu.add_item("采光模拟") {
                #    MMR.recognize_floor
                #    MoosasDaylight.local_analysis_daylight(rendered=true)
                #}

                #sub_menu.add_separator

                #sub_menu.add_item("加载OSM建筑数据"){
                #    MoosasUrban.load_osm_building
                #}

                #sub_menu.add_item("分析城市光环境(SVF)"){
                #    MoosasUrban.analysis_urban_svf
                #}

                #sub_menu.add_item("导入城市光环境数据"){
                #    MoosasUrban.load_urban_svf_data
                #}
            end
        end
    end

    def self.create_toolbars()
        if $language == 'Chinese'
            tooltip_name=['打开Moosas','模型识别',"通风分析","气流模拟","日照时数分析","辐射分析","室内采光分析","性能优化","查看上一个空间","查看下一个空间","显示所有空间","可视化面的类型"]
        else
            tooltip_name=['Open Interface','Recognize Model',"Ventilation Analysis","CFD Analysis","Sunhour Analysis","Radiation Analysis","Daylight Simulation","Performance Optimization","Last Space","Next Space","Show All Faces","Vilualize Faces' type"]
        end
        image_fodler = MPath::UI+"images/0.5x"
        large_image_fodler =MPath::UI+"images/1x"

        toolbar = UI::Toolbar.new MoosasConstant::PLUGIN_MENU_STRING
        
        cmd = UI::Command.new(tooltip_name[0]) {
            MoosasWebDialog.show_ui() if MoosasLock.valid()
        }
        cmd.small_icon = "#{image_fodler}/main.png"
        cmd.large_icon = "#{image_fodler}/main.png"
        cmd.tooltip = tooltip_name[0]
        cmd.status_bar_text = "打开Moosas | Open the MOOSAS interface."
        cmd.menu_text = tooltip_name[0]
        toolbar = toolbar.add_item cmd

        cmd = UI::Command.new(tooltip_name[1]) {
            
            MMR.recognize_floor  if MoosasLock.valid()
            #UI.messagebox("模型识别完成！")
        }
        cmd.small_icon = "#{image_fodler}/model.png"
        cmd.large_icon = "#{large_image_fodler}/model.png"
        cmd.tooltip = tooltip_name[1]
        cmd.status_bar_text = "模型识别 | Model transformation from skp to Moosas model."
        cmd.menu_text = tooltip_name[1]
        toolbar = toolbar.add_item cmd

        toolbar = toolbar.add_separator

        cmd = UI::Command.new(tooltip_name[2]) {
            MMR.update_model
            if MoosasLock.valid()
                MoosasVent.analysis()
            end
        }
        cmd.small_icon = "#{image_fodler}/vent.png"
        cmd.large_icon = "#{large_image_fodler}/vent.png"
        cmd.tooltip = tooltip_name[2]
        cmd.status_bar_text = "使用Contam进行通风网络分析。 Ventilation analysis by contam based on Air Flow Network(AFN)."
        cmd.menu_text = tooltip_name[2]
        toolbar = toolbar.add_item cmd

        cmd = UI::Command.new(tooltip_name[3]) {
            #MMR.update_model
            if MoosasLock.valid()
                MoosasFoam.analysis()
            end
        }
        cmd.small_icon = "#{image_fodler}/CFD.png"
        cmd.large_icon = "#{large_image_fodler}/CFD.png"
        cmd.tooltip = tooltip_name[3]
        cmd.status_bar_text = "基于AFN结果的CFD气流模拟。 Climate Fluent Dynamic(CFD) analysis based on Air Flow Network(AFN) result."
        cmd.menu_text = tooltip_name[3]
        toolbar = toolbar.add_item cmd

        #cmd = UI::Command.new("生成网格") {
        #    MoosasGrid.fit_grids()  if MoosasLock.valid()
        #}
        #cmd.small_icon = "#{image_fodler}/grid.png"
        #cmd.large_icon = "#{image_fodler}/grid.png"
        #cmd.tooltip = "生成网格"
        #cmd.status_bar_text = "生成网格"
        #cmd.menu_text = "生成网格"
        #toolbar = toolbar.add_item cmd

        cmd = UI::Command.new(tooltip_name[4]) {
            MoosasSunHour.sunhour_analyse_grids()  if MoosasLock.valid()
        }
        cmd.small_icon = "#{image_fodler}/sunhour.png"
        cmd.large_icon = "#{large_image_fodler}/sunhour.png"
        cmd.tooltip = tooltip_name[4]
        cmd.status_bar_text = "分析给定平面的全年日照时数 | Analysis the direct sun hour of refered surfaces."
        cmd.menu_text = tooltip_name[4]
        toolbar = toolbar.add_item cmd

        cmd = UI::Command.new(tooltip_name[5]) {
            MoosasRadiance.calculate_radiance()  if MoosasLock.valid()
        }
        cmd.small_icon = "#{image_fodler}/radiance.png"
        cmd.large_icon = "#{large_image_fodler}/radiance.png"
        cmd.tooltip = tooltip_name[5]
        cmd.status_bar_text = "分析给定平面的全年太阳辐射强度 | Anaylsis the solar radiation intensity of refered surfaces."
        cmd.menu_text = tooltip_name[5]
        toolbar = toolbar.add_item cmd

        cmd = UI::Command.new(tooltip_name[6]) {
            MMR.update_model
            MoosasDaylight.local_analysis_daylight($space_select_index)  if MoosasLock.valid()
        }
        cmd.small_icon = "#{image_fodler}/daylight.png"
        cmd.large_icon = "#{large_image_fodler}/daylight.png"
        cmd.tooltip = tooltip_name[6]
        cmd.status_bar_text = "按空间分析室内采光满足率、均匀度等 | Analize the daylighting performance by spaces."
        cmd.menu_text = tooltip_name[6]
        toolbar = toolbar.add_item cmd

        cmd = UI::Command.new(tooltip_name[7]) {
            if $current_model == nil
                MMR.recognize_floor
            end
            MoosasWebDialog.show_ui('params_analysis_tab') if MoosasLock.valid()
            #MoosasWebDialog.send()
        }
        cmd.small_icon = "#{image_fodler}/optimization.png"
        cmd.large_icon = "#{large_image_fodler}/optimization.png"
        cmd.tooltip = tooltip_name[7]
        cmd.status_bar_text = "打开建筑性能优化面板 | Show the performance optimization panel."
        cmd.menu_text = tooltip_name[7]
        toolbar = toolbar.add_item cmd


        toolbar = toolbar.add_separator

        cmd = UI::Command.new(tooltip_name[8]) {
            if MoosasLock.valid()
                if $current_model == nil
                    p "Spaces not found. Please run the model transformation." 
                else
                    $space_select_index -= 1
                    $space_select_index = $space_select_index % $current_model.spaces.length
                    space_id=MMR.select_space_walls($space_select_index)
                    p "Select Space:#{$space_select_index},id#{space_id}"
                end
            end
        }
        cmd.small_icon = "#{image_fodler}/select_last.png"
        cmd.large_icon = "#{large_image_fodler}/select_last.png"
        cmd.tooltip = tooltip_name[8]
        cmd.status_bar_text = "查看上一个空间及其相关信息 | Show the geometry and info of the last room."
        cmd.menu_text = tooltip_name[8]
        toolbar = toolbar.add_item cmd

        cmd = UI::Command.new(tooltip_name[9]) {
            if MoosasLock.valid()
                if $current_model == nil
                    p "Spaces not found. Please run the model transformation." 
                else
                $space_select_index += 1
                $space_select_index = $space_select_index % $current_model.spaces.length
                
                space_id=MMR.select_space_walls($space_select_index)
                p "Select Space:#{$space_select_index},id#{space_id}"
                end          
            end
        }
        cmd.small_icon = "#{image_fodler}/select_next.png"
        cmd.large_icon = "#{large_image_fodler}/select_next.png"
        cmd.tooltip = tooltip_name[9]
        cmd.status_bar_text = "查看下一个空间及其相关信息 | Show the geometry and info of the next room."
        cmd.menu_text = tooltip_name[9]
        toolbar = toolbar.add_item cmd

         cmd = UI::Command.new(tooltip_name[10]) {
             if MoosasLock.valid()
                 if $current_model == nil
                    p "Spaces not found. Please run the model transformation." 
                 else
                     MMR.show_all_face
                 end
             end
        }
        cmd.small_icon = "#{image_fodler}/select_all.png"
        cmd.large_icon = "#{large_image_fodler}/select_all.png"
        cmd.tooltip = tooltip_name[10]
        cmd.status_bar_text = "显示所有空间。 Show all room"
        cmd.menu_text = tooltip_name[10]
        toolbar = toolbar.add_item cmd

        cmd = UI::Command.new(tooltip_name[11]) {
            if MoosasLock.valid()
                if $current_model == nil
                    p "Spaces not found. Please run the model transformation." 
                else
                    MoosasRender.visualize_repeat($current_model)
                end
            end
        }
        cmd.small_icon = "#{image_fodler}/tag_entity.png"
        cmd.large_icon = "#{large_image_fodler}/tag_entity.png"
        cmd.tooltip = tooltip_name[11]
        cmd.status_bar_text = "按照类型对模型面进行标注 | Visualize the faces in the model based on their types."
        cmd.menu_text = tooltip_name[11]
        toolbar = toolbar.add_item cmd

        #toolbar = toolbar.add_separator

        #cmd = UI::Command.new("城市分析") {
        #    MoosasMap.show_ui()  if MoosasLock.valid()
        #}
        #cmd.small_icon = "#{image_fodler}/Urban.png"
        #cmd.large_icon = "#{large_image_fodler}/Urban.png"
        #cmd.tooltip = "城市分析"
        #cmd.status_bar_text = "打开MOOSAS城市分析功能 | Open the urban alalysis panel."
        #cmd.menu_text = "城市分析"
        #toolbar = toolbar.add_item cmd

        @TOOLBAR=toolbar
        toolbar.show
    end
end

$space_select_index = 0