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
	# Function:
	# Determines whether the current platform is a Unix-based system.
	# 
	# Parameters:
	# None
	# 
	# Returns:
	# bool: Returns true if the current RUBY_PLATFORM matches a Unix-like system
	# (including darwin, linux, i386-cygwin, or i386-mingw32), otherwise false.
	# Note: The method uses a case-insensitive regular expression check and
	# returns true only if the match result is exactly 1, which may indicate
	# a logic issue since regex match results are typically indices or nil.
		( RUBY_PLATFORM =~ /(darwin|linux|i386-cygwin|i386-mingw32)/i ) == 1
	end

	def self.moosas_active?
		MoosasWebDialog.dialog.visible?
	end
	def self.exec_python(pyfile,codelines,console=true)
	# Function:
	# Executes a Python script file generated from provided code lines using either python.exe or pythonw.exe,
	# captures execution status via log files, and returns success or failure based on the presence of errors.
	# 
	# Parameters:
	# pyfile : str
	# The name of the Python script file to be created and executed.
	# codelines : list of str
	# A list of Python code lines to be written into the script file. These lines are inserted inside a try block.
	# console : bool, optional
	# If true (default), uses python.exe to run the script with console output; otherwise, uses pythonw.exe
	# to run the script without a console window.
	# 
	# Returns:
	# bool
	# Returns True if the script executes without raising an exception (i.e., no error.log is created).
	# Returns False if an exception occurs during execution, indicated by the creation of error.log,
	# or if an error occurs while attempting to run the system command.
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
			if console
				f.puts("\tinput('******Severe Error******')\n")
				end
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
	# """
	# Function
	# --------
	# Handles exception logging and model operation abortion in SketchUp environment.
	# 
	# Parameters
	# ----------
	# e : Exception
	# The exception object to be logged.
	# log_to_sconsole : bool, optional
	# If true, logs the error message to SketchUp's Ruby console. Default is True.
	# 
	# Returns
	# -------
	# None
	# This method does not return a value. It performs side effects including operation abortion and error logging.
	# """
	    if (defined?(Sketchup.active_model) and not Sketchup.active_model.nil?)
	      Sketchup.active_model.abort_operation
	    end
	    MoosasUtils.log_error(e, log_to_sconsole)
	end

	def self.log_error(e, log_to_sconsole=true)
	# """
	# Function
	# --------
	# Logs an error message or exception to the system console or log system.
	# 
	# Parameters
	# ----------
	# e : Exception or String
	# The exception object or error message to be logged. If it is an Exception
	# with a backtrace, the formatted exception including stack trace will be logged.
	# Otherwise, the string representation of the error will be logged.
	# log_to_sconsole : bool, optional
	# If True (default), logs the error to the system console. This parameter
	# does not directly affect logging behavior in this method but may be used
	# in downstream `self.log` implementation to route output.
	# 
	# Returns
	# -------
	# None
	# This method does not return a value. It performs a side effect by writing
	# error information to the log.
	# """
	 	if defined?(e.backtrace)
	      self.log(self.format_error(e))
	    else
	      self.log("error: " + e)
	    end
	end

	def self.format_error(e)
	# Function:
	# Format an exception into a standardized error message string.
	# 
	# Parameters:
	# e : Exception
	# The exception object to be formatted. It should have `inspect` and `backtrace` methods available,
	# typically an instance of a Ruby Exception class or its descendants.
	# 
	# Returns:
	# str
	# A formatted string containing the error message and backtrace. The message includes the inspected
	# exception value and the full backtrace indented and joined with newline characters for readability.
		error_backtrace = e.backtrace.join("\n                            ")
    	"error: message='#{e.inspect}', backtrace='#{error_backtrace}'"
  	end

	def self.log(string)
	# Function:
	# Logs a given string with a timestamp to the console.
	# 
	# Parameters:
	# string : str
	# The message to be logged. It will be prefixed with the current time in ASCII format.
	# 
	# Returns:
	# None
	# This method does not return a value. It outputs the log line to standard output (console).
	 	log_line = Time.now.asctime+"\t"+string+"\n"
    	puts log_line
	end

	def self.get_path()
	# """
	# Function
	# --------
	# Returns the parent directory path of the current file's directory.
	# 
	# Parameters
	# ----------
	# None
	# 
	# Returns
	# -------
	# str
	# The absolute path to the parent directory of the directory containing the current file.
	# """
		File.dirname(__FILE__) + "/../"
	end

	def self.upload_file(url, filename)
	# """
	# Function
	# ----------
	# Uploads the content of a local file to a specified URL using an HTTP GET request with the file data in the body.
	# 
	# Parameters
	# ----------
	# url : str
	# The destination URL to which the file will be uploaded. Must include the scheme (http or https).
	# filename : str
	# The path to the local file that is to be uploaded. The file is read in binary mode.
	# 
	# Returns
	# -------
	# response : Net::HTTPResponse
	# The HTTP response object returned by the server after the request is made. This includes status code, headers, and body.
	# """
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
	# """
	# Function
	# ----------
	# Download a file from the specified URL and save it locally with the given filename.
	# 
	# Parameters
	# ----------
	# url : str
	# The URL of the file to be downloaded. Must be a valid HTTP or HTTPS address.
	# filename : str
	# The local path and name under which the downloaded file will be saved.
	# 
	# Returns
	# -------
	# None
	# This method does not return a value. It saves the downloaded content directly to the specified file.
	# """
		open(url,:ssl_verify_mode => OpenSSL::SSL::VERIFY_NONE,"Content-Type" => "application/octet-stream") { |f|
      		File.open(filename, 'wb') do |file|
        		file.puts f.read
      		end
    	}
	end

	def self.get_document_dir()
	# """
	# Function
	# --------
	# Get the document directory path for the application, creating it if it does not exist.
	# 
	# On Unix-like systems, the directory is created under the user's home folder as '~/Moosas/'.
	# On Windows, it retrieves the user's personal documents folder from the registry and appends 'Moosas'.
	# 
	# Parameters
	# ----------
	# None
	# This method does not accept any parameters.
	# 
	# Returns
	# -------
	# String or nil
	# The file path to the document directory (e.g., '~/Moosas' or 'C:/Users/User/Documents/Moosas').
	# Returns nil if an exception occurs during execution.
	# """
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
	# """
	# Function
	# --------
	# get_temp_dir : class method
	# Returns the path to a temporary directory used by the application.
	# If the directory does not exist, it is created automatically.
	# 
	# Parameters
	# ----------
	# None
	# This method does not accept any parameters.
	# 
	# Returns
	# -------
	# str
	# The file system path to the temporary directory. On Unix-like systems,
	# this is '/tmp/Moosas/'. On Windows, it is a 'Moosas' subdirectory
	# within the system's TEMP directory.
	# """
		if(is_unix())
			temp = "/tmp/Moosas/"
		else
			temp = File.join(File.expand_path(ENV["TEMP"]), "Moosas")
		end

		Dir.mkdir(temp) unless File.exists?(temp)

		return temp
	end

    def self.get_flat_plane
    # Function:
    # Extracts selected faces from the active SketchUp model and projects them onto the XY plane (Z=0)
    # by creating a new group containing flattened versions of the original faces.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # nil : The method does not return any value. It modifies the model by adding a new group
    # with projected 2D faces on the XY plane.
    # 
    # Notes:
    # - Operates on the current selection in the active model.
    # - Only processes entities that are instances of Sketchup::Face.
    # - Each vertex of the selected face is projected onto the XY plane (defined by origin and Z-axis normal).
    # - A new face is created in a group using the projected 2D points.
    # - Prints each entity and a progress message for every processed face.

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
    # """
    # Function
    # --------
    # Retrieve and apply space settings from a JSON file associated with the current SketchUp model.
    # 
    # This method constructs a file path based on the active model's title, reads a JSON file containing
    # space-specific settings, and applies those settings to corresponding spaces in the current model.
    # If the file is not found or cannot be parsed, an error message is printed and the method returns early.
    # 
    # Parameters
    # ----------
    # None
    # This is a class method that takes no arguments. It operates on the currently active SketchUp model
    # and uses global variable `$current_model` to access space entities.
    # 
    # Returns
    # -------
    # nil
    # The method does not return a value. On failure to read the settings file, it prints an error message
    # and returns nil. On success, it updates space settings in the model and prints the count of retrieved settings.
    # """
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
	# Function:
	# Backs up the settings data of spaces in a SketchUp model to a JSON file. If no specific space ID is provided, it backs up settings for all spaces in the current model. If a space ID is given, only the settings for that particular space are backed up.
	# 
	# Parameters:
	# space_id : String or nil, optional
	# The unique identifier of a specific space to back up. If not provided (i.e., set to nil), settings for all spaces in the current model will be backed up.
	# 
	# Returns:
	# None
	# This method does not return any value. It writes the backup data directly to a JSON file on disk.
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
    # """
    # Function
    # --------
    # Waits for a specified file to become available within a given time limit.
    # 
    # This method repeatedly checks for the existence of a file at half-second intervals
    # up to a maximum number of attempts. It prints a message each time the file is not found
    # and returns early if the file is detected before the timeout.
    # 
    # Parameters
    # ----------
    # file : String
    # The path to the file whose existence is being checked.
    # max_waiting : Integer, optional
    # The maximum number of half-second intervals to wait (default is 10, i.e., 5 seconds).
    # 
    # Returns
    # -------
    # Boolean
    # Returns `true` if the file is found within the waiting period.
    # If the file is not found after `max_waiting` attempts, the method ends without an explicit return,
    # which results in `nil` being returned by default.
    # """
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
    # Function:
    # Creates a backup copy of the active SketchUp model with a timestamped filename.
    # If the model is already saved, it uses the original path and model title to construct
    # the backup filename. Otherwise, saves the backup to the user's Desktop with a default name.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # str or None: The file path of the saved backup copy if successful; None if the save operation
    # fails or an exception occurs (e.g., model has not been saved yet). Prints an error message
    # to stdout if the model cannot be backed up due to being unsaved.
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