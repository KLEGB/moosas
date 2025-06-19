UI = {};


//页面每一次重新加载的时候，根据存储在skp端的数据，进行界面的初始化
UI.reset_ui = function(data){
	//alert(data.city);

	//UI.update_weather_chart(data.weather.data);

    //UI.update_geometry_info(data.geometry);
    //Skp.send("getUI.reset_ui",[data])
    UI.reset_settings(data)
}

UI.init_ui = function(){
    //以下初始化数据




    //以下初始化UI界面交互响应机制
	$('[data-toggle="tooltip"]').tooltip();

    $('#recognize_btn').on('click', function () {
        Skp.send("recognize_model",[" "]);
    });

    $('#enable_visualize_entity_type').on('click', function () {
        Skp.send("visualize_entity_type",[" "]);
    });

    $('#disable_visualize_entity_type').on('click', function () {
        Skp.send("disable_visualize_entity_type",[" "]);
    });

    $('#show_all_face').on('click', function () {
        Skp.send("show_all_face",[" "]);
    });



    $('#main_analysis').on('click', function () {
        UI.update_settings()
        Skp.send("main_analysis",[JSON.stringify(UI.settings)]);
        Skp.send("main_analysis",[JSON.stringify(params)]);
    });

    $('#optimize_energy_btn').on('click', function () {
        UI.run_optimize_energy_analysis();
    });    

    $("#update_optimize_energy_btn").on('click', function () {
        Skp.send("update_optimize_energy",[" "]);
    });    

    UI.init_all_sliders();

    $("#param_analysis_btn").on('click', function () {
        UI.run_param_analysis();
    });    

    $("#inputParamsAnalysisGoalType").on('change',function(){
        UI.update_params_plot_lengend_mode();
    });

    $("#recognize_result_stat div .col-2").on("click",function(){
        var type = $(this).find("h1").first().attr("id");
        $("#recognize_result_stat div .col-2").css("background-color","#ffffff");
        $(this).css("background-color","#28A745");
        var et = type.substr(7) * 1;
        Skp.send("visualize_one_entity_type",[et]);
    });

    $(".parameter_setting_input_apply_btn").on("click",function(){
        var tag = $(this).parent().parent().find(".parameter_setting_input").attr("tag");
        var value = $(this).parent().parent().find(".parameter_setting_input").val();
        Skp.send("update_parameter_setting",[tag,value]);
    });

    $("#render_daylight_in_skp_btn").on('click', function () {
        Skp.send("render_daylight_in_skp_btn",[" "]);
    });    

    UI.update_model=function (){
        Skp.send("update_model_data",[" "]);
    };

    UI.init_update_multi_goal_params_analysis_sensitive_chart();
    $(".multi_goal_params_analysis_btn").on('click', function () {
        var tag = $(this).attr("tag");
        var name = $(this).attr("name");
        UI.run_mutil_goal_param_analysis(tag,name);
    });  
    UI.settings={}
    //UI.update_settings()
}
UI.reset_settings=function(ui_settings){
    //Skp.send("getUI.reset_settings",[JSON.stringify(ui_settings)])
    var buildingType = $('#main_tab');
    UI.settings = ui_settings;
    buildingType.find("select").each(function(){
            var name = $(this).attr("id");
            
            $(this).val(ui_settings[name]);
        });
    $("#require_recognize_model").get(0).checked = UI.settings["recognize"];
    $("#require_radiation").get(0).checked = UI.settings["radiation"];
}
UI.update_settings=function(){
    var buildingType = $('#main_tab');
    buildingType.find("select").each(function(){
            var name = $(this).attr("id");
            var value = $(this).val();
            UI.settings[name] = value;
        });
    UI.settings["recognize"] = $("#require_recognize_model").get(0).checked;
    UI.settings["radiation"] = $("#require_radiation").get(0).checked;
    Skp.send("change_settings",[JSON.stringify(UI.settings)])
}
UI.energy_analysis=function () {
        UI.update_settings()
        Skp.send("main_analysis",[JSON.stringify(UI.settings)]);
    };
UI.daylight_analysis=function () {
        Skp.send("daylight_analysis",[" "]);
    }; 
UI.sunhour_analysis=function () {
        Skp.send("sunhour_analysis",[" "]);
    }; 
UI.radiance_analysis=function () {
        Skp.send("radiance_analysis",[" "]);
    }; 
UI.ventilation_analysis=function () {
        Skp.send("ventilation_analysis",[" "]);
    }; 
