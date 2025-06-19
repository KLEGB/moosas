/*
@author: Hongzhong Chen
@email: 316959124@qq.com
@version: 1.0
@since: 2018-03-18
@license:

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
**/


/**
    x_bounds: 优化参数控制的上下限[[,]]
    preference_x:  偏好点向量 []
    perference_x_delta: 偏好点允许的领域上下限 [[,]]
**/
 var generations_data = [];
 var on_draw =  false;
function NSGA2(num_parameters, x_bounds, num_objectives,mutation_rate=0.1, crossover_rate=1.0){

    this.num_parameters = num_parameters;
    this.x_bounds = x_bounds;

    this.num_objectives = num_objectives;
    this.mutation_rate = mutation_rate;
    this.crossover_rate = crossover_rate;

    this.status = true;

    

    /*
    **/
    this.run = function(population_size, num_generations){
        this.status = true;
        //随机初始化种群P
        var i,j,k;
        var P = [];

        for(i = 0; i < population_size * 3; i++){
            var s = new Solution(this.num_parameters, this.x_bounds, this.num_objectives);
            for(j = 0; j < this.num_parameters; j++){
                s.x[j] = this.x_bounds[j][0] + Math.random() * (this.x_bounds[j][1] - this.x_bounds[j][0]);
            }
            s.evaluate_solution();
            P.push(s);
        }

        var Q = [];
        var R = null;
        var fronts =  null;

        i = 0;
        while(i < num_generations){
            console.log("Generation "+ i);
            R = P.concat(Q);
            fronts = this.fast_nondominated_sort(R);
            P = [];

            for (j = 0; j < fronts.length; j++){
                if(fronts[j].length ==  0) break;

                this.crowding_distance_assignment(fronts[j]);
                P = P.concat(fronts[j]);

                if (P.length >= population_size){
                    break;
                }
            }

            this.sort_crowding(P);
            //console.log(P);
            if(P.length > population_size){
                P = P.slice(0,population_size);
            }

            //console.log(P[0].x);
            //console.log(P[0].objectives);
            generations_data.push([i,P]);
            //this.update_visualize(i,P);

            i++;
            if(i < num_generations) Q = this.make_new_pop(P);
        }

        this.status = false;
    }

    /**
        在P中查找Prato前沿
    */
    this.fast_nondominated_sort = function(P){
        var fronts = [];
        var S = {};
        var n = {};
        var i,j,k;
        var p, q,r, s;
        for(i = 0;i < P.length; i++){
            S[P[i].name] = [];
            n[P[i].name] = 0;
        }

        fronts.push([]);

        for( i =0; i < P.length; i++){
            p = P[i];
            for(j = 0; j < P.length; j++){
                if (i == j) continue;
                q = P[j];
                if(p.can_dominate(q)){
                    S[p.name].push(q);
                }else if(q.can_dominate(p)){
                    n[p.name] += 1;
                }
            }
            if(n[p.name] == 0){
                fronts[0].push(p);
            }
        }

        i = 0

        while( fronts[i].length != 0){
            var next_front = [];

            for(j = 0; j < fronts[i].length; j++){
                r = fronts[i][j];
                for(k = 0;  k < S[r.name].length; k++){
                    s = S[r.name][k];
                    n[s.name] -= 1;
                    if (n[s.name] == 0){
                        next_front.push(s);
                    }
                }
            }

            i += 1;
            fronts.push(next_front);
        }

        //console.log(fronts);

        return fronts;
    } 

    /**
        给front的每个方案设定一个crowding distance值
    */
    this.crowding_distance_assignment = function(front){

        var i;
        for (i = 0; i < front.length; i++){
            front[i].distance = 0;
        }

        var obj_idx;
        var range; 
        for( obj_idx = 0; obj_idx < this.num_objectives; obj_idx++){
            this.sort_objective(front,obj_idx);
            front[0].distance = 99999999999;
            front[front.length-1].distance = 99999999999;

            range = front[0].objectives[obj_idx] -  front[front.length-1].objectives[obj_idx] ;  //此目标的最大值剪去最小值
            if(range == 0) range = 1.0; 
            for(i = 1; i < front.length-1; i++){
                //front[i].distance += (front[i + 1].distance - front[i - 1].distance)
                front[i].distance += (front[i + 1].objectives[obj_idx] - front[i - 1].objectives[obj_idx]) /range;
                //console.log(front[i].distance);
            }

        }

    }

    this.sort_objective = function(P, obj_idx){
        var i,j, temp;
        for(i = P.length-1; i >=0; i--){
            for( j = 1; j < i +1; j++){
                if(P[j-1].objectives[obj_idx] > P[j].objectives[obj_idx]){
                    temp = P[j - 1];
                    P[j - 1] = P[j];
                    P[j] = temp;
                }
            }
        }
    }

    this.sort_crowding = function(P){
        var i,j, temp;
        for(i = P.length-1; i >=0; i--){
            for( j = 1; j < i +1; j++){
                if(this.crowded_comparison(P[j-1],P[j]) < 0){
                    temp = P[j - 1];
                    P[j - 1] = P[j];
                    P[j] = temp;
                }
            }
        }
    }

    this.crowded_comparison = function(s1,s2){
        if(s1.rank < s2.rank) return 1;
        else if (s1.rank > s2.rank) return -1;
        else if (s1.distance > s2.distance) return 1;
        else if (s1.distance < s2.distance) return -1;
        else return 0;
    }

    /**
        根据父代P，产生子代Q
    */
    this.make_new_pop = function(P){
        var Q = [];
        var selected_solutions;
        var s1,s2; 
        var i; 
        while(Q.length != P.length){

            //从P中挑选的两个精英
            selected_solutions = [null,null];
            while(selected_solutions[0] == selected_solutions[1]){
                for(i = 0; i < 2; i++){
                    s1 = this.random_choice(P);
                    s2 = s1;
                    while(s1 == s2){
                        s2 = this.random_choice(P);
                    }
                    if(this.crowded_comparison(s1,s2) > 0){
                        selected_solutions[i] = s1
                    }else{
                        selected_solutions[i] = s2;
                    }
                }

            }

            //杂交和变异产生下一代
            if(Math.random() < this.crossover_rate){
                var child_solution = selected_solutions[0].crossover(selected_solutions[1]);

                if(Math.random() < this.mutation_rate){
                    child_solution.mutate();
                }

                child_solution.evaluate_solution();

                Q.push(child_solution);
            }

        }

        return Q;
    }

    this.random_choice = function(P){
        var i = Math.floor(Math.random()*P.length);
        if (i == P.length )  i-=1;
        return P[i];
    }


    this.defaultPlotlyConfiguration ={
        modeBarButtonsToRemove: ['sendDataToCloud', 'autoScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'lasso2d', 'select2d'], 
        displaylogo: false, 
        showTips: true 
    };

    this.objectives_data = null;
    this.params_data = null;
    this.params_name = null;
    this.layout1 = null;
    this.layout2 = null;
    this.obj1_data = null;
    this.obj2_data = null;
    this.obj3_data = null;
    this.obj4_data = null;
    this.layout_obj1 = null;
    this.layout_obj2 = null;
    this.layout_obj3 = null;
    this.layout_obj4 = null;

    this.init_visualize = function(){

        //对目标值的可视化
        var objectives = {
          x: [],
          y: [],
          mode: 'markers',
          type: 'scatter'
        };
        this.objectives_data = [objectives];
        this.layout1 = {
          title:'第' + 0 + "代种群",
          xaxis: {
            title: '目标1',
          },
          yaxis: {
            title: '目标2',
          }
        };
        Plotly.newPlot('prato_plot', this.objectives_data,this.layout1);


        //对优化参数进行可视化
        this.params_data = [];
        var j;
        this.params_name = [];
        for(j = 0; j < this.num_parameters; j++){
            this.params_name.push("参数" + (j+1));
        }
        this.layout2 = {
          title:'第' + 0 + "代优化参数",
          xaxis: {
            title: '参数名称',
          },
          yaxis: {
            title: '参数取值',
          }
        };
        Plotly.newPlot('params_plot', this.params_data,this.layout2);

        //对目标1结果的可视化
        this.obj1_data = {
          x: [],
          y: [],
          type: 'scatter'
        };
        this.layout_obj1 = {
          xaxis: {
            title: '方案',
          },
          yaxis: {
            title: '目标1取值',
          },
          width: 390,
          height: 200,
          margin: {
            l: 50,
            r: 0,
            b: 30,
            t: 5
          }
        };
        Plotly.newPlot('obj1_plot', [this.obj1_data],this.layout_obj1,this.defaultPlotlyConfiguration);

        this.obj2_data = {
          x: [],
          y: [],
          type: 'scatter'
        };
        this.layout_obj2 = {
          xaxis: {
            title: '方案',
          },
          yaxis: {
            title: '目标2取值',
          },
          width: 390,
          height: 200,
          margin: {
            l: 50,
            r: 0,
            b: 30,
            t: 5
          }
        };
        Plotly.newPlot('obj2_plot', [this.obj2_data],this.layout_obj2,this.defaultPlotlyConfiguration);

        // this.obj3_data = {
        //   x: [],
        //   y: [],
        //   type: 'scatter'
        // };
        // this.layout_obj3 = {
        //   xaxis: {
        //     title: '方案',
        //   },
        //   yaxis: {
        //     title: '目标3取值',
        //   },
        //   width: 390,
        //   height: 100,
        //   margin: {
        //     l: 50,
        //     r: 0,
        //     b: 30,
        //     t: 5
        //   }
        // };
        // Plotly.newPlot('obj3_plot', [this.obj3_data],this.layout_obj3,this.defaultPlotlyConfiguration);

        // this.obj4_data = {
        //   x: [],
        //   y: [],
        //   type: 'scatter'
        // };
        // this.layout_obj4 = {
        //   xaxis: {
        //     title: '方案',
        //   },
        //   yaxis: {
        //     title: '目标4取值',
        //   },
        //   width: 390,
        //   height: 100,
        //   margin: {
        //     l: 50,
        //     r: 0,
        //     b: 30,
        //     t: 5阿
        //   }
        // };
        // Plotly.newPlot('obj4_plot', [this.obj4_data],this.layout_obj4,this.defaultPlotlyConfiguration);
    }

    this.update_visualize = function(num_generations=0,front=[]){

        var i,j;
        var obj1 = [];
        var obj2 = [];
        var s;

        for( i = 0; i < front.length; i++){
            s = front[i];
            obj1.push(s.objectives[0]);
            obj2.push(s.objectives[1]);

            this.obj1_data.x.push(this.obj1_data.x.length);
            this.obj1_data.y.push(s.objectives[0]);

            this.obj2_data.x.push(this.obj2_data.x.length);
            this.obj2_data.y.push(s.objectives[1]);

            this.obj3_data.x.push(this.obj3_data.x.length);
            this.obj3_data.y.push(s.objectives[2]);

            this.obj4_data.x.push(this.obj4_data.x.length);
            this.obj4_data.y.push(s.objectives[3]);


            var p_data = [];
            for(j = 0; j < this.num_parameters; j++){
                p_data.push(s.x[j]);
            }
            var trace = {
                  x: this.params_name,
                  y: p_data,
                  type: 'scatter'
                };
            this.params_data[i] = trace;
        }

        //对目标值的可视化
        var objectives = {
          x: obj1,
          y: obj2,
          mode: 'markers',
          type: 'scatter'
        };
        this.objectives_data[0] = objectives;
        this.layout1.title = '第' + num_generations + "代种群";
        on_draw = true;
        Plotly.newPlot('prato_plot',this.objectives_data,this.layout1).then(function(){
            on_draw = false;
            setTimeout(fetch_and_update,100);
        });

        /*$("body").append("<div class='prato' id='p"+num_generations+"'></div>");
        Plotly.newPlot('p'+num_generations,this.objectives_data,this.layout1).then(function(gd) {
          Plotly.downloadImage(gd, {
            format: 'png',
            height: 400,
            width: 400,
            filename: 'newplot' + Math.random()
          })
        });*/

        //对优化参数进行可视化
        this.layout2.title = '第' + num_generations + "代优化参数";
        Plotly.redraw('params_plot');

        //对目标值的数据进行可视化
        Plotly.redraw('obj1_plot');
        Plotly.redraw('obj2_plot');
        Plotly.redraw('obj3_plot');
        Plotly.redraw('obj4_plot');

    }

    this.init_visualize();
}



/***
    单个方案的处理
*/
var solution_counter = 0;
function Solution(num_parameters,x_bounds,num_objectives){
    this.num_parameters = num_parameters;
    this.x = Array(num_parameters).fill(0);
    this.x_bounds = x_bounds;
    this.normal_x = Array(num_parameters).fill(0);

    this.num_objectives = num_objectives;
    this.objectives = Array(num_objectives).fill(0);
    
    this.rank = Number.MAX_SAFE_INTEGER;
    this.distance = 0.0;

    solution_counter += 1;
    this.name = "s" + solution_counter;


    this.evaluate_solution = function(){
        //根据x求取多个目标，在本例中：将x传到ruby,获取四个目标值
        
        this.objectives[0] = this.test_obj1();
        this.objectives[1] = this.test_obj2();
        this.objectives[2] = this.test_obj3();
        this.objectives[3] = this.test_obj4();
    }

    this.test_obj1 = function(){
        return Math.pow(this.x[0],2);
    }

    this.test_obj2 = function(){
        return Math.pow(this.x[0]-2.0 ,2);
    }

    this.test_obj3 = function(){
        return Math.pow(this.x[0]-3.0,2);
    }

    this.test_obj4 = function(){
        return Math.pow(this.x[0]-4.0,2);
    }

    this.crossover = function(other){
        var child_solution = new Solution(this.num_parameters, this.x_bounds, this.num_objectives);
        var g1,g2;
        this.normalize();
        other.normalize();
        for(var i =0; i < this.num_parameters; i++){
            child_solution.normal_x[i] = Math.sqrt(this.normal_x[i] * other.normal_x[i]);
        }
        child_solution.denormalize();

        return child_solution;
    }

    this.mutate = function(){
        var mutate_gene_i = Math.floor(Math.random() * this.num_parameters);
        if(mutate_gene_i == this.num_parameters) mutate_gene_i -= 1;
        //在x上下限范围内进行某个基因位的突变
        this.x[mutate_gene_i] = this.x_bounds[mutate_gene_i][0] + Math.random() * (this.x_bounds[mutate_gene_i][1] - this.x_bounds[mutate_gene_i][0]);
    }

    /**
        判断本方案是不是比其他方案帕累托更优
    */
    this.can_dominate = function(other){
        var dominates = false;
        for(var i = 0; i < this.num_objectives; i++){
            if(this.objectives[i] > other.objectives[i]){
                return false;
            }
            else{
                dominates = true;
            }
        }
        return true;
    }


    this.normalize = function(){
        var i;
        for(i = 0; i < this.num_parameters; i++){
            this.normal_x[i] = (this.x[i] - this.x_bounds[i][0]) /  (this.x_bounds[i][1] - this.x_bounds[i][0]);
        }
    }

    this.denormalize = function(){
        var i;
        for(i = 0; i < this.num_parameters; i++){
            this.x[i] = this.x_bounds[i][0]  + this.normal_x[i] * (this.x_bounds[i][1] - this.x_bounds[i][0]);
        }
    }
}


