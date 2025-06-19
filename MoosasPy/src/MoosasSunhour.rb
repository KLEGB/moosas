
class MoosasSunHour
    Ver='0.6.3'
    DAY = 60*60*24

    # Called when the menu item is clicked, this sets up the parameters dialog and passes the parameters
    # to sunlight_analyse_grids_params.
    def self.sunhour_analyse_grids(params="default 1 21 12 21 12 1 1 7 00 18 00 t t t t t t t 1 f f")
        Sketchup.active_model.start_operation("日照分析", true)

        model = Sketchup.active_model

        #scaleObserver = Moosas::GridScaleObservers[model]
        #scaleObserver.closeScale() if scaleObserver
        #scaleObserver.clearGridStasticsInfo() if scaleObserver
        
        selection = model.selection
        # Find all grids in the selection
        grids = []
        selection.each { |ent|
            # A grid is identified by having the "SunHours_grid_properties" attribute dictionary
            if ent.attribute_dictionaries and ent.attribute_dictionaries["grid"]
                grids << ent
            end
        }
        # If no grids are found in the selection, inform the user and stop immediately
        if grids.length == 0
            ent=MoosasGrid.fit_grids()
            if ent==nil
                p "网格拾取失败，请拾取网格并重新运行"
                return 
            else
                grids=ent
            end
        end
        self.sunhour_analyse_grids_params(params, grids)

        Sketchup.active_model.commit_operation
    end


    # For each grid:
    #   For each period of days:
    #       For each day in the period:
    #           For each time period in the day:
    #               Iterate through the period, advancing by the time step
    #                   For every valid node in the grid:
    #                       Determine if the node is in the sun
    #   Colour the grid
    def self.sunhour_analyse_grids_params(parameters_string, grids)
        
        begin
            model = Sketchup.active_model
            shinfo = model.shadow_info
            entities = model.active_entities
            selection = model.selection
            model_dict = model.attribute_dictionary("Grids", false)

            parameters = parameters_string.split
            action_name = parameters.shift

            ### Getting the parameters from the interface

            # Fetch date periods in the form:
            # [ [ [startDay0, startMonth0], [endDay0, endMonth0] ] , [ [startDay1, startMonth1], [end...] ] , ... ]
            dates = []
            datePeriods = (parameters.shift).to_i
            for n in 0...datePeriods
                n = n.to_s
                dates << [ [(parameters.shift).to_i, (parameters.shift).to_i] , \
                           [(parameters.shift).to_i  , (parameters.shift).to_i  ] ]
            end

            # Fetch time periods in a similar form to the dates, except that that form represents a single type
            times = []
            types = (parameters.shift).to_i
            for m in 0...types
                timePeriods = (parameters.shift).to_i
                type = []
                for n in 0...timePeriods
                    type << [ [(parameters.shift).to_i, (parameters.shift).to_i] , \
                               [(parameters.shift).to_i  , (parameters.shift).to_i ] ]
                end
                times << type
            end

            # Fetch weekdays to include (an array of booleans: t means include)
            weekdays = []
            for m in 0...types
                weekdays << (0...7).collect { |i| parameters.shift=="t" }
            end

            # Granularity of the calculation: time step in hours
            timeStep = Float(parameters.shift)*3600
            
            # Whether or not to include minima and maxima in the CSV
            mins = (parameters.shift=="t")
            maxs = (parameters.shift=="t")

        rescue => error
            UI.messagebox("计算出错: " + error.message)
            raise
        end

        ##### ANALYSIS

        begin

            cost_time = 0
            ## Initialisation
            # Group the analysis of all grids into a single operation that can be undone in one go
            model.start_operation("分析日照", true)
            # Hide all grids so that they don't interfere with the calculation (they cast shadows)
            MoosasRender.hide_glazing
            entities.each { |ent| ent.hidden = true if ent.attribute_dictionaries and ent.attribute_dictionaries["grid"] }
            # Initialise here for scope: they will be needed after all grids have been analysed for export to file,
            # but get set to zero for each grid anyway
            totalDays = 0; totalTime = 0;

            # String containing all the data that will be exported to file
            #allResults = ""

            # Unrelated to grid ID: this is used when showing progress
            gridnum=0

            # This is so that after analysis the model's time can be reset to normal, especially so that shadows don't cover the model
            originalTime = shinfo["ShadowTime"]

            ## Actual analysis

            #临时统计达标率百分比
            ratios = []


            ave_sunhour = 0.0
            all_n = 0

            # For each grid
            grids.each { |grid|

                t1 = Time.new
                gridnum+=1

                # Fetch grid info
                dict = grid.attribute_dictionaries["grid"]
                nodes = dict["nodes"]
                is_surface = dict["is_surface"]
                norm = Geom::Vector3d.new(dict["norm"])

                # Number of grid cells in the x and y directions
                nx = nodes[0].length-1; ny = nodes.length-1

                # Give the grid an ID if it doesn't already have one
                if not dict["id"]
                    dict["id"] = model_dict["grid_id"]

                    # Update the model's next available ID
                    model_dict["grid_id"] += 1
                end

                #allResults += "\nGrid ID:, "+dict["id"].to_s+"\n\n"

                # Set up the three result grids (with zeroes) to store analysis results
                totalsGrid = []; maxGrid = []; minGrid = []
                for y in 0..ny
                    totalsGrid << [0]*(nx+1)
                    maxGrid << [0]*(nx+1)
                    minGrid << [1.0/0.0]*(nx+1)
                end

                totalTime = 0 # Maximum potential time in sun, in hours
                totalDays = 0

                # Iterate through periods of days
                for datePeriod in 0...datePeriods

                    # Note that all calculations are done in the year 2015
                    startDate = Time.utc(2015, dates[datePeriod][0][1], dates[datePeriod][0][0], 12)
                    shinfo["ShadowTime"] = startDate

                    endDate = Time.utc(2015, dates[datePeriod][1][1], dates[datePeriod][1][0]) + DAY

                    # Iterate through days in the period
                    while shinfo["ShadowTime"] <= endDate

                        # Selecting the appropriate type based on the weekday
                        excludeDay = true;

                        for type in 0...types
                            if weekdays[type][(shinfo["ShadowTime"].wday-1)%7]
                                excludeDay = false
                                break
                            end
                        end

                        # Excluding the day if no type has this weekday
                        if excludeDay
                            shinfo["ShadowTime"] += DAY
                            next
                        end

                        totalDays += 1

                        # Set up a grid of results for just that day (needed for min and max grids particularly)
                        dayGrid = []
                        for y in 0..ny
                            dayGrid << [0]*(nx+1)
                        end

                        timePeriods = times[type].length

                        # Iterate through time periods
                        for timePeriod in 0...timePeriods
                            startTime = shinfo["ShadowTime"].utc
                            startTime = Time.utc(2015, startTime.month, startTime.day, times[type][timePeriod][0][0], times[type][timePeriod][0][1], 0)
                            startTime = [startTime, shinfo["SunRise"].utc].max # Don't start analysis before sunrise
                            startTime += DAY*365*(2015-startTime.year) # Sometimes the year just changes when it calculates sunrise (particularly on the 31 Dec)

                            endTime = shinfo["ShadowTime"].utc
                            endTime = Time.utc(2015, endTime.month, endTime.day, times[type][timePeriod][1][0], times[type][timePeriod][1][1], 0)
                            endTime = [endTime, shinfo["SunSet"].utc].min # End analysis before sunset
                            endTime += DAY*365*(2015-endTime.year) # in case of same bug as above

                            totalTime += (endTime - startTime)/3600

                            shinfo["ShadowTime"] = startTime

                            while shinfo["ShadowTime"] < endTime

                                # For each node...
                                for y in 0..ny
                                    for x in 0..nx
                                        pt = nodes[y][x] # This is a Point3d (actually it's just a 3-element array)
                                        # If the node is valid (i.e. included in the grid)
                                        if pt
                                            # Add time to the results node if the point is in sun at the time
                                            # The raytest is the crucial test for sunlight. Hidden geometry (and hence analysis grids) is ignored
                                            ray = [pt, shinfo["SunDirection"]]
                                            intersection = model.raytest(ray)
                                            dayGrid[y][x] += [timeStep, endTime-shinfo["ShadowTime"]].min.to_f/3600 if !intersection
                                        end
                                    end
                                end
                                shinfo["ShadowTime"] += timeStep
                            end
                            # End of the time period
                        end
                        # End of the day
                        # Use the day grid to update the three main result grids
                        # For each node:
                        for y in 0..ny
                            for x in 0..nx
                                val = dayGrid[y][x]
                                totalsGrid[y][x] += val
                                maxGrid[y][x] = [maxGrid[y][x], val].max
                                minGrid[y][x] = [minGrid[y][x], val].min
                            end
                        end
                        # Show progress in the status bar (as text)
                        Sketchup.status_text=shinfo["ShadowTime"].strftime("已经分析 %d %b") + (grids.length>1 ? (" #{gridnum}个网格，总共有#{grids.length}个") : "")
                        # Next day (adding to a time advances it by seconds)
                        shinfo["ShadowTime"] += DAY
                    end
                    # End of period of days

                end
                # End of year and of analysis for this grid

                #临时统计
                blelow_2 = 0.0
                total_n = 0.0
                # Set all invalid nodes to -1 in the result grids
                for y in 0..ny
                    for x in 0..nx
                        if nodes[y][x]
                            total_n += 1
                            if totalsGrid[y][x] < 2
                                blelow_2 += 1
                            end
                            ave_sunhour += totalsGrid[y][x]
                            all_n += 1
                        end
                        totalsGrid[y][x] = maxGrid[y][x] = minGrid[y][x] = -1 if not nodes[y][x]     
                    end
                end

                ratios.push(1 - blelow_2/total_n)
                #p "日照达标率#{1 - blelow_2/total_n}"

                #self.remove_numbers_from_grid(grid)
                dict["results"] = totalsGrid
                dict["valueRange"] = totalTime
                dict["old_grid"] = false
                dict["type"] = "sunhour"
                #p "totalTime=#{totalTime}"

                t2 = Time.new
                # Update the progress in the status bar             
                Sketchup.status_text="分析了" + (grids.length>1 ? (" #{gridnum}个网格，总共有#{grids.length}个网格") : "") + "..."
                MoosasRender.show_all_face
                #MoosasGrid.color_grid(grid)

                ## Add the results from the 3 grids to the output string for exporting to file
                '''
                allResults += "Totals:\n\n"
                for y in 0..ny
                    line = ""
                    for x in 0..nx
                        line += totalsGrid[y][-1-x].to_s
                        line += ", " if x!=nx
                    end
                    allResults += line+"\n"
                end

                if mins
                    allResults += "\nMinimums:\n\n"
                    for y in 0..ny
                        line = ""
                        for x in 0..nx
                            line += minGrid[y][-1-x].to_s
                            line += ", " if x!=nx
                        end
                        allResults += line+"\n"
                    end
                end

                if maxs
                    allResults += "\nMaximums:\n\n"
                    for y in 0..ny
                        line = ""
                        for x in 0..nx
                            line += maxGrid[y][-1-x].to_s
                            line += ", " if x!=nx
                        end
                        allResults += line+"\n"
                    end
                end
                '''

                cost_time = cost_time + (t2-t1)

            }
            # All grids analysed
            #p "日照达标率总计：#{ratios}"

            # Color Grids
             grids.each { |grid|
                Sketchup.status_text="渲染了" + (grids.length>1 ? (" #{gridnum}个网格，总共有#{grids.length}个网格") : "") + "..."
                MoosasGrid.color_grid(grid)
             }


            p "日照分析时间 #{cost_time}"
            # Return the model time to what it was before analysis
            shinfo["ShadowTime"] = originalTime

            ave_sunhour = ave_sunhour / all_n
            p "日照小时数平均值:#{ave_sunhour}"

            # Unselect and reselect the grids so that the selection observer shows the scale
            selection.clear
            selection.add(grids)

            description="Direct Sun Hour\nLocation:#{MoosasWeather.singleton.station_info["city"]}\nPriod:Annual"
            scaleRender=MoosasGridScaleRender.new(0,(ave_sunhour*2).round(0),description = description,unit='h',colors=MoosasGrid.color_setting["sunhour"]["colours"])
            scaleRender.draw_panel(Sketchup.active_model.selection)

            #Moosas::GridScaleObservers[model].showScale
            #Moosas::GridScaleObservers[model].showGridStasticsInfo

            # Show all grids again (they were hidden to avoid interfering with the calculation)
            entities.each { |ent| ent.hidden = false if ent.attribute_dictionaries and ent.attribute_dictionaries["grid"] }

            # Complete the "Analyse grids" operation
            model.commit_operation
        rescue => error
            model.abort_operation
            UI.messagebox("日照分析出现错误: " + error.message)
            raise
        end
        # Clear the status bar which was showing progress
        Sketchup.set_status_text("")
    end
    # End of sunlight_analyse_grids_params function definition
end