UI.space_params={}
UI.defaultPlotlyConfiguration ={
    modeBarButtonsToRemove: ['sendDataToCloud', 'autoScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'lasso2d', 'select2d'], 
    displaylogo: false, 
    showTips: true };

UI.ELEMENT_NAME_MAP = {
        "Glazing":"窗户",
        "Wall":"外墙",
        "Roof":"屋顶",
        "Floor":"楼板",
        "Ground Floor":"地板",
        "Shading":"遮阳",
        "Internal Wall":"内墙",
        "Internal Glazing":"内窗",
        "Sky Glazing":"天窗",
        "Party Wall":"隔墙",
        "Door":"门",
        "Ignore":"忽略"
};

UI.geometry = null;
UI.building_tree = null;
UI.update_geometry_info = function(g){
    UI.geometry = g;

    var z_ids;
    var z_list = [];
    var i,j;
    var f,s,z;
    var f_data,s_data, z_data;
    var floor_zone_map = new HashMap();
    var z_faces, f_zones;
    for(i = 0; i < g.zones.length; i++){
        z = g.zones[i];
        z_data = {};
        z_data.id =  i;
        z_data.text = "分区"+(i+1);
        z_data.checked = false;
        z_data.flagUrl = null;
        z_data.hasChildren = true;

        z_data.level = "zone";
        z_data.fn = z.fn;
        z_data.area = z.area;
        z_data.height = z.height;
        z_data.isOuter = z.isOuter;
        z_data.isGround = z.isGround;
        z_data.isRoof = z.isRoof;

        z_faces = [];
        z_ids = []; 
        for(j = 0; j < z.surfaces.length; j++){
            s = z.surfaces[j];
            s_data = {};

            s_data.id = s.id;
            s_data.text = UI.ELEMENT_NAME_MAP[s.type] + s.id;
            s_data.checked = false;
            s_data.flagUrl = null;
            s_data.hasChildren = false;
            s_data.children = [];

            s_data.level = "surface";
            s_data.cls = s.class;
            s_data.type = s.type;
            s_data.area = s.area;
            s_data.normal = s.normal.join(",");

            z_faces.push(s_data);
            z_ids.push(s.id);
        }
        z_data.ids = z_ids.join(",");
        z_data.children = z_faces;

        z_list.push(z_data);

        f_zones = floor_zone_map.get(z.fn);
        if(f_zones == null){
            f_zones = [];
        }
        f_zones.push(z_data);
        floor_zone_map.put(z.fn,f_zones);
    }

    var data = [];

    var keySet = floor_zone_map.keySet();
    keySet = keySet.sort();
    for(var fni in keySet){ 
        fn = keySet[fni];
        z_data = floor_zone_map.get(fn);

        f_data = {};
        f_data.id = 1000000 + fni * 1;
        f_data.level = "floor";
        f_data.text = "楼层" + fni;
        f_data.checked = false;
        f_data.flagUrl = null;
        f_data.hasChildren = true;
        f_data.children = z_data;

        data.push(f_data);
    }

    UI.building_tree = $('#building_tree').tree({
        uiLibrary: 'bootstrap4',
        dataSource: data,
        primaryKey: 'id',
        //imageUrlField: 'flagUrl',
        checkboxes: true,
        autoLoad: true,
        onhoverColor: "red"
    });

    UI.building_tree.on('select', UI.select_building_tree_node);

}


UI.select_building_tree_node = function(e, node, id){
    var data = UI.building_tree.getDataById(id);

    alert(data.level);
    if(data.level == "surface"){
        $(".building_params").css("visibility","hidden");
        $("#surface_params").css("visibility","visible");
    }else if(data.level == "zone"){
        $(".building_params").css("visibility","hidden");
        $("#zone_params").css("visibility","visible");
    }else if(data.level == "floor"){
        $(".building_params").css("visibility","hidden");
        $("#floor_params").css("visibility","visible");
    }
}

UI.load_weather_stations_data = function(data){

    var htmlText = "";
    var stations = data["stations"];
    for(var s in stations){
        htmlText += "<option value='"+ s +"''>" + stations[s]["city"] + "</option>"
    }
    $("#selectCity").html(htmlText);
    $("#selectCity").unbind("change");
    $("#selectCity").bind("change",function(){
        //alert($("#selectCity").val());
        var sid = $("#selectCity").val();
        Skp.send("update_weather_station",[sid]);
    });

    //选中当前城市
    var select_station_id = data["station_id"];
    $("#selectCity").val(select_station_id);
}

UI.update_weather_chart = function(data){


    var weather = eval('(' + data.weather + ')');

	var temperature = [];
	var humandity = [];
	var global_radiance = [];


	var year_days = [];
	var day_hours = ["1:00","2:00","3:00","4:00","5:00","6:00","7:00","8:00","9:00","10:00","11:00","12:00",
					 "13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00","23:00","24:00"];
	
	var wind_speed_step = [1.8,3.3,5.4,8.5,11.1,20.0]; //20.0 = 13.9
	var wind_step_label = ["<1.8 m/s","1.8-3.3 m/s","3.3-5.4 m/s","5.4-8.5 m/s","8.5-11.1 m/s",">11.1 m/s"];
	var wind_step_colors = ['#d73027','#fc8d59','#fee090','#e0f3f8','#91bfdb','#4575b4'];
	var wind_direction = ['N','NNE', 'NE','ENE', 'E', 'ESE','SE', 'SSE', 'S', 'SSW','SW','WSW', 'W', 'WNW', 'NW', 'NNW']; 
	var wind_rose_group = [[],[],[],[],[],[]];
	var wsi, wdi, ws, wd;
	for(wsi = 0; wsi < 6; wsi ++){
		for(wdi = 0; wdi < 16; wdi ++){
			wind_rose_group[wsi].push(0);
		}
	}

	var h, d;
	var hour_tem;
	var i ;

	var day_number = weather.length / 24;

	var date = new Date("2018-01-01");
	for(d = 1; d <= day_number; d++){
		year_days.push((date.getMonth()+1)+"/"+ (date.getDate()));
		date.setDate(date.getDate()+1);
	}

	for(h = 0; h < 24; h++){
		temperature.push([]);
		humandity.push([]);
		global_radiance.push([]);  
	}

	for(i = 0; i < weather.length; i++){
		h = i % 24;
		temperature[h].push(weather[i].t);
		humandity[h].push(weather[i].d);
		global_radiance[h].push(weather[i].rt);

		if(weather[i].wd != 0){
			ws = weather[i].ws;
			wsi = 0;
			while(ws > wind_speed_step[wsi]){
				wsi ++;
			}
			wind_rose_group[wsi][weather[i].wd-1] += ws;
		}
	}

	var temperature_data = [
	  {
	    z: temperature,
	    x: year_days,
	    y: day_hours,
	    type: 'heatmap',
	    colorscale: [
		    ['0.0', 'rgb(49,54,149)'],
		    ['0.111111111111', 'rgb(69,117,180)'],
		    ['0.222222222222', 'rgb(116,173,209)'],
		    ['0.333333333333', 'rgb(171,217,233)'],
		    ['0.444444444444', 'rgb(224,243,248)'],
		    ['0.555555555556', 'rgb(254,224,144)'],
		    ['0.666666666667', 'rgb(253,174,97)'],
		    ['0.777777777778', 'rgb(244,109,67)'],
		    ['0.888888888889', 'rgb(215,48,39)'],
		    ['1.0', 'rgb(165,0,38)']
		 ]
	  }
	];

	var humandity_data = [
	  {
	    z: humandity,
	    x: year_days,
	    y: day_hours,
	    type: 'heatmap',
	    colorscale: [
		    ['0.0', 'rgb(49,54,149)'],
		    ['0.111111111111', 'rgb(69,117,180)'],
		    ['0.222222222222', 'rgb(116,173,209)'],
		    ['0.333333333333', 'rgb(171,217,233)'],
		    ['0.444444444444', 'rgb(224,243,248)'],
		    ['0.555555555556', 'rgb(254,224,144)'],
		    ['0.666666666667', 'rgb(253,174,97)'],
		    ['0.777777777778', 'rgb(244,109,67)'],
		    ['0.888888888889', 'rgb(215,48,39)'],
		    ['1.0', 'rgb(165,0,38)']
		 ]
	  }
	];

	var global_radiance_data = [
	  {
	    z: global_radiance,
	    x: year_days,
	    y: day_hours,
	    type: 'heatmap',
	    colorscale: [
		    ['0.0', 'rgb(49,54,149)'],
		    ['0.111111111111', 'rgb(69,117,180)'],
		    ['0.222222222222', 'rgb(116,173,209)'],
		    ['0.333333333333', 'rgb(171,217,233)'],
		    ['0.444444444444', 'rgb(224,243,248)'],
		    ['0.555555555556', 'rgb(254,224,144)'],
		    ['0.666666666667', 'rgb(253,174,97)'],
		    ['0.777777777778', 'rgb(244,109,67)'],
		    ['0.888888888889', 'rgb(215,48,39)'],
		    ['1.0', 'rgb(165,0,38)']
		 ]
	  }
	];

	var layout_1 = {
	  	autosize: false,
	 	width: 600,
	  	height: 250,
		margin: {
		 	l: 50,
		 	r: 50,
		 	b: 40,
		 	t: 10,
		 	pad: 4
		 }
		// paper_bgcolor: '#7f7f7f',
		// plot_bgcolor: '#c7c7c7'
	};

	Plotly.newPlot('v-pills-temperature', temperature_data,layout_1, {displayModeBar: false});
	Plotly.newPlot('v-pills-humandity', humandity_data,layout_1, {displayModeBar: false});
	Plotly.newPlot('v-pills-global-radiation', global_radiance_data,layout_1, {displayModeBar: false});


	var wind_rose_traces = [];
	for(wsi = 0;  wsi < 6; wsi ++){
		var trace = {
  			r: wind_rose_group[wsi],
  			t: wind_direction,
  			name: wind_step_label[wsi],
  			marker: {color: wind_step_colors[wsi]},
  			type: 'area'
		};
		wind_rose_traces.push(trace);
	}
	var layout_2 = {
	  	autosize: true,
	 	width: 350,
	  	height: 290,
		margin: {
		 	l: 20,
		 	r: 100,
		 	b: 10,
		 	t: 0,
		 	pad: 4
		 },
		orientation: 270,
		showlegend: true,
		legend: {
		    x: 1,
		    y: 0.5
		}
	};

	Plotly.newPlot('wind-rose-chart', wind_rose_traces,layout_2);

}


UI.colors = {
    total_energy :'rgb(0,0,0)',
    cooling : 'rgb(0,84,165)',
    heating :'rgb(243, 101, 35)',
    lighting: 'rgb(255, 197, 1)',
    df_over_lit :'rgb(239,208,6)',
    df_normal :'rgb(0,176,236)',
    df_under_lit :'rgb(0,55,0)'
};

//记录部分Energy Use分析结果的数据
UI.result = {
    total_area:0,
    eui:0
};

UI.show_main_analysis_result = function(data){
    var energy = data.energy;

    //显示总面积
    var total_area = data.area.toFixed(0);
    $("#total_area").html(total_area);
    UI.result.total_area = total_area;

    //显示总Energy Use
    var eui_value = eval(energy.total.join("+")).toFixed(2);
    $("#eui_value").html(eui_value * 1);
    UI.result.eui = eui_value;

    var total_energy = (eui_value * total_area / 1000.0).toFixed(0);
    $("#total_energy_value").html(total_energy);
    
    //显示Energy Use占比数据
    var energy_percent_data = [{
      values: energy.total,
      labels: ['Cooling', 'Heating', 'Lighting' ],
      domain: {column: 0},
      name: 'Energy Use',
      hoverinfo: 'label+value',
      hole: .7,
      type: 'pie',
      marker: {colors: [ UI.colors.cooling, UI.colors.heating, UI.colors.lighting]}
    }];

    var layout = {
        title: null,
        showlegend: false,
        autosize: true,
        width: 230,
        height: 230,
        margin: {
            l: 30,
            r: 30,
            b: 30,
            t: 30,
            pad: 0
        },
        annotations: [
        {
          font: {
            size: 12
          },
          showarrow: false,
          text: 'kWh/m2a',
          x: 0.5,
          y: 0.5
        }]
    };
    Plotly.newPlot('energy_percent', energy_percent_data, layout, UI.defaultPlotlyConfiguration);

    //显示采光系数估算值
    var dfs = data.dfs;
    var level1 = 3.0;
    var level2 = 8.0;
    var dfs_pecent = [0,0,0];
    var di;
    var ave_df = 0.0;
    var zone_df;
    var zone_area;
    var all_area = 0.0;
    for(di = 0; di < dfs.length; di++){
        zone_df = dfs[di][0];
        zone_area = dfs[di][1];
        if(zone_df < level1){
            dfs_pecent[0] += zone_area;
        }else if (zone_df > level2){
            dfs_pecent[2] += zone_area;
        }else{
            dfs_pecent[1] += zone_area;
        }
        ave_df += zone_df * zone_area;
        all_area += zone_area;
    }
    ave_df = (ave_df/all_area).toFixed(1);
    var daylight_percent_data = [{
      values: dfs_pecent,
      labels: ['0%-3%', '3%-8%', '>8%' ],
      domain: {column: 0},
      name: '采光系数',
      hoverinfo: 'label+percent',
      hole: .7,
      type: 'pie',
      marker: {colors: [ UI.colors.df_under_lit, UI.colors.df_normal, UI.colors.df_over_lit]}
    }];

    var daylight_layout = {
        title: null,
        showlegend: false,
        autosize: true,
        width: 230,
        height: 230,
        margin: {
            l: 30,
            r: 30,
            b: 30,
            t: 30,
            pad: 0
        },
        annotations: [
        {
          font: {
            size: 12
          },
          showarrow: false,
          text: 'DF均值：'+ave_df,
          x: 0.5,
          y: 0.5
        }]
    };
    Plotly.newPlot('daylight_percent', daylight_percent_data, daylight_layout, UI.defaultPlotlyConfiguration);

    //显示逐月分项Energy Use数据
    var c_data = [], h_data=[], l_data = []; 
    var month_data = [];
    var md = energy.months;
    for(var i = 0; i < 12; i++){
        c_data.push(md[i][0]);
        h_data.push(md[i][1]);
        l_data.push(md[i][2]);
    }
    month_data.push(UI.build_energy_month_bar_item("Lighting",UI.colors.lighting,l_data));
    month_data.push(UI.build_energy_month_bar_item("Cooling",UI.colors.cooling,c_data));
    month_data.push(UI.build_energy_month_bar_item("Heating",UI.colors.heating,h_data));
    var layout_month = {
        title: "Monthly Energy Use",
        barmode: 'stack',
        showlegend: true,
        autosize: true,
        width: 600,
        height: 300,
        margin: {
            l: 70,
            r: 30,
            b: 60,
            t: 30,
            pad: 10
        },
        yaxis: {
            title: 'kWh/m2a',
            titlefont: {
                size: 12
            }
        }
    };
    Plotly.newPlot('month_energy_chart', month_data, layout_month, UI.defaultPlotlyConfiguration);
    //显示每个空间分项Energy Use数据
    c_data = [], h_data=[], l_data = []; 
    var space_data = [];
    var sd = energy.spaces;
    var space_number = sd.length;
    for(var i = 0; i < space_number; i++){
        c_data.push(sd[i][0]);
        h_data.push(sd[i][1]);
        l_data.push(sd[i][2]);
    }
    space_data.push(UI.build_energy_sapces_bar_item("Lighting",UI.colors.lighting,l_data,sd));
    space_data.push(UI.build_energy_sapces_bar_item("Cooling",UI.colors.cooling,c_data,sd));
    space_data.push(UI.build_energy_sapces_bar_item("Heating",UI.colors.heating,h_data,sd));
    var layout_space = {
        title: "Space Annual Energy Use",
        barmode: 'stack',
        showlegend: true,
        autosize: true,
        width: 600,
        height: 300,
        margin: {
            l: 70,
            r: 30,
            b: 60,
            t: 30,
            pad: 20
        },
        yaxis: {
            title: 'kWh/m2a',
            titlefont: {
                size: 12
            }
        }
    };
    Plotly.newPlot('space_energy_chart', space_data, layout_space, UI.defaultPlotlyConfiguration);
}

UI.build_energy_month_bar_item =function(name,c,y_data){
    var item = {
        x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        y: y_data,
        name: name,
        type: 'bar',
        marker: {color: c}
    };
    return item;
}

UI.build_energy_history_bar_item =function(name,c,y_data){
    var x = [];
    var i = 0;
    for(i = 0; i < y_data.length; i++){
        x.push("#" + (i+1));
    }
    var item = {
        x: x,
        y: y_data,
        name: name,
        type: 'bar',
        marker: {color: c}
    };
    return item;
}

UI.build_energy_sapces_bar_item =function(name,c,y_data,space_data){
    var x_data = [];
    var area_data = [];

    for(var i = 0; i < y_data.length; i++){
        x_data.push(space_data[i][5]);
        area_data.push(space_data[i][4]);
    }
    var item = {
        x: x_data,
        y: y_data,
        width:area_data,

        name: name,
        type: 'bar',
        marker: {color: c}
    };
    return item;
}

//更新性能分析数据
UI.update_analysis_history = function(data){

    var n = data.length;
    var i = 0;
    var table_values = [[],[],[],[],[],[],[]];//按列组织

    for(i = 0; i < n; i++){
        var d = JSON.parse(data[i]);
        var name =  d.backup_path.split("\\");
        name = name[name.length - 1];
        var area = d.area*1.0;
        var cool = d.energy[0]*1.0;
        var heat = d.energy[1]*1.0;
        var light = d.energy[2]*1.0;
        var total = cool + heat + light;
        
        table_values[0].push("#"+(i+1));
        table_values[1].push(name);
        table_values[2].push((area).toFixed(0));
        table_values[3].push((area*total).toFixed(2));
        table_values[4].push((area*cool).toFixed(2));
        table_values[5].push((area*heat).toFixed(2));
        table_values[6].push((area*light).toFixed(2));
    }

    //更新图
    var solution_data = [];
    solution_data.push(UI.build_energy_history_bar_item("Lighting",UI.colors.lighting,table_values[6]));
    solution_data.push(UI.build_energy_history_bar_item("Cooling",UI.colors.cooling,table_values[4]));
    solution_data.push(UI.build_energy_history_bar_item("Heating",UI.colors.heating,table_values[5]));
    var layout_history = {
        title: "History EUI",
        barmode: 'stack',
        showlegend: true,
        autosize: true,
        width: 700,
        height: 300,
        margin: {
            l: 70,
            r: 30,
            b: 60,
            t: 30,
            pad: 10
        },
        yaxis: {
            title: 'kWh/m2',
            titlefont: {
                size: 12
            }
        }
    };
    Plotly.newPlot('history_chart', solution_data, layout_history, UI.defaultPlotlyConfiguration);

    //更新表
    var pl_table_data = [{
        type: 'table',
        header: {
            values: [["<b>编号</b>"], ["<b>名称</b>"], ["<b>面积</b>"],["<b>总Energy Use(kWh/a)</b>"], ["<b>CoolingEnergy Use(kWh/a)</b>"],["<b>HeatingEnergy Use(kWh/a)</b>"], ["<b>LightingEnergy Use</b>"]],
            align: "center",
            line: {width: 1, color: 'black'},
        fill: {color: "grey"},
        font: {family: "Arial", size: 12, color: "white"}
        },
      cells: {
        values: table_values,
        align: "center",
        line: {color: "black", width: 1},
        font: {family: "Arial", size: 11, color: ["black"]}
      }
    }];

    var table_layout = {
      margin:{
        l:20,
        r:20,
        t:40,
        b:20
      },
      title:"history Cases"
    };

    Plotly.newPlot('history_table', pl_table_data,table_layout,UI.defaultPlotlyConfiguration);
}

UI.run_optimize_energy_analysis = function(){

    var x_bounds = [[0.0,1.0],[0.0,1.0],[0.0,1.0],[0.0,1.0]];

    var opts = {
        optimizer:"optimizer_energy",
        num_parameters:4,
        x_bounds:x_bounds,
        population_size:10
    };

    Skp.send("optmize_energy",[JSON.stringify(opts)]);
}


UI.params_labels = ["WWR-S","WWR-W","WWR-N","WWR-E"];
UI.update_coordinate_chart = function(id,num_parameters,x_bounds,solutions){

    //第一步：更新图
    var j,i;
    var x_dimensions = [];
    var sn = solutions.length;
    var min_obj = Number.MAX_VALUE;
    var max_obj = Number.MIN_VALUE;
    var obj_values = [];
    var s;

    var obj = 0;
    for(i = 0; i < sn; i++){
        s = solutions[i];
        obj = s.objective * UI.result.total_area;
        if(s.objective > max_obj) max_obj = obj;
        if(s.objective < min_obj) min_obj = obj;
        obj_values.push(obj);
    }

    for(j = 0; j < num_parameters; j++){
        var x_values = [];
        for(i = 0; i < sn; i++){
            x_values.push(solutions[i].x[j]*1.0);
        }
        x_dimensions.push({
            range: x_bounds[j],
            label: UI.params_labels[j],  //'参数'+(j+1),
            tickformat:"",
            values: x_values
        });
    }
    var params_layout = {
      title:"设计参数取值分布图",
      font: {
        family: 'Times New Roman'
      },
      yaxis:{
        autorange:true
      }
    };
    var params_data = [{
      type: 'parcoords',
      pad: [80,80,80,80],
      line: {
        showscale: true,
        reversescale: false,
        colorscale: 'Jet',
        cmin: min_obj,
        cmax: max_obj,
        color: obj_values
      },

      /*line: {
        color: unpack(rows, 'species_id'),
        colorscale: [[0, 'red'], [0.5, 'green'], [1, 'blue']]
      },*/
      dimensions: x_dimensions
    }];


    Plotly.newPlot(id, params_data,params_layout,UI.defaultPlotlyConfiguration);

    //第二步：更新表


    var values = [[],[],[],[],[],[]];//按列组织
    for(i = 0; i < sn; i++){
        s = solutions[i];
        obj = s.objective * UI.result.total_area;
        values[0].push("方案" + (i+1));
        values[1].push(obj.toFixed(2));
        values[2].push((s.x[0]*1.0).toFixed(2));
        values[3].push((s.x[1]*1.0).toFixed(2));
        values[4].push((s.x[2]*1.0).toFixed(2));
        values[5].push((s.x[3]*1.0).toFixed(2));
    }

    var data = [{
        type: 'table',
        header: {
            values: [["<b>方案编号</b>"], ["<b>总Energy Use(kWh/a)</b>"], ["<b>南向窗墙比</b>"],["<b>西向窗墙比</b>"], ["<b>北向窗墙比</b>"], ["<b>东向窗墙比</b>"]],
            align: "center",
            line: {width: 1, color: 'black'},
        fill: {color: "grey"},
        font: {family: "Arial", size: 12, color: "white"}
        },
      cells: {
        values: values,
        align: "center",
        line: {color: "black", width: 1},
        font: {family: "Arial", size: 11, color: ["black"]}
      }
    }];

    var table_layout = {
      margin:{
        l:20,
        r:20,
        t:40,
        b:20
      },
      title:"最优方案设计参数取值表"
    };

    Plotly.newPlot('opt_energy_params_table', data,table_layout,UI.defaultPlotlyConfiguration);

    //$("#opt_energy_params_plot").html(JSON.stringify(params_data));
}

UI.update_energy_rader_chart =function(id,energys){

    var area = UI.result.total_area;
    var unopt_eui = UI.result.eui;
    var cool_eui = energys[0];
    var heat_eui = energys[1];
    var light_eui = energys[2];
    var opt_eui = cool_eui + heat_eui + light_eui;
    var percent = (opt_eui - unopt_eui) / unopt_eui * 100.0;

    $("#un_optimized_energy").html((area * unopt_eui).toFixed(2));
    $("#optimized_energy").html((area * opt_eui).toFixed(2));
    $("#optimized_energy_percent").html(percent.toFixed(2));
    $("#optimized_cool_energy").html((area * cool_eui).toFixed(2));
    $("#optimized_heat_energy").html((area * heat_eui).toFixed(2));
    $("#optimized_light_energy").html((area * light_eui).toFixed(2));
    /*
    var max_v = 0.0;
    var i = 0;
    var rs = [];
    for(i = 0; i < energys.length; i++){
        if (energys[i] > max_v){
            max_v = energys[i];
        }
        rs.push(energys[i]);
    }
    rs.push(energys[0]);

    var data = [{
      type: 'scatterpolar',
      r: rs,
      theta: ['Cooling','Heating','Lighting',"Cooling"],
      fill: 'toself'
    }]

    var layout = {
      polar: {
        radialaxis: {
          visible: true,
          range: [0, max_v]
        }
      },
      showlegend: false,
      margin:{
        l:20,
        r:20,
        t:40,
        b:20
      },
      title:"最优方案性能"
    };

    Plotly.plot(id, data, layout,UI.defaultPlotlyConfiguration);*/
}

UI.performance_boundary_history = {"best":[],"worst":[]};
UI.update_coverage_chart_version_old= function(id, solutions){
    var j,i;
    var sn = solutions.length;
    var min_obj = Number.MAX_VALUE;
    var max_obj = Number.MIN_VALUE;
    var s;
    var n = UI.performance_boundary_history.best.length;
    for(i = 0; i < sn; i++){
        s = solutions[i];
        if(s.objective > max_obj) max_obj = s.objective;
        if(s.objective < min_obj) min_obj = s.objective;
    }
    UI.performance_boundary_history.best.push(min_obj);
    UI.performance_boundary_history.worst.push(max_obj);
    if (n == 0){
        UI.performance_boundary_history.best.push(min_obj);
        UI.performance_boundary_history.worst.push(max_obj);
    }

    var j = 0;
    
    var generations = [];

    for(j = 0;  j <= n; j++){
        generations.push(j);
    }

    var traces = [
        {x: generations, y: UI.performance_boundary_history.best, type: 'scatter',marker:{color:"orange"}},
        {x: generations, y: UI.performance_boundary_history.worst,  type: 'scatter',marker:{color:"gray"}}
    ];

    var layout = {
      showlegend: false,
      margin:{
        l:20,
        r:60,
        t:40,
        b:40
      },
      title:"性能收敛与性能边界图"
    };

    Plotly.newPlot(id, traces,layout, UI.defaultPlotlyConfiguration);
}

UI.update_coverage_chart= function(id, solutions){

    var j,i;
    var sn = solutions.length;
    var min_obj = Number.MAX_VALUE;
    var max_obj = Number.MIN_VALUE;
    var s;
    var n = UI.performance_boundary_history.best.length;
    for(i = 0; i < sn; i++){
        s = solutions[i];
        if(s.objective > max_obj) max_obj = s.objective;
        if(s.objective < min_obj) min_obj = s.objective;
    }
    UI.performance_boundary_history.best.push(min_obj);
    UI.performance_boundary_history.worst.push(max_obj);
    if (n == 0){
        UI.performance_boundary_history.best.push(min_obj);
        UI.performance_boundary_history.worst.push(max_obj);
    }

    var j = 0;
    
    var generations = [];

    for(j = 0;  j <= n; j++){
        generations.push(j+"");
    }

    var values = [];
    for(j = 0; j <= n; j++){
        values.push( (UI.performance_boundary_history.best[j] * UI.result.total_area).toFixed(2));
    }

    var traces = [
        {   x: generations, 
            y:values, 
            type: 'scatter',
            mode:"markers", 
            marker:{color:"green"},
            marker: { size: 12 }}
    ];

    var layout = {
      showlegend: false,
      margin:{
        l:50,
        r:60,
        t:40,
        b:40
      },
      title:"最佳方案Energy Use取值"
    };

    Plotly.newPlot(id, traces,layout, UI.defaultPlotlyConfiguration);
}


UI.update_optimize_energy_result = function(data){
    //更新Energy Use结果数据，而非Energy Use雷达图
    UI.update_energy_rader_chart("opt_energy_radar",data.solutions[0].obj_record);
    //更新参数取值分布图
    UI.update_coordinate_chart("opt_energy_params_plot",data.num_parameters,data.x_bounds,data.solutions);
    //更新收敛图表
    UI.update_coverage_chart("opt_performance_boundary",data.solutions);
}


UI.init_all_sliders = function(){
    $("#p0").slider({
        range: true,
        values: [0, 1.0]
    });
    $("#p1").slider({
        range: true,
        values: [0, 1.0]
    });
    $("#p2").slider({
        range: true,
        values: [0, 1.0]
    });
    $("#p3").slider({
        range: true,
        values: [0, 1.0]
    });
}
UI.show_tab = function(tab){
    
    $("#main_tab").attr('class') = "moosas_link nav-link"
    $("#"+tab[0]).attr('class') +=  " active"

}
UI.run_param_analysis = function(){
    var p_selected = $("#inputParamsAnalysisParamsType  option:selected");
    var p_type = p_selected.attr("tag");
    var p_range = p_selected.attr("range");
    var p_name = p_selected.attr("name");
    var p_step = p_selected.attr("step");

    var id = "param_tab_header_" + p_type;


    var tab_header = "<a class='nav-link' id='"+id+"' data-toggle='pill' href='#v-pills-params-analysis' role='tab' aria-controls='v-pills-params-analysis' aria-selected='false'>"+p_name+"</a>";
    $("#v-pills-tab-params").append(tab_header);
    $("#"+id).click();

    id = "params_analysis_result_"+p_type;
    var tab_box = "<div class='row' style='overflow-x:hidden;' id='"+ id+"'></div>";
    $("#v-pills-params-analysis").append(tab_box);
    $("#"+id).append("<div class='col-6 params-plot' id='params_analysis_result_left_"+ p_type+"' style='height: 300px;'></div>");
    $("#"+id).append("<div class='col-6 params-distribution' id='params_analysis_result_right_"+ p_type+"' style='height: 300px;'></div>");


    p_type = p_type.split("-");
    p_range = p_range.split(",");
    p_range[0] *= 1;
    p_range[1] *= 1;

    var opts = {
        type:p_type[0],
        target:p_type[1]*1,
        range:p_range,
        step: p_step * 1,
        name: p_name,
        buildingtype : UI.settings['selectBuildingType']
    };
    Skp.send("params_analysis",[JSON.stringify(opts)]);
}

UI.param_names_analysis_plots = [];
UI.update_params_analysis_plot = function(id,name,values){
    
    var x_values = [];
    var c_values = [];
    var h_values = [];
    var l_values = [];
    var t_values = [];

    var i;
    var v;
    for(i = 0; i < values.length; i++){
        v = values[i];
        x_values.push(v.x);
        c_values.push(v.y[0]);
        h_values.push(v.y[1]);
        l_values.push(v.y[2]);
        t_values.push(eval(v.y.join("+")));
    }

    var t_trace = {
      x: x_values,
      y: t_values,
      type: 'scatter',
      name: '总Energy Use',
      line: {
        color: UI.colors.total_energy,
        width: 1
      }
    };

    var c_trace = {
      x: x_values,
      y: c_values,
      type: 'scatter',
      name: 'Cooling',
      line: {
        color: UI.colors.cooling,
        width: 1
      }
    };

    var h_trace = {
      x: x_values,
      y: h_values,
      type: 'scatter',
      name: 'Heating',
      line: {
        color: UI.colors.heating,
        width: 1
      }
    };

    var l_trace = {
      x: x_values,
      y: l_values,
      type: 'scatter',
      name: 'Lighting',
      line: {
        color: UI.colors.lighting,
        width: 1
      }
    };

    var layout = {
      showlegend: true,
      legend: {
        x: 0.0,
        y: -0.1,
        orientation:"h"
      },
      title:"参数分析：Energy Use与"+name,
      height:300,
      margin:{
        l:60,
        r:20,
        t:40,
        b:40
      },
      xaxis: {
            showline:true
      },
      yaxis:{
        title: "Energy UsekWh/m2a"
      }
    };

    var data = [t_trace,c_trace,h_trace,l_trace];

    var plot = Plotly.newPlot(id, data,layout,UI.defaultPlotlyConfiguration);
    UI.param_names_analysis_plots.push(document.getElementById(id));
}


UI.update_params_plot_lengend_mode = function(){
    var value = $("#inputParamsAnalysisGoalType option:selected").attr("id");
    var plots = UI.param_names_analysis_plots;
    var pn = plots.length;
    var i;


    for (i = 0; i < pn; i++){
        if(value == "all"){
            plots[i].data[3].visible =true;
            plots[i].data[2].visible =true;
            plots[i].data[1].visible =true;
            plots[i].data[0].visible =true;
            Plotly.redraw(plots[i]);
        }else if(value == "total"){
            plots[i].data[2].visible ='legendonly';
            plots[i].data[1].visible ='legendonly';
            plots[i].data[3].visible ='legendonly';
            plots[i].data[0].visible =true;
            Plotly.redraw(plots[i]);
        }else if(value == "cool"){
            plots[i].data[3].visible ='legendonly';
            plots[i].data[2].visible ='legendonly';
            plots[i].data[0].visible ='legendonly';
            plots[i].data[1].visible =true;
            Plotly.redraw(plots[i]);
        }else if(value == "light"){
            plots[i].data[0].visible ='legendonly';
            plots[i].data[2].visible ='legendonly';
            plots[i].data[1].visible ='legendonly';
            plots[i].data[3].visible =true;
            Plotly.redraw(plots[i]);
        }else if(value == "heat"){
            plots[i].data[3].visible ='legendonly';
            plots[i].data[1].visible ='legendonly';
            plots[i].data[0].visible ='legendonly';
            plots[i].data[2].visible =true;
            Plotly.redraw(plots[i]);
        }

    }
}


UI.update_param_distribution_chart = function(id,pname,bis,range,step){
    var x_values = [];
    var y_values = [];
    var x_min = range[0];
    var x_max = range[1];
    var n = Math.floor((x_max - x_min) / step);
    var i;
    for(i = 1; i <= n; i++){
        y_values.push(0);
        x_values.push((x_min + i * step).toFixed(1));
    }
    var bn = bis.length;
    var j;
    for(j = 0; j < bn; j++){
        i = Math.floor((bis[j] - x_min) / step);
        y_values[i] += 1;
    }

    var trace = {
      x: x_values,
      y: y_values,
      marker: {
              color: "rgba(100, 200, 102, 0.7)",
               line: {
                color:  "rgba(100, 200, 102, 1)", 
                width: 1
        } 
           }, 
      name: pname+"取值分布", 
      opacity: 0.75, 
      type: "bar"
    };

    var data = [trace];
    var layout = {
      title: pname+"取值分布", 
      xaxis: {title: "取值"}, 
      yaxis: {title: "墙面数量"},
      height:300,
      margin:{
        l:40,
        r:20,
        t:40,
        b:40
      }
    };
    Plotly.newPlot(id, data, layout);
}


UI.params_performances = {param_names:[],ks:[]};
UI.update_sensitive_chart = function(name,bis,values,range,step){
    //var total_energy = eval(cur_energy.join("+"));
    var x_min = range[0];
    var x_max = range[1];
    var unit = step / (x_max - x_min);   //相对单元大小
    //计算平均敏感性
    var bn = bis.length;
    var vn = values.length;
    var mean = 0;
    var mn= 0;
    var i,j,x,k;
    var y1,y2;
    for(j = 0; j < bn; j++){
        x = bis[j];
        //寻找当前参数所在的位置
        i = 0;
        while (i < vn - 1){
            if( x >= values[i].x && x <= values[i+1].x){
                break;
            }
            i +=1;
        }
        if(i >= vn - 1){
            continue;
        }

        //计算当前这个数的敏感值
        y1 = eval(values[i].y.join("+"));
        y2 = eval(values[i+1].y.join("+"));
        k =  (y2 - y1)/unit;
        mean += k;
        mn += 1;
    }

    if(mn >0) mean /= mn;

    UI.params_performances.param_names.push(name);
    UI.params_performances.ks.push(mean);

    var data = [{
      type: 'bar',
      x: UI.params_performances.ks,
      y: UI.params_performances.param_names,
      orientation: 'h',
      marker: {
              color: "rgba(100, 200, 102, 0.7)",
               line: {
                color:  "rgba(100, 200, 102, 1)", 
                width: 1}
        }  
    }];

    var layout = {
      title: "设计参数敏感性分析", 
      xaxis: {title: "影响大小"},
      margin:{
        l:100
      }
    };

    Plotly.newPlot('sensitive_chart', data, layout, UI.defaultPlotlyConfiguration);
}

UI.update_params_analysis_result = function(res){
    var id = "params_analysis_result_left_" + res[0].type + "-"+res[0].target;
    UI.update_params_analysis_plot(id,res[0].name,res[0].values);

    id = "params_analysis_result_right_" + res[0].type + "-"+res[0].target;
    UI.update_param_distribution_chart(id,res[0].name,res[0].bis,res[0].range,res[0].step);

    UI.update_sensitive_chart(res[0].name,res[0].bis,res[0].values,res[0].range,res[0].step);
}

UI.run_mutil_goal_param_analysis = function(tag,name){
    var ta = tag.split("-");
    var opts = {
        type: ta[0],
        target: ta[1]*1,
        range: [0,1.0],
        step: 0.1,
        name: name,
        buildingtype : UI.settings['selectBuildingType']  
    };

    Skp.send("multi_goal_params_analysis",[JSON.stringify(opts)]);

    UI.update_multi_goal_params_analysis_sensitive_chart("");
}

UI.init_update_multi_goal_params_analysis_sensitive_chart = function(){
    var title = "南向窗墙比多目标参数分析";
    var x_values = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0];
    var y1_values = [];
    var y2_values = [];
    UI.update_multi_goal_params_analysis_sensitive_chart("wwr-0","南向窗墙比多目标参数分析",x_values,y1_values,y2_values);
    UI.update_multi_goal_params_analysis_sensitive_chart("wwr-1","西向窗墙比多目标参数分析",x_values,y1_values,y2_values);
    UI.update_multi_goal_params_analysis_sensitive_chart("wwr-2","北向窗墙比多目标参数分析",x_values,y1_values,y2_values);
    UI.update_multi_goal_params_analysis_sensitive_chart("wwr-3","东向窗墙比多目标参数分析",x_values,y1_values,y2_values);
}


