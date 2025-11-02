
require 'win32/registry'
require 'Win32Api'  
require "digest/sha1"

class MoosasLock
    p 'MoosasLock Ver.0.7.1'
    @exp_date = [2027,9,1]
    
    #连接到PKPM的锁或授权，连接成功返回true
    def self.remain_time()
    # Function:
    # Calculate the remaining time in days between the current date and the expiration date.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # int: The difference in days between the expiration date (@exp_date) and the current date.
    # A positive value indicates the number of days until expiration,
    # while a negative value indicates that the expiration date has passed.
        time=Time.new
        date = [time.year,time.month,time.day]
        date = date[0] * 365 + date[1] * 30 + date[2]
        expd = @exp_date[0] * 365 + @exp_date[1] * 30 + @exp_date[2]
        return expd-date
    end

    p "Expired after: #{self.remain_time()} days"
    
    def self.link_key()
    # Function:
    # Determines whether the software license key is currently linked or valid based on remaining time.
    # 
    # This method checks if the license key remains valid by evaluating the remaining time of the license.
    # If the remaining time is greater than zero, it returns true, indicating the key is still effectively linked.
    # Originally intended to interface with a native DLL to verify hardware key presence, this functionality
    # is currently disabled and replaced with a time-based check.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # Boolean :
    # true if the remaining license time is greater than 0 (indicating an active link), false otherwise.
    # In the current implementation, it always returns true when remaining time is positive,
    # simulating a successful license key connection.
        #return true if MoosasConstant::PLUGIN_DEBUG
        return true if self.remain_time() > 0
        return false
        # dll_path = self.get_dll_path
        # api = Win32API.new(dll_path, 'LinkKey', ['I', 'I'], 'I')
        # key_single_net_flag = self.get_key_single_net_flag
        # key_single_net_flag = key_single_net_flag.to_i
        # is_linked = api.call(23,key_single_net_flag)
        # is_linked = is_linked.to_i
        # #p "LinkKey, 是否连接到PKPM的锁：#{is_linked}"
        # if is_linked == 1
        #     return true
        # else
        #     UI.messagebox "无法连接到软件锁，请检查软件锁接入情况！"
        #     return false
        # end
    end

    #通常软件在使用过程中可以调用此函数，验证锁是否当前还插在电脑上，避免一开始插锁，LinkKey成功后就拔掉的情况
    def self.read_key()
    # Function:
    # Checks the connection status of the PKPM software license key (hardware dongle) by calling a native DLL function.
    # Displays a warning message if the key is not detected and returns the connection status.
    # Skips the check in debug mode or under specific network and hardware key conditions.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # Boolean:
    # true if the software license key is properly connected or if running in debug mode;
    # false if the key is not detected or if execution is skipped due to network/hardware conditions.
        return true if MoosasConstant::PLUGIN_DEBUG

        #当是网络版且是硬件锁时，建议不要调用ReadKey，因为若用户的网络环境不好时，此函数执行效果不稳定
        key_single_net_flag = self.get_key_single_net_flag
        is_hard_key = self.link_flag_is_hard_key
        if key_single_net_flag == "255" and is_hard_key
            return
        end

        dll_path = self.get_dll_path
        api = Win32API.new(dll_path, 'ReadKey', ['I'], 'I')
        is_still_linked = api.call(23)
        is_still_linked = is_still_linked.to_i
        #p "ReadKey, 是否仍然连接到PKPM的锁：#{is_still_linked}" 
        if is_still_linked == 1
            return true
        else
            UI.messagebox "软件锁不在线，请检查软件锁接入情况！"
            return false
        end
    end

    #关闭PKPM的锁/授权
    def self.close_key()
    # """
    # Function
    # --------
    # Closes the PKPM license/authorization key by calling a native DLL function.
    # 
    # This method conditionally executes only when plugin debugging is disabled.
    # It retrieves the DLL path and invokes the 'CloseKey' function from the native
    # library with no parameters, effectively closing the authorization key used by PKPM.
    # 
    # Parameters
    # ----------
    # None
    # 
    # Returns
    # -------
    # nil
    # Returns immediately without action if MoosasConstant::PLUGIN_DEBUG is true;
    # otherwise, returns after calling the native CloseKey function.
    # """
        return if MoosasConstant::PLUGIN_DEBUG
        dll_path = self.get_dll_path
        api = Win32API.new(dll_path, 'CloseKey', [], 'V')
        api.call()
        #p "CloseKey, 关闭PKPM的锁/授权" 
    end


    #获取dll的路径
    @dll_path = nil
    def self.get_dll_path()
    # Function:
    # Determines and returns the file path to the appropriate DLL based on the system architecture (32-bit or 64-bit).
    # The path is cached in the class variable `@dll_path` to avoid repeated computation.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # str: The file system path to the DLL (`pkpmGreenModelFun.dll`) located in either the 32_bit or 64_bit subdirectory,
    # depending on the result of `self.get_os_architecture`. The path is constructed relative to the current file's directory.
        if @dll_path == nil
            os_arch = self.get_os_architecture
            if os_arch == "x64"
                @dll_path = File.dirname(__FILE__)+"/../lock/64_bit/pkpmGreenModelFun.dll"
            else
                @dll_path = File.dirname(__FILE__)+"/../lock/32_bit/pkpmGreenModelFun.dll"
            end
        end
        return @dll_path
    end


    #获取当前锁的标志，是单机版还是网络锁，单机版时传126、网络版时传255
    @key_cfg = nil #指定读取key_single_net_flag的文件地址
    @key_single_net_flag = nil #单机版时传126、网络版时传255
    def self.get_key_single_net_flag
    # Function:
    # Retrieves the single network flag value used for PKPM software configuration.
    # This method first checks if the flag is already set in the instance variable.
    # If not, it attempts to read the 'DestInterrupt=' value from the PKPM.INI configuration file.
    # A default value of 255 is assigned if the flag is uninitialized and no configuration is found.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # int: The value of the single network flag, typically read from the 'DestInterrupt=' line
    # in the PKPM.INI file, or 255 if not set or file/config is unavailable.
        @key_single_net_flag = 255
        return @key_single_net_flag
        '''
        if @key_single_net_flag == nil
            if @key_cfg == nil
                self.get_pkpm_registry_key
            end
            pkpm_init_path = @key_cfg + "/PKPM.INI"  #获取文件
            #从文件中读取DestInterrupt=这行的值
            File.open(pkpm_init_path,"r") do |file|  
                while line = file.gets  
                    if line.start_with? "DestInterrupt="
                        arr = line.split("=")
                        @key_single_net_flag = arr[1].strip
                        break
                    end
                end  
            end
        end
        '''
        return @key_single_net_flag
    end


    #判断是否为硬件锁
    @key_auth_code = nil  #值若不是1，就代表是硬件锁
    def self.link_flag_is_hard_key
    # """
    # Function
    # --------
    # Determines whether the link flag is set as a hard key based on the authorization code.
    # 
    # Parameters
    # ----------
    # None
    # This is a class method and does not take any explicit parameters. It relies on the
    # instance variable `@key_auth_code` and may call `get_pkpm_registry_key` to initialize it.
    # 
    # Returns
    # -------
    # bool
    # Returns `False` if `@key_auth_code` is "1", indicating the link flag is not a hard key.
    # Returns `True` otherwise, including when `@key_auth_code` is nil or any value other than "1".
    # """
        if @key_auth_code == nil
            self.get_pkpm_registry_key
        end
        if @key_auth_code == "1"
            return false
        else
            return true   #
        end
    end

    def self.get_pkpm_registry_key
    # """
    # Function
    # ----------
    # get_pkpm_registry_key
    # Reads PKPM software registry information from the Windows Registry under HKEY_LOCAL_MACHINE.
    # Specifically retrieves the values of 'KeyAuthCode' and 'CFG' from the registry key obtained via `get_pkpm_key_name`.
    # 
    # Parameters
    # ----------
    # None
    # This is a class method with no parameters. It internally calls `self.get_pkpm_key_name()` to obtain the registry key path.
    # 
    # Returns
    # -------
    # None
    # This method does not return a value. It sets instance variables `@key_auth_code` and `@key_cfg` with the corresponding registry values.
    # """
        key_name = self.get_pkpm_key_name()
        Win32::Registry::HKEY_LOCAL_MACHINE.open(key_name) do |reg|
            @key_auth_code = reg["KeyAuthCode"]
            @key_cfg = reg["CFG"]
        end
    end

    #获取pkpm_注册表
    @key_name = nil
    def self.get_pkpm_key_name()
    # Function:
    # Retrieves the registry key name used to locate the PKPM installation path based on the system architecture.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # str: The Windows registry key path as a string. Returns "SOFTWARE\\Wow6432Node\\PKPM\\MAIN\\PATH" for 64-bit systems,
    # and "SOFTWARE\\PKPM\\MAIN\\PATH" for 32-bit systems. The value is cached in the class instance variable @key_name.
        if @key_name == nil
            os_arch = self.get_os_architecture
            if os_arch == "x64"
                @key_name = "SOFTWARE\\Wow6432Node\\PKPM\\MAIN\\PATH"
            else
                @key_name = "SOFTWARE\\PKPM\\MAIN\\PATH"
            end
        end
        return @key_name
    end

    #获取操作系统版本
    def self.get_os_architecture()
    # Function:
    # Determines and returns the system architecture for Windows platforms based on the RUBY_PLATFORM constant.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # str: Returns "x64" if the platform is 64-bit Windows, "x86" if it is 32-bit Windows.
    # Raises a RuntimeError if the operating system is not supported (i.e., not Windows).
        case RUBY_PLATFORM
        when /win/i, /ming/i 
            if RUBY_PLATFORM.include?"x64"
                return "x64"
            else
                return "x86"
            end
        else
            raise "暂时只支持windows操作系统!" 
        end
    end


    #吕帅的50个验证码
    @authorize_code = ['1774f6eca21bb97be2a81dcbc3799da53ac921e9','c735c2fb86793f7dbc6cfb6dcd711dfc60fa0bcd','307d98c36755489b871a016e9c77aaa39d6fed57','885f40b34c50a6a5974f7f1283d7db400e894513','163505460aa670e76201cfe2ff6462d3b603f3dd','c6f776a6c4eca54eaa9641c7416a5234b8aa1bfb','d138da99c35d4843c4b57d71f71dd14d75cf6366','16bf4443e87372e09bc8945d26ff73f1d40df8b6','45164e26f691e224c983dc9a37b4b37080f9e95e','e3e9cc2eaae120535a8cdea3f0153c4f724f7aee','1887a567fe6c18e59d379068b437380c69ef79ec','bc88cc859a2b1534b672812d81576398e81aeda5','a6dff52d26d0acdb715af9b9b2582fc88ea6121b','0a74fc8933717d29d7c98334a1951043c5dafec8','8fbc3f4e80d9617f3d06437c725e2a462cf8836d','0a5510ee747c8582be88d061c8a5bf0c4ab8877d','ffc4cd26422dbdf844da8bd8acff19fa223f6bfe','d8f13ccf575a00ad0943d52ea6d60fd902ec17ad','1cf236e72ca7be98a4a07d478dcd400c79615ad2','6c7cc7cdb58aba825753bd4020c1bdf5a4a479db','4f2386e14aab7f7d1f97a96b56dc3e87fec5dd04','cbb7cc5d7e9cc681fc3f98dacdf28ab32d34a727','28402dbfac23043965a823308ca4503e3ff573f7','2e055c84caea9502789655ecab28a267cebe5792','29fda174dc1dd6e3d2f000ea2cdc7bc76262f583','a72e6b7cfde1a0f26005fe8b4f558e705358c9a6','f5fd58ac62ef4e0e2d2521eb8e4a8b7eb9cbf2d4','fbee9828d8f0606bbd16e72c83c199c58cfdd597','0ad194203f2164ce2379c450d9517fa4f9df1d34','6c776147104ebc2382ef172cfbe12ad7362087d6','c70f1fb1c5c8ce815aa2f710af75bfe1405783be','6b284ac835a5f8b492f14d2e07bc1e64cf4bbcf8','7a3c9ea2a53929f2dc040715b572f75847723880','004a1952d99f0e3399d4e21ff1f2915c4cc78be4','861aa485830d8d0c06bbad48847d1f30de733580','6c942226819fde6329f6ce048d4a272d96e4bf5d','af95da451af79cdf3d1b0cbc771d322607aad615','e0e54c0bb4ee4184849a612b888685e6706f9259','9aa88fba22f398608cf6857da29786f8fd2834af','3f8a3ecab7735d6b7d2869f60905a47ba3c41140','07de1d19cd4037eb97db702e9090ed498d4b7c83','a9562e360bb46aa2428e53d1639181daebf2a5fb','616e435fcc097b324d7ef9c8a9a5ffddf40fa053','ce18b6fc82f8e8909e346c7dab862143cbbd35bb','656bc85c31f4ff0b3d1b4bf3216e9fee03908b65','9d64ed565ab43c2ed47a942077bda32c95c91b78','44d8bb58c8c805911e7499a9761888ee8b044f5a','a77fea6c533c66c2afef0f7c33ac4b17cd951255','38b791360b4131ce0efbf38f8dd976684b857bed','d2447bf118aaa349dbc4986f2de4507c2aca176e']
    def self.check_authorize_code()
    # Function
    # --------
    # Check the authorization code for the PKPM-MOOSAS software by verifying a SHA1-hashed license key either from a local file or user input.
    # 
    # The method first attempts to read an existing authorized code from a local settings file. If not found or invalid, it prompts the user to enter a new authorization code.
    # The entered code is hashed using SHA1 and checked against a predefined list of valid codes (`@authorize_code`). If valid, the hash is saved to the settings file for future use.
    # 
    # A hardcoded expiration date (2020-12-31) exists in the system but is not directly enforced within this method.
    # 
    # Parameters
    # ----------
    # None
    # This is a class method with no parameters. It relies on class variables (e.g., `@authorize_code`) and file I/O operations.
    # 
    # Returns
    # -------
    # Boolean
    # Returns `true` if the authorization code is valid (either from file or user input), `false` otherwise.
    # Exceptions during file operations or invalid inputs also result in `false`.
        begin
            #读取本地授权码
            setting_file = File.dirname(__FILE__)+"/../db/settings.moosas"
            lines = IO.readlines(setting_file)
            sha1 = lines[0].gsub("\n",'').gsub("\r",'')
            if sha1 != nil and sha1 != "" and @authorize_code.include?(sha1)
                return true
            end
            #如果没有本地授权码，再请用户输入
            prompts = ["授权码(xxxx-xxxx-xxxx)："]
            defaults = [""]
            input = UI.inputbox(prompts, defaults, "请输入PKPM-MOOSAS软件使用授权码")
            input_code = input[0]
            sha1 = Digest::SHA1.hexdigest(input_code)

            if @authorize_code.include? sha1
                File.open(setting_file,"w+") do |f|
                    f.puts sha1
                end
                return true
            else
                return false
            end
        rescue Exception => e
            return false
        end
    end

    #硬编码检查过期时间2020-12-31
    def self.check_expire()
    # Function:
    # Checks whether the current time has exceeded a predefined expiration time.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # bool: Returns True if the current time is on or after the expiration time (December 31, 2020, 00:00:00); otherwise, returns False.
        expire_time = Time.local(2020,12,31,0,0,0,0)
        now = Time.now

        if now < expire_time 
            return false
        else
            return true
        end
    end

    #从远程获取登录许可
    def self.remote_validate()
    # Function:
    # Perform a remote validation check by sending an HTTP request to a specified URL to determine if the software should be allowed to run based on the server response. If the response indicates a high crash possibility (100 or above), the validation fails.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # bool: Returns false if the remote response contains "pkpmvalidate" with a crash possibility greater than or equal to 100.0; otherwise, returns true. Also returns true if an exception occurs during the request or if Sketchup is offline.
        begin
            if Sketchup.is_online
                request = Sketchup::Http::Request.new("http://www.moosas.cn/pkpm_validate", Sketchup::Http::GET)
                request.start do |request, response|
                    text = response.body
                    #格式pkpmvalidate_xx
                    if text != nil and text.include?("pkpmvalidate")
                        arr = text.split("_")
                        possibility_to_crash = arr[1].to_f
                        if possibility_to_crash >= 100.0
                            return false
                        end
                    end
                end
            end
        rescue Exception => e
            return true
        end
        return true
    end

    #离线验证码版本（给吕帅的验证版本）
    # @pass_checked = false
    # def self.valid()
    #     if @pass_checked
    #         return true
    #     else
    #         if self.check_expire()  #过期检测
    #             UI::messagebox("此版本PKPM-MOOSAS试用插件已经过期!")
    #             @pass_checked = false
    #         else
    #             #软件使用码检测
    #             if  self.check_authorize_code
    #                 @pass_checked = true
    #             else
    #                 UI::messagebox("验证失败，请输入正确的授权码!")
    #                 @pass_checked = false
    #             end
    #         end
    #         return @pass_checked
    #     end
    # end

    #PKPM联机验证版本
    def self.valid()
    # Function:
    # Returns the link key associated with the class by invoking the class method `link_key`.
    # 
    # Parameters:
    # None
    # 
    # Returns:
    # The value returned by the `link_key` class method, which is typically a unique identifier or key used for linking purposes.
        return self.link_key()
    end

end