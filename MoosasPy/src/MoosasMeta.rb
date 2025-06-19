
class MoosasMeta
    Ver='0.6.3'

    def self.get_and_set_dic(dic_name,key_name,data,append=false)

        model = Sketchup.active_model
        content = model.get_attribute(dic_name,key_name) 
        #p "get_attribute"
        #p content
        if append
            if content == nil
                new_content = [data]
            else
                new_content = content.push(data)
            end
        else
            new_content = data 
        end
        model.set_attribute(dic_name,key_name,new_content)
        return new_content
    end


    def self.reset_saved_data
        model = Sketchup.active_model

        #方案当前数据
        meta_current_data = model.get_attribute("moosas","current")
        if meta_current_data!=nil
            MoosasWebDialog.send("main_analysis_result",JSON.parse(meta_current_data))
        end

        #方案分析历史数据
        meta_history_data = model.get_attribute("moosas","history")
        MoosasWebDialog.send("update_analysis_history",meta_history_data)

    end

end