UI.update_multi_goal_params_analysis_result = function(res){
    var id = res[0].type + "-"+res[0].target;
    var title = res[0].name + "多目标参数分析";

    var values = res[0].values;
    var n = values.length;
    var x_values = [];//[0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0];
    var y1_values = [];
    var y2_values = [];
    for(i = 0; i < n; i++){
        x_values.push(values[i].x.toFixed(1));
        y1_values.push(values[i].y1.toFixed(2));
        y2_values.push(values[i].y2.toFixed(2));
    }
    UI.update_multi_goal_params_analysis_sensitive_chart(id,title,x_values,y1_values,y2_values);
}

UI.update_multi_goal_params_analysis_sensitive_chart = function(id,title,x_values,y1_values,y2_values){

    var div_id = "multi_goal_params_analysis_chart_" + id;

    $("#"+div_id).html("");

    var trace1 = {
      x: x_values,
      y: y1_values,
      name: 'Energy Use',
      type: 'scatter'
    };

    var trace2 = {
      x: x_values,
      y: y2_values,
      name: '采光系数',
      yaxis: 'y2',
      type: 'scatter'
    };

    var data = [trace1, trace2];

    var layout = {
        width:400,
      title: title,
      xaxis: {title: '窗墙比'},
      yaxis: {title: 'Energy Use(kWh/m2a)'},
      yaxis2: {
        title: '采光系数(%)',
        titlefont: {color: 'rgb(148, 103, 189)'},
        tickfont: {color: 'rgb(148, 103, 189)'},
        overlaying: 'y',
        side: 'right'
      },
      margin:{
        l:50,
        r:50,
        t:50,
        b:60
      },
      showlegend: true,
      legend: {
        x: 0.6,
        y: -0.1,
        orientation:"h"
      }
    };

    Plotly.newPlot(div_id, data, layout);
}

