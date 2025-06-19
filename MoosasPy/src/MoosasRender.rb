# Ver.0.6.1
class MoosasRender
    Ver='0.6.3'
    
    @entity_materials = nil
    @visulized=false
    @backup_materials= {}

    def self.visualize_repeat(model)
        if @visulized
            begin
                self.disable_visualize_entity_type(model)
            rescue StandardError => e
                @visulized = false
            end
            
        else
            begin
                self.visualize_entity_type(model)  
            rescue StandardError => e
                @visulized = true
            end
            
        end
    end

    def self.visualize_entity_type(model)

        if @entity_materials == nil
            self.load_entity_materials()
        end


        Sketchup.active_model.start_operation("标记面的类型", true)

        moosas_faces = model.get_all_face

        moosas_faces.each do |mf|
            #p "id =#{mf.id}, type = #{mf.type}"
            mat = "moosas_" + @entity_materials[mf.type]
            face = mf.face
            if @backup_materials[mf.id]==nil
                @backup_materials[mf.id]=[face.material,face.back_material]
            end
            face.material = mat
            face.back_material = mat
            if mf.type == MoosasConstant::ENTITY_SHADING or mf.type == MoosasConstant::ENTITY_SURROUNDING
                face.material.alpha=0.5
            end
        end
        
        m=Sketchup.active_model
        entities=m.active_entities

        #for s in model.spaces
        #    entities=s.construct_space_volume(entities)
        #end
        Sketchup.active_model.commit_operation

        #Sketchup.send_action "showRubyPanel:"
        #p "提醒：\r\n进入标签状态后，在任何修改模型操作之前，请点击\"关闭可视化识别结果\"按钮,退到进入标签前的状态，避免模型材质恢复出错!"
        @visulized=true
    end


    def self.disable_visualize_entity_type(model)
        return if @visulized==false

        #status = Sketchup.active_model.abort_operation  #简单采用撤销操作
        #Sketchup.send_action("editUndo:")
        moosas_faces = model.get_all_face

        for i in 0..moosas_faces.length-1
            begin
                face = moosas_faces[i].face
                face.material = @backup_materials[moosas_faces[i].id][0]
                face.back_material = @backup_materials[moosas_faces[i].id][1]
            rescue
            end
        end
        @visulized=false
    end

    def self.show_entity_type(model,type_index)
        Sketchup.active_model.start_operation("标记面的类型#{type_index}", true)
        self.hide_all_face
        moosas_faces = model.get_all_face
        moosas_faces.each do |mf|
            if mf.type == type_index
                mf.face.hidden = false
            end
        end
        Sketchup.active_model.commit_operation
    end

    def self.traverse_faces(entity, path=[], &func)
        case entity
        when Sketchup::Face
            func.arity == 1 ? func.call(entity) : func.call(entity, path)
        when Sketchup::Group 
            traverse_faces(entity.entities, path + [entity], &func)
        when Sketchup::ComponentInstance
            traverse_faces(entity.definition.entities, path + [entity], &func)
        when Sketchup::Entities, Sketchup::Selection, Enumerable
            entity.each {|e| traverse_faces(e,path,&func)}
        end
    end

    def self.show_all_face
        self.traverse_faces(Sketchup.active_model.entities) do |e,path|
            e.hidden = false
        end
    end

    def self.show_space(model,id)
        for i in 0..model.spaces.length-1
            if model.spaces[i].id==id
                $space_select_index=i
                break
            end
        end
        MMR.select_space_walls($space_select_index)
    end

    def self.hide_all_face
        self.traverse_faces(Sketchup.active_model.entities) do |e,path|
            e.hidden = true
        end
    end
    def self.hide_glazing
        self.traverse_faces(Sketchup.active_model.entities) do |e,path|
            if MMR.is_glazing(e)
                e.hidden = true
            end
        end
    end

    def self.load_entity_materials
        d = Sketchup.active_model.bounds.diagonal
        size = 50 + 50 * (d/800)

        dir = MPath::UI+"images/"

        #if not Sketchup.active_model.materials["test_material"]
        #    ignore_material = Sketchup.active_model.materials.add("test_material")
        #    ignore_material.texture = dir + "checkerboard.png"
        #    ignore_material.color = "Gray"
        #    ignore_material.texture.size = size
        #end
        

        @entity_materials = {
            0 => "wall",
            3 => "internalwall",
            1 => "glazing",
            5 => "internalglazing",
            6 => "skyglazing",
            2 => "roof",
            4 => "floor",
            8 => "groundfloor",
            16 => "shading",
            -1 => "surrounding",
            -2 => "ignore"
        }

        @entity_materials.keys.each do |k|
            mat_name = "moosas_" + @entity_materials[k]
            Sketchup.active_model.materials.remove(mat_name) if Sketchup.active_model.materials[mat_name]
            material = Sketchup.active_model.materials.add mat_name
            material.texture = dir +  "textures/texture_" + @entity_materials[k] + ".png"
            material.texture.size = size
            #material.alpha = mat_name.include?("glazing") ? 0.95 : 1.0

        end
    end




end