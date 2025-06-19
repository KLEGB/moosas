#Sketchup::require("moosas2018/src/MoosasConstant")

# if Sketchup.version.to_f >= 14

# 	begin
# 		require 'net/https'
# 	rescue LoadError => e
# 		MoosasUtils.log_error(e)
# 	end

# 	begin
# 		require 'uri'
# 		require 'open-uri' #using open-uri since it follows redirects properly, and has a simpler interface
# 	rescue LoadError => e
# 		MoosasUtils.log_error(e)
# 	end
# end

class MoosasUtils
	Ver='0.6.4'

	def self.is_unix()
		( RUBY_PLATFORM =~ /(darwin|linux|i386-cygwin|i386-mingw32)/i ) == 1
	end

	def self.moosas_active?
		MoosasWebDialog.dialog.visible?
	end
	def self.exec_python(pyfile,codelines,console=false)
		Dir.chdir MPath::PYTHON
		if FileTest::exists?("status.log")
			File.delete("status.log")
		end
		if FileTest::exists?("error.log")
			File.delete("error.log")
		end
		File.open(MPath::DATA+"script/#{pyfile}","w+") do |f|
			f.puts("import traceback\n")
			f.puts("try:\n")
			for line in codelines
				f.puts("\t#{line}\n")
			end
			f.puts("\twith open('status.log','w+') as f:\n")
			f.puts("\t\tf.write('1')\n")
			f.puts("except Exception as e:\n")
			f.puts("\tprint(traceback.format_exc())\n")
			f.puts("\twith open('error.log','w+') as f:\n")
			f.puts("\t\tf.write(traceback.format_exc())\n")
			f.puts("\twith open('status.log','w+') as f:\n")
			f.puts("\t\tf.write('0')\n")
		end
		begin
			if console
				system(".\\python.exe \"#{MPath::DATA}script/#{pyfile}\"")
			else
				system(".\\pythonw.exe \"#{MPath::DATA}script/#{pyfile}\"")
			end
			# self.wait("status.log")
			# sleep(0.1)
			if FileTest::exists?("error.log")
				File.open("error.log","w+") do |err|
					p err.gets
				end
				return false
			else
				return true
			end
		rescue => e
			MoosasUtils.rescue_log(e)
			return false
		ensure
			Dir.chdir File.dirname(__FILE__)
		end
	end
	def self.rescue_log(e, log_to_sconsole=true)
	    if (defined?(Sketchup.active_model) and not Sketchup.active_model.nil?)
	      Sketchup.active_model.abort_operation
	    end
	    MoosasUtils.log_error(e, log_to_sconsole)
	end

	def self.log_error(e, log_to_sconsole=true)
	 	if defined?(e.backtrace)
	      self.log(self.format_error(e))
	    else
	      self.log("error: " + e)
	    end
	end

	def self.format_error(e)
		error_backtrace = e.backtrace.join("\n                            ")
    	"error: message='#{e.inspect}', backtrace='#{error_backtrace}'"
  	end

	def self.log(string)
	 	log_line = Time.now.asctime+"\t"+string+"\n"
    	puts log_line
	end

	def self.get_path()
		File.dirname(__FILE__) + "/../"
	end

	def self.upload_file(url, filename)
		uri = URI.parse(url)

    	http = Net::HTTP.new(uri.host, uri.port)
    	http.use_ssl = (uri.scheme == 'https')
    	http.verify_mode = OpenSSL::SSL::VERIFY_NONE

    	request = Net::HTTP::Get.new(uri.request_uri, {"Content-Type" => "application/octet-stream"})
    	request.body = File.open(filename, 'rb').read
    	response = http.request(request)
    	return response
	end

	def self.download_file(url, filename)
		open(url,:ssl_verify_mode => OpenSSL::SSL::VERIFY_NONE,"Content-Type" => "application/octet-stream") { |f|
      		File.open(filename, 'wb') do |file|
        		file.puts f.read
      		end
    	}
	end

	def self.get_document_dir()
		begin
			if(!@documents_dir)
				if(is_unix())
					@documents_dir = File.expand_path('~/Moosas/')
				else
					require 'win32/registry'
					reg_path = 'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        			reg = Win32::Registry::HKEY_CURRENT_USER.open( reg_path )
        			dir = File.expand_path(reg['Personal'])
        			@documents_dir = File.join(dir, "Moosas")
				end
			end

			Dir.mkdir(@documents_dir,(0777 & ~File.umask)) unless File.exists?(@documents_dir)

			return @documents_dir

		rescue Exception => e
			rescue_log(e)
		end
	end

	def self.get_temp_dir()
		if(is_unix())
			temp = "/tmp/Moosas/"
		else
			temp = File.join(File.expand_path(ENV["TEMP"]), "Moosas")
		end

		Dir.mkdir(temp) unless File.exists?(temp)

		return temp
	end

    def self.get_flat_plane

        model  = Sketchup.active_model
        sel = model.selection
        oxy_plane = [Geom::Point3d.new(0,0,0), Geom::Vector3d.new(0,0,1)]

        group = Sketchup.active_model.entities.add_group
        entities = group.entities
        i = 0
        sel.each do |entity|
            p entity
            case entity
            when Sketchup::Face
                ol = entity.outer_loop
                vertices = ol.vertices
                vs = []
                vertices.each do |v|
                    vs.push v.position.project_to_plane(oxy_plane)
                end
                entities.add_face vs
                i += 1
                p "添加了#{i}个面"
            end
        end
    end
    def self.retrive_setting_data()
    	model = Sketchup.active_model
        title =  model.title
        path=MPath::DB+ "settings/"+title+".json"
        begin
        	setting_data=JSON.parse(File.read(path))
        	#p setting_data
        rescue
        	p "space settings data unfound."
        	return
        end
        retrivelen=0
        #setting_data.keys.each{|space_id|
        #	if ($current_model%space_id)!=nil
        #		($current_model%space_id).settings=setting_data[space_id]
        #		p  p "#{space_id}:#{($current_model%space_id).settings["zone_summerrad"]}"
        #		retrivelen+=1
        #	end
        #}
        $current_model.spaces.each{ |s|  
        	if setting_data.include?(s.id)
        		s.settings=setting_data[s.id]
        		retrivelen+=1
        	end
        }
        p "retrive space settings: #{retrivelen}"
       
    end
	def self.backup_setting_data(space_id = nil)
		model = Sketchup.active_model
        title =  model.title
        path=File.dirname(__FILE__) + "/../db/settings/"+title+".json"
        begin
        	setting_data=JSON.parse(File.read(path))
        rescue
        	setting_data={}
        end
        if space_id==nil
        	$current_model.spaces.each{|space| setting_data[space.id]=space.settings}
        	p "backup space settings: #{setting_data.keys.length}"
        else 
        	setting_data[space_id]=($current_model%space_id).settings
        end
        File.write(path, JSON.dump(setting_data))
    end
    def self.wait(file,max_waiting=10)
    	(1..max_waiting).each{ |variable|  
	    	if File.exists? file
	    		return true
	    	else
	    		p "**Error: Unfound " + file + " Waiting..." + variable.to_s
	    		sleep(0.5)
	    	end
    	}
    end

    def self.back_up_model()
        model = Sketchup.active_model
        path = model.path
        fn = Time.new
        fn = fn.to_s
        fn = fn[0,19].gsub(":","_").gsub(" ","_")

        title =  model.title
        if path != nil and path != "" and title != nil and title !=""
            arr = path.split("\\")
            arr[arr.length-1] = "#{title}_#{fn}.skp"
            filename = arr.join("\\")
        else
            filename = File.join(ENV['Home'], 'Desktop', "MOOSAS模型#{fn}.skp")
        end


        begin
            status = model.save_copy(filename)
            if status == true
                return filename
            else
                return nil
            end
        rescue Exception => e
            p "请先保存模型，才能进行模型备份!"
            return nil
        end
    end

end