UI.update_model_data = function(model){

    $("#building_area").html(model.area.toFixed(0));
    $("#building_height").html(model.height.toFixed(1));
    $("#average_floor_height").html(model.floor_height.toFixed(1));

    var spaces = model.spaces;
    var sn = spaces.length;
    var fn;
    var i,j;
    var types_number = {
        "0" :0,
        "3": 0,
        "1": 0,
        "5": 0,
        "6": 0,
        "2": 0,
        "4": 0,
        "8": 0,
        "16": 0,
        "-1":0/*,
        "32": 0,
        "64": 0,
        "-2": 0,
        "-1": 0*/
    };

    var sd;
    var btree = "";
    var tnodes;
    for(i = 0; i <sn; i ++){
        s_info = spaces[i][0];
        sd = spaces[i][1];
        UI.space_params[s_info.id]=s_info;
        fn = sd.length;
        for(j = 0; j < fn; j++){
            types_number[""+sd[j][1]] += 1;
        }
        btree+="<button class=\"space_button\" onclick=UI.showspace(\""+s_info.id+"\") id="+s_info.id+">" +s_info.zone_name+"</button>";
    } 
    $('#building_tree').html(btree);  

    $("#zone_params").css("visibility","visible");

    var et;
    for (et in types_number)  {  
        $("#entity-" + et).html(types_number[et]);
    } 
}


