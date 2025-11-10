# frozen_string_literal: true

module MoosasIDF
  require 'csv'
  require 'json' # 用于安全转换Ruby数据为JavaScript对象
  require 'fileutils'

  RUN_SCRIPT = "#{MPath::LIB}energy/run_idf.py"
  READ_SCRIPT = "#{MPath::LIB}energy/read_idfSql.py"
  HEATING_COP = 1.8
  COOLING_COP = 3.0
  @summary = nil
  @simulated = false

  def self.run_idf()
    if @simulated
      visualize(@summary)
      return
    end
    UI.messagebox("Select a epw file")
    epw_file = UI.openpanel("Open Epw File", "c:/", "Epw Files|*.epw;*.csv;||")
    if epw_file != nil
      if UI.messagebox("Using Customize IDF template?", MB_YESNO) == IDYES
        idf_template = UI.openpanel("Open idf File", "c:/", "idf Files|*.idf;||")
        if idf_template == nil
          idf_template = MPath::DB + "default.idf"
        end
      else
        idf_template = MPath::DB + "default.idf"
      end
      idfFile = []
      code = ["from MoosasPy import loadModel,IO"]
      for owl in $ontologies
        filename_with_ext = File.basename(owl)
        # => "report.pdf"（以第一个路径为例）

        # 2. 获取扩展名（含小数点，如 .pdf、.log）
        ext = File.extname(filename_with_ext)
        # => ".pdf"

        # 3. 去除后缀，得到纯文件名
        filename_without_ext = filename_with_ext.chomp(ext)
        targetIDF = MPath::DATA + "energy/#{filename_without_ext}.idf"
        code.push("model = loadModel('#{owl}')")
        code.push("IO.writeIDF('#{targetIDF}',model,'#{idf_template}')")
        idfFile.push(targetIDF)
      end
      MoosasUtils.exec_python("writeIDF.py", code, console = true)

      # run idf
      Dir.chdir MPath::PYTHON
      outs = []
      for idf in idfFile
        cmd = ".\\python.exe \"#{RUN_SCRIPT}\" -w \"#{epw_file}\" \"#{idf}\""
        p "run #{File.basename(idf)}"
        system(cmd)
        sql = idf.chomp(".idf") + "\\#{File.basename(epw_file).chomp(".epw")}out.sql"
        out = idf.chomp(".idf") + ".csv"
        cmd = ".\\python.exe \"#{READ_SCRIPT}\" -o \"#{out}\" \"#{sql}\""
        p "read #{File.basename(sql)}"
        system(cmd)
        outs.push(out)
      end
      summary = MPath::DATA + 'energy/idf_summary/'

      total_energy = sum_multiple_csvs(outs, summary + 'raw.csv')
      process_hourly(summary + 'raw.csv', summary + 'hourly.csv')
      process_monthly(summary + 'raw.csv', summary + 'monthly.csv')
      process_typical_days_per_month(summary + 'raw.csv', summary)
      generate_info(total_energy,summary + 'info.txt')
      @simulated = true
      @summary = summary
      visualize(summary)
    end
  end

  def self.generate_info(total_energy,out_path)
    totalOutsideArea, totalVolume = 0, 0
    facadeArea, windowArea = 0, 0
    $current_model.spaces.each do |s|
      totalVolume += s.area_m * s.height_m
      s.bounds.each do |b|
        unless b.is_internal_edge
          totalOutsideArea += b.area_m
          facadeArea += b.area_m * (1 - b.wwr)
          windowArea += b.area_m * b.wwr
        end
      end

      s.ceils.each do |c|
        if c.type == MoosasConstant::ENTITY_ROOF
          totalOutsideArea += c.area_m
        elsif c.type == MoosasConstant::ENTITY_SKY_GLAZING
          totalOutsideArea += c.area_m
        end
      end
    end
    txt = ["Space Number : #{$current_model.spaces.length}"]
    txt.push("Total Energy : #{total_energy.round(2)} kWh/m2")
    txt.push("Gross Floor Area : #{$current_model.get_total_area.round(2)} m2")
    txt.push("Shape Factor : #{(totalOutsideArea/totalVolume).round(2)}")
    txt.push("Average WWR : #{(windowArea/facadeArea).round(2)}")
    txt.join("\n")
    File.open(out_path,"w+") do |f|
      f.puts(txt)
    end
  end

  def self.visualize(summary_dir)
    # 1. 路径配置

    # 模板文件路径（确保与插件中模板的实际位置一致）
    if $language == 'Chinese'
      template_path = File.join(MPath::LIB, 'ui', 'idf_view_CN.html')
    else
      template_path = File.join(MPath::LIB, 'ui', 'idf_view.html')
    end
    template_path = File.expand_path(template_path)

    # 2. 检查模板文件是否存在
    unless File.exist?(template_path)
      UI.messagebox("HTML模板文件不存在:\n#{template_path}\n请确认idf_view.html的位置")
      return false
    end

    begin
      # 4. 读取数据（Ruby中读取，准备嵌入HTML）
      # 4.1 建筑信息
      info_txt = if File.exist?("#{summary_dir}/info.txt")
                   File.read("#{summary_dir}/info.txt", encoding: 'utf-8')
                 else
                   "未找到info.txt文件"
                 end

      # 4.2 逐时数据
      hourly_data = CSV.read(summary_dir + '/hourly.csv', headers: true).map(&:to_h)

      # 4.3 逐月数据
      monthly_data = CSV.read(summary_dir + '/monthly.csv', headers: true).map(&:to_h)

      # 4.4 典型日数据
      typical_data = {
        1 => CSV.read("#{summary_dir}/typical_day_month_1.csv", headers: true).map(&:to_h),
        4 => CSV.read("#{summary_dir}/typical_day_month_4.csv", headers: true).map(&:to_h),
        7 => CSV.read("#{summary_dir}/typical_day_month_7.csv", headers: true).map(&:to_h),
        11 => CSV.read("#{summary_dir}/typical_day_month_11.csv", headers: true).map(&:to_h)
      }

      # 4.5 全年总和（饼图）
      cooling_total = hourly_data.sum { |row| row['sensible cooling'].to_f } / 1000
      heating_total = hourly_data.sum { |row| row['sensible heating'].to_f } / 1000
      lighting_total = 15

      # 4.6 整合所有数据为JSON
      app_data = {
        hourly: hourly_data,
        monthly: monthly_data,
        typical: typical_data,
        totals: {
          cooling: cooling_total.round(2),
          heating: heating_total.round(2),
          lighting: lighting_total
        }
      }
      app_data_json = JSON.generate(app_data)

    rescue => e
      UI.messagebox("数据读取失败:\n#{e.message}")
      return false
    end

    begin
      # 5. 读取HTML模板并替换占位符
      template_content = File.read(template_path, encoding: 'utf-8')

      # 替换占位符（注意转义特殊字符）
      final_html = template_content
                     .gsub('{{info_txt}}', info_txt) # 转义HTML特殊字符
                     .gsub('{{app_data_json}}', app_data_json)

    rescue => e
      UI.messagebox("模板处理失败:\n#{e.message}")
      return false
    end

    # 6. 显示生成的HTML
    @dialog = UI::HtmlDialog.new(
      {
        :dialog_title => "Moosas IDF Visualization",
        :preferences_key => "PkpmMoosasPlugin",
        :scrollable => true,
        :resizable => true,
        :width => @width || 1200,
        :height => @height || 800,
        :min_width => 500,
        :min_height => 400,
        :style => UI::HtmlDialog::STYLE_DIALOG,
        :debug => true
      }
    )

    @dialog.set_html(final_html)
    @dialog.show
    true
  end

  def self.sum_multiple_csvs(input_files, output_file)
    # """
    # Sums data from multiple CSV files with the same structure (8760*4) by corresponding rows.
    # The 'hour' column remains unchanged, while the other three columns are summed numerically.
    #
    # Parameters
    # ----------
    # input_files : Array<String>
    #     Array of input CSV file paths (e.g., ["file1.csv", "file2.csv"]).
    # output_file : String
    #     Path for the output CSV file to store the summed results.
    #
    # Raises
    # ------
    # ArgumentError
    #     If any input file does not exist.
    # RuntimeError
    #     If any file contains invalid 'hour' values (not in 0-8759), inconsistent row order,
    #     or an incorrect number of rows (not 8760).
    # """
    # Initialize sum results: 8760 rows, each containing hour and three columns with initial value 0
    # Structure: [{ hour: 0, lights: 0.0, cooling: 0.0, heating: 0.0 }, ...]
    total_area = 0
    $current_model.spaces.each do |s|
      total_area += s.area_m
    end
    total_energy = 0.0
    sum_results = Array.new(8760) do |i|
      {
        hour: i,
        lights: 0.0,
        cooling: 0.0,
        heating: 0.0
      }
    end

    input_files.each do |file|
      # Check if file exists
      unless File.exist?(file)
        raise ArgumentError, "File does not exist: #{file}"
      end

      row_count = 0 # Record the number of rows read from the current file
      CSV.foreach(file, headers: true) do |row|
        # Parse the 'hour' value of the current row (should be 0 to 8759)
        current_hour = row["hour"].to_i

        # Validate hour legality (must be in 0-8759 and consistent with row index)
        if current_hour < 0 || current_hour >= 8760
          raise "Invalid hour in file #{file}: #{current_hour} (must be 0-8759)"
        end
        if current_hour != row_count
          raise "Row order exception in file #{file}: The hour of row #{row_count + 1} should be #{row_count}, but is actually #{current_hour}"
        end

        # Sum the three columns (convert to float to avoid string concatenation)
        sum_results[current_hour][:lights] += row["lights electricity"].to_f / total_area
        sum_results[current_hour][:cooling] += row["sensible cooling"].to_f / total_area / COOLING_COP
        sum_results[current_hour][:heating] += row["sensible heating"].to_f / total_area / HEATING_COP
        total_energy += row["sensible cooling"].to_f / total_area / COOLING_COP
        total_energy += row["sensible heating"].to_f / total_area / HEATING_COP
        row_count += 1
      end

      # Validate that the file has exactly 8760 rows
      unless row_count == 8760
        raise "Row count exception in file #{file}: Should be 8760 rows, but is actually #{row_count} rows"
      end

      puts "Completed summing file: #{file}"
      return total_energy/1000
    end

    # Write the summed results to the output file
    CSV.open(output_file, "w") do |out_csv|
      # Write header (maintain original structure)
      out_csv << ["hour", "lights electricity", "sensible cooling", "sensible heating"]
      # Write each row of summed data
      sum_results.each do |row|
        out_csv << [
          row[:hour],
          row[:lights],
          row[:cooling],
          row[:heating]
        ]
      end
    end

    puts "All files summed successfully. Result exported to: #{output_file}"
  end

  def self.get_month(hour)
    # """
    # Calculates the corresponding month (1-12) based on the hour number (0-8759) in a non-leap year.
    #
    # Parameters
    # ----------
    # hour : Integer
    #     Hour number in the year (0-8759).
    #
    # Returns
    # -------
    # Integer
    #     Corresponding month (1-12).
    # """
    # Cumulative hours for each month in a non-leap year (index 0 is the start, 1-12 correspond to the end of months 1-12)
    monthly_hours = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
    (1..12).each do |month|
      return month if hour < monthly_hours[month]
    end
    12 # Ensure the last hour is correctly categorized
  end

  # 1. Generate hourly data CSV (including month information)
  def self.process_hourly(input_path, output_path)
    # """
    # Generates an hourly CSV file containing specific datetime information (mm-dd hh:00 format),
    # excluding the 'lights electricity' column. Converts the 'hour' column (0-8759) to corresponding datetime.
    #
    # Parameters
    # ----------
    # input_path : String
    #     Path of the input CSV file.
    # output_path : String
    #     Path for the output hourly CSV file.
    # """
    # Days in each month (non-leap year)
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    # Cumulative days up to each month (index 0 = 0 days, index 1 = days in Jan, index 2 = Jan+Feb, etc.)
    cumulative_days = [0]
    days_in_month.each { |days| cumulative_days << cumulative_days.last + days }

    CSV.open(output_path, "w") do |out_csv|
      # Update header to "datetime" for the first column
      out_csv << ["datetime", "sensible cooling", "sensible heating"]

      CSV.foreach(input_path, headers: true) do |row|
        hour = row["hour"].to_i
        cooling = row["sensible cooling"].to_f
        heating = row["sensible heating"].to_f

        # Calculate total days and current hour of the day
        total_days = hour / 24
        current_hour = hour % 24

        # Find corresponding month and day
        month = nil
        day = nil
        cumulative_days.each_with_index do |cum_days, idx|
          next if idx == 0 # Skip index 0 (0 days)
          if total_days < cum_days
            month = idx # Months are 1-based (1-12)
            day = total_days - cumulative_days[idx - 1] + 1 # Days are 1-based
            break
          end
        end

        # Format as mm-dd hh:00 (pad with leading zeros for single digits)
        formatted_datetime = sprintf("%02d-%02d %02d:00", month, day, current_hour)

        out_csv << [formatted_datetime, cooling, heating]
      end
    end
    puts "Hourly data with datetime generated: #{output_path}"
  end

  # 2. Generate monthly statistics CSV (sum by month)
  def self.process_monthly(input_path, output_path)
    # """
    # Generates a monthly CSV file with summed values of 'sensible cooling' and 'sensible heating' for each month.
    #
    # Parameters
    # ----------
    # input_path : String
    #     Path of the input CSV file.
    # output_path : String
    #     Path for the output monthly statistics CSV file.
    # """
    # Initialize monthly cumulative data (for months 1-12)
    monthly_totals = Hash.new { |h, k| h[k] = { cooling: 0.0, heating: 0.0 } }

    CSV.foreach(input_path, headers: true) do |row|
      hour = row["hour"].to_i
      cooling = row["sensible cooling"].to_f
      heating = row["sensible heating"].to_f
      month = get_month(hour)

      monthly_totals[month][:cooling] += cooling
      monthly_totals[month][:heating] += heating
    end

    CSV.open(output_path, "w") do |out_csv|
      out_csv << ["month", "sensible cooling", "sensible heating"]
      (1..12).each do |month|
        out_csv << [month, monthly_totals[month][:cooling], monthly_totals[month][:heating]]
      end
    end
    puts "Monthly statistics generated: #{output_path}"
  end

  # 3. Generate typical day statistics CSV (hourly averages for months 1,4,7,11)
  def self.process_typical_days_per_month(input_path, output_dir = ".")
    # """
    # Generates separate CSV files for typical day statistics of months 1, 4, 7, and 11.
    # Each file contains hourly averages (0-23) of 'sensible cooling' and 'sensible heating' for the month.
    #
    # Parameters
    # ----------
    # input_path : String
    #     Path of the input CSV file.
    # output_dir : String, optional
    #     Directory to store the output CSV files (default is current directory).
    # """
    target_months = [1, 4, 7, 11]

    target_months.each do |target_month|
      # Initialize hourly data for the month (grouped by hour 0-23)
      hourly_data = Hash.new { |h, k| h[k] = { coolings: [], heatings: [] } }

      CSV.foreach(input_path, headers: true) do |row|
        hour = row["hour"].to_i
        current_month = get_month(hour)
        # Only process data for the current target month
        next unless current_month == target_month

        day_hour = hour % 24 # Hour of the day (0-23)
        cooling = row["sensible cooling"].to_f
        heating = row["sensible heating"].to_f

        # Collect all data for this hour
        hourly_data[day_hour][:coolings] << cooling
        hourly_data[day_hour][:heatings] << heating
      end

      # Generate typical day CSV file for the month
      output_path = File.join(output_dir, "typical_day_month_#{target_month}.csv")
      CSV.open(output_path, "w") do |out_csv|
        out_csv << ["hour", "sensible cooling", "sensible heating"]
        (0..23).each do |h|
          coolings = hourly_data[h][:coolings]
          heatings = hourly_data[h][:heatings]
          # Calculate average (handle empty data, adjust in actual business scenarios as needed)
          avg_cooling = coolings.empty? ? 0.0 : coolings.sum / coolings.size.to_f
          avg_heating = heatings.empty? ? 0.0 : heatings.sum / heatings.size.to_f

          out_csv << [h, avg_cooling, avg_heating]
        end
      end
      puts "Typical day data for month #{target_month} generated: #{output_path}"
    end
  end
end