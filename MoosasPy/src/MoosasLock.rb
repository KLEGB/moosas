
require 'win32/registry'
require 'Win32Api'  
require "digest/sha1"

class MoosasLock
    p 'MoosasLock Ver.0.7.1'
    @exp_date = [2025,9,1]
    
    #连接到PKPM的锁或授权，连接成功返回true
    def self.remain_time()
        time=Time.new
        date = [time.year,time.month,time.day]
        date = date[0] * 365 + date[1] * 30 + date[2]
        expd = @exp_date[0] * 365 + @exp_date[1] * 30 + @exp_date[2]
        return expd-date
    end

    p "Expired after: #{self.remain_time()} days"
    
    def self.link_key()
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
        return if MoosasConstant::PLUGIN_DEBUG
        dll_path = self.get_dll_path
        api = Win32API.new(dll_path, 'CloseKey', [], 'V')
        api.call()
        #p "CloseKey, 关闭PKPM的锁/授权" 
    end


    #获取dll的路径
    @dll_path = nil
    def self.get_dll_path()
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
        key_name = self.get_pkpm_key_name()
        Win32::Registry::HKEY_LOCAL_MACHINE.open(key_name) do |reg|
            @key_auth_code = reg["KeyAuthCode"]
            @key_cfg = reg["CFG"]
        end
    end

    #获取pkpm_注册表
    @key_name = nil
    def self.get_pkpm_key_name()
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
        return self.link_key()
    end

end