UI.selected_space=null
UI.showspace = function(space_id){
    Skp.send("show_space",[space_id]);
    //Skp.send('text',[JSON.stringify(UI.space_params[space_id])]);
    UI.selected_space=space_id;
    var params_tab = $('#building_params_table').find(".caname");
    for(i = 0 ; i < params_tab.length ; i++) {    
        params_tab[i].innerHTML= UI.space_params[space_id][params_tab[i].id];
    }
    $('#zone_standard')[0].innerHTML = UI.space_params[space_id]['zone_standard']
};
$("#building_params_table").on('click', 'tr > .caname', function () {
            // 获取当前点击的元素
            var td = $(this);
            // 获取当前元素的内容
            var txt = $.trim(td.text());
            // 把获取到的内容添加到 input 的 value 中
            var input = $("<input width='70' type='text' value='" + txt + "'/>");
            // 把 input 放到 元素中
            td.html(input);
            input.click(function () { return false; });
            //this.setSelectionRange(0,text.length);
            //获取焦点
            input.trigger("focus");
            input.trigger("select");
            //文本框失去焦点后提交内容，重新变为文本
            input.blur(function () {
                var newtxt = $(this).val();
                td.html(newtxt)
                //判断文本有没有修改
                if (newtxt != txt) {
                    td.html(newtxt);
                    UI.space_params[UI.selected_space][td.attr('id')]=newtxt
                    Skp.send('change_space_parameters',[UI.selected_space,td.attr('id'),newtxt]);
                    
                }
            })
        })
