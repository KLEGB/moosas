
class MoosasMeta
    Ver='0.6.3'

    def self.get_and_set_dic(dic_name,key_name,data,append=false)
    # """
    # Function
    # ----------
    # get_and_set_dic
    # Retrieves a value from a model's attribute dictionary and optionally appends data to it, then sets the updated value back into the dictionary.
    # 
    # Parameters
    # ----------
    # dic_name : String
    # The name of the attribute dictionary.
    # key_name : String
    # The key within the dictionary to retrieve or set.
    # data : Object
    # The data to be stored or appended in the dictionary entry.
    # append : Boolean, optional (default: False)
    # If True, appends the provided data to the existing array value. If False, replaces the existing value with the new data.
    # 
    # Returns
    # -------
    # Object
    # The updated content that was set in the attribute dictionary. If append is True and the original value existed, returns the extended array; otherwise, returns the new data value.
    # """

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
    # Function:
    # Resets and sends saved data from the SketchUp model's attributes to the MoosasWebDialog.
    # This includes both the current analysis data and the historical analysis data stored in the model.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # None
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