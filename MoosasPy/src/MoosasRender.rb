# Ver.0.6.1
class MoosasRender
    
    @entity_materials = nil
    @visulized=false
    $define_materials = {}
    $backup_materials = {}

    def self.update_define_materials(face,cat)
        if @entity_materials == nil
            self.load_entity_materials
        end
        if cat.is_a?(String)
            cat = cat.to_i
        end
        if @entity_materials.has_key?(cat)
            $define_materials[face.persistent_id] = cat
        end
    end

    def self.mark_face(cat)
        entities = Sketchup.active_model.selection
        self.traverse_faces(entities) do |face,path|
            self.update_define_materials(face,cat)
            if $define_materials.has_key?(face.persistent_id)
                if $backup_materials[face.persistent_id]==nil
                    $backup_materials[face.persistent_id]=[face.material,face.back_material]
                end
                mat = "moosas_" + @entity_materials[$define_materials[face.persistent_id]]
                face.material = mat
                face.back_material = mat
            end
        end
    end

    def self.visualize_repeat(model)
        if @visulized
            begin
                self.disable_visualize_entity_type(model)
            rescue StandardError => e
                p "Error disable visualize"
                @visulized = false
            end
            
        else
            begin
                self.visualize_entity_type(model)  
            rescue StandardError => e
                p "Error visualize"
                @visulized = true
            end
            
        end
    end

    def self.visualize_entity_type(model)

        if @entity_materials == nil
            self.load_entity_materials
        end


        Sketchup.active_model.start_operation("标记面的类型", true)

        model = Sketchup.active_model

        self.traverse_faces(model.entities) do |face,path|
            if $define_materials.has_key?(face.persistent_id)
                if $backup_materials[face.persistent_id]==nil
                    $backup_materials[face.persistent_id]=[face.material,face.back_material]
                end
                mat = "moosas_" + @entity_materials[$define_materials[face.persistent_id]]
                face.material = mat
                face.back_material = mat
            end
        end

        # moosas_faces = MMR.all_recognized_faces
        #
        # moosas_faces.each do |mf|
        #     #p "id =#{mf.id}, type = #{mf.type}"
        #     mat = "moosas_" + @entity_materials[mf.type]
        #     face = mf.face
        #     if $backup_materials[face.persistent_id]==nil
        #         $backup_materials[face.persistent_id]=[face.material,face.back_material]
        #     end
        #     face.material = mat
        #     face.back_material = mat
        #     if mf.type == MoosasConstant::ENTITY_SHADING or mf.type == MoosasConstant::ENTITY_SURROUNDING
        #         face.material.alpha=0.5
        #     end
        # end
        #
        # m=Sketchup.active_model
        # entities=m.active_entities

        #for s in model.spaces
        #    entities=s.construct_space_volume(entities)
        #end
        Sketchup.active_model.commit_operation

        #Sketchup.send_action "showRubyPanel:"
        #p "提醒：\r\n进入标签状态后，在任何修改模型操作之前，请点击\"关闭可视化识别结果\"按钮,退到进入标签前的状态，避免模型材质恢复出错!"
        @visulized=true
    end


    def self.disable_visualize_entity_type(model)
        return if !@visulized
        model = Sketchup.active_model
        self.traverse_faces(model.entities) do |face,path|
            if $backup_materials.has_key?(face.persistent_id)
                face.material = $backup_materials[face.persistent_id][0]
                face.back_material = $backup_materials[face.persistent_id][1]
            end
        end
        # moosas_faces = MMR.all_recognized_faces
        #
        #status = Sketchup.active_model.abort_operation  #简单采用撤销操作
        #Sketchup.send_action("editUndo:")
        # moosas_faces = model.get_all_face
        #
        # for i in 0..moosas_faces.length-1
        #     begin
        #         face = moosas_faces[i].face
        #         face.material = $backup_materials[face.persistent_id][0]
        #         face.back_material = $backup_materials[face.persistent_id][1]
        #         # face.material = moosas_faces[i].skp_material[0]
        #         # face.back_material = moosas_faces[i].skp_material[1]
        #     rescue
        #     end
        # end
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
        if @entity_materials != nil
            return @entity_materials
        end
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
          MoosasConstant::ENTITY_WALL => "wall",
          MoosasConstant::ENTITY_INTERNAL_WALL => "internalwall",
          MoosasConstant::ENTITY_GLAZING => "glazing",
          MoosasConstant::ENTITY_INTERNAL_GLAZING => "internalglazing",
          MoosasConstant::ENTITY_SKY_GLAZING => "skyglazing",
          MoosasConstant::ENTITY_ROOF => "roof",
          MoosasConstant::ENTITY_FLOOR => "floor",
          MoosasConstant::ENTITY_GROUND_FLOOR => "groundfloor",
          MoosasConstant::ENTITY_SHADING => "shading",
          MoosasConstant::ENTITY_PARTY_WALL => "partywall",
          MoosasConstant::ENTITY_DOOR => "door",
          MoosasConstant::ENTITY_AIRWALL => "airwall",
          MoosasConstant::ENTITY_SURROUNDING => "surrounding",
          MoosasConstant::ENTITY_IGNORE => "ignore"
        }

        @entity_materials.keys.each do |k|
            mat_name = "moosas_" + @entity_materials[k]
            Sketchup.active_model.materials.remove(mat_name) if Sketchup.active_model.materials[mat_name]
            material = Sketchup.active_model.materials.add mat_name
            material.texture = dir +  "textures/texture_" + @entity_materials[k] + ".png"
            material.texture.size = size
            #material.alpha = mat_name.include?("glazing") ? 0.95 : 1.0

        end

        return @entity_materials
    end

    def self.moosas_material_lib
        if @entity_materials == nil
            self.load_entity_materials
        end
        return @entity_materials
    end


end