//在web界面上绘制采光结果
UI.daylight ={
    scene:null,
    camera:null,
    renderer:null,
    controls:null
};

UI.update_daylight_webgl = function(data){

    //初始化绘制场景
    var div_width = 590, div_height = 540;
    UI.daylight.scene = new THREE.Scene();
    UI.daylight.scene.background = new THREE.Color( 0xffffff);
    UI.daylight.camera = new THREE.PerspectiveCamera( 90, div_width * 1.0 / div_height, 0.1, 1000 );  
    UI.daylight.renderer = new THREE.WebGLRenderer();
    //UI.daylight.renderer.setClearColor( 0xffffff, 0);
    UI.daylight.renderer.setSize( div_width, div_height );
    $('#daylight_webgl_render_area').html("");
    document.getElementById('daylight_webgl_render_area').appendChild(UI.daylight.renderer.domElement );
    // 给场景添加一个环境光
    var ambientLight = new THREE.AmbientLight( 0xf5f5f5);
    UI.daylight.scene.add( ambientLight );
    var xy_grid = new THREE.GridHelper( 500, 50, 0xcccccc, 0xcccccc );
    UI.daylight.scene.add( xy_grid );
    //alert("finish setup basic params.");

    //添加场景几何
    var grids = data.grids;
    var i;
    //alert("grids Number = " + grids.length);

    var box = new THREE.Box3();

    var debug = true;


    for(i = 0; i < grids.length; i++){
        var geometry = new THREE.Geometry();

        var grid = grids[i];
        var is_surface = grid.is_surface;
        //alert("is_surface = " + is_surface);
        var nodes = grid.nodes;
        var values = grid.values;
        var value_range = grid.value_range;
        var y, x;
        var nodes_y = nodes.length;
        //alert("nodes_y = " + nodes_y);
        var indexs = [];
        var n = 0;
       // alert("start add vertices");
        for(y = 0; y < nodes_y; y++){
            var nodes_x = nodes[y].length;
            //alert("nodes_x = " + nodes_x);
            var index = [];
            for(x = 0; x < nodes_x; x++){
                var p = nodes[y][x];
                if(p){
                    geometry.vertices.push(new THREE.Vector3(p[0], p[2], 0- p[1]));
                    //alert([n,values[x][y]]);
                    index.push([n,values[y][x]]);
                    n = n + 1;
                }else{
                    index.push([false,false]);
                }
            }
            //return;
            indexs.push(index);
        }

        //alert("finish add vertices" + geometry.vertices.length);

        var mats=[];
        var mi = 0;
        for(y = 0; y < nodes_y - 1; y++){
            var nodes_x = nodes[y].length;
            for(x = 0; x < nodes_x - 1; x++){
                var p1,p2,p3,p4;
                p1 = indexs[y][x];
                p2 = indexs[y+1][x];
                p3 = indexs[y+1][x+1];
                p4 = indexs[y][x+1];

                if(is_surface == true){
                    if(p1[0] && p2[0] && p3[0]){
                        var f = new THREE.Face3(p3[0], p2[0], p1[0]);
                        var hex = Math.random() * 0xffffff;
                        f.color.setHex( hex );
                        geometry.faces.push(f);
                    }
                    if(p1[0] && p4[0] && p3[0]){
                        var f = new THREE.Face3(p4[0], p3[0], p1[0]);
                        var hex = Math.random() * 0xffffff;
                        f.color.setHex( hex );
                        geometry.faces.push(f);
                    }
                }else{
                    if( p1[0] && p2[0] && p3[0] && p4[0]){
                        var f1 = new THREE.Face3(p3[0], p2[0], p1[0]);
                        mats.push(UI.get_daylight_color([p3[1], p2[1], p1[1],p4[1]],value_range));
                        f1.materialIndex = mi;
                        mi += 1;
                        geometry.faces.push(f1);
                        

                        /*
                        var hex1 = Math.random() * 0xffffff;
                        f1.color.setHex( hex1 );*/
                        
                        var f2 = new THREE.Face3(p4[0], p3[0], p1[0]);
                        mats.push(UI.get_daylight_color([p4[1], p3[1], p1[1],p2[1]],value_range));
                        f2.materialIndex = mi;
                        mi += 1;
                        geometry.faces.push(f2);

                        /*
                        var hex2 = Math.random() * 0xffffff;
                        f2.color.setHex( hex2 );
                        */

                    }
                }
            }
        }
        //alert("faces number = " + geometry.faces.length);
        var material = new THREE.MeshBasicMaterial({
            vertexColors: THREE.FaceColors
        });

        geometry.computeBoundingBox();
        box.union(geometry.boundingBox);

        var obj = new THREE.Mesh(geometry, mats);
        obj.name = "Daylight_" + i;
        UI.daylight.scene.add(obj);
    }

    var sphere = new THREE.Sphere();
    box.expandByScalar(3.0);
    box.getBoundingSphere(sphere);
    var c_dir = new THREE.Vector3(1.0,1.0,1.0);
    c_dir.multiplyScalar(sphere.radius * 2.0);
    var cpos = sphere.center.clone();
    cpos.add(c_dir);
    
    //UI.show_vector("center",sphere.center);

    UI.daylight.camera.up.set(0,1,0);
    UI.daylight.camera.position.set(cpos.x,cpos.y,cpos.z); 
    UI.daylight.camera.lookAt({
        x:sphere.center.x,
        y:sphere.center.y,
        z:sphere.center.z
    });
    //UI.show_vector("cpos",UI.daylight.camera.position);

    UI.daylight.scene.add(UI.daylight.camera);

    /*
    var center = new THREE.Vector3( );
    box.getCenter(center);
    alert("center: "+ center.x + ","+center.y + ","+center.z);
    alert("box max: "+ box.max.x + ","+box.max.y + ","+box.max.z);
    alert("box min: "+ box.min.x + ","+box.min.y + ","+box.min.z);
    UI.daylight.camera.position = box.min;//  set( 0, 50,-100 ); 
    UI.daylight.camera.lookAt(center);
    */

    //添加界面交互控制功能
    UI.daylight.controls = new THREE.OrbitControls( UI.daylight.camera, UI.daylight.renderer.domElement );
    UI.daylight.controls.enabled = true;
    UI.daylight.controls.enableZoom =true;//允许缩放
    UI.daylight.controls.enablePan = true;
    UI.daylight.controls.enableDamping = true;
    UI.daylight.controls.minDistance = 1;
    UI.daylight.controls.maxDistance = 2000;
    UI.daylight.controls.enableRotate =true;
    UI.daylight.controls.rotateSpeed = 0.3;


    //启动动画
    UI.daylight_animate();
}

UI.daylight_colors = [new THREE.Color("rgb(1,76,255)"),new THREE.Color("rgb(1,227,225)"),new THREE.Color("rgb(61,255,1)"),new THREE.Color("rgb(255,161,1)"),new THREE.Color("rgb(255,0,0)")];
UI.daylight_bands = 5;

UI.get_daylight_color =function(values,value_range){
    //alert("values = " + values);
    //alert("value_range = " + value_range);
    var sum = eval(values.join("+"));
    var weight = sum / values.length / value_range;
    if(weight > 1.0){
        weight = 1.0;
    }else if(weight < 0.0){
        weight = 0.0;
    }
    //alert(weight);
    var i = Math.floor(weight / 0.25);
    if(i == 4) i=3;
    var c1 = UI.daylight_colors[i].clone();
    var c2 = UI.daylight_colors[i+1];
    //alert(c1.toArray())
    //alert(c2.toArray())
    weight = (weight - i * 0.25) * 4.0;

    c1.lerp(c2,weight); 

    var material = new THREE.MeshBasicMaterial(  );//{color: "0x"+c1.getHexString(), side: THREE.DoubleSide}
    material.color = c1;
    material.side = THREE.DoubleSide;

    //alert(c1.toArray())
    return material;
}

UI.show_vector  = function(name,v){
    alert(name + ": "+ v.x + ", "+v.y + ", "+v.z);
}

UI.daylight_animate = function(){
    requestAnimationFrame( UI.daylight_animate );
    UI.daylight.controls.update();
    UI.daylight.renderer.render( UI.daylight.scene, UI.daylight.camera );
}


$(document).ready(function(){ 
	

	UI.init_ui();
    Skp.send("reset_ui_data",[" "]);


	//UI.update_building_recognition_result();
	
})