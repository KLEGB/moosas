//// test data with latitude and longitude
//var X = [
//    [10.0001, 10.0001], [10.0002, 10.0002], [10.0003, 10.0003], [10.0004, 10.0004],
//    [20.0001, 20.0001], [20.0002, 20.0002], [20.0003, 20.0003], [20.0004, 20.0004],
//    [30.0001, 30.0001], [30.0002, 30.0002], [30.0003, 30.0003], [30.0004, 30.0004],
//    [40.0001, 40.0001], [40.0002, 40.0002], [40.0003, 40.0003], [40.0004, 40.0004],
//    [70, 70], 
//    [80, 80]
//];
//var eps = 100;
//var MinPts = 4;
 
// spatial distance
//var Lbound = [[52.0,57.0],[40.0,45.0],[40.0,45.0],[25.0,40.0],[25.0,40.0],[25.0,40.0],[15.0,27.0],[15.0,27.0],[15.0,27.0],[15.0,27.0]];
//var Lrange = [5.0, 5.0, 5.0, 15.0, 15.0, 15.0, 12.0, 12.0, 12.0, 12.0];

var Lbound = [[10.0,57.0],[10.0,57.0],[10.0,57.0],[10.0,57.0],[10.0,57.0],[10.0,57.0],[10.0,57.0],[10.0,57.0],[10.0,57.0],[10.0,57.0]];
var Lrange = [47.0,47.0,47.0,47.0,47.0,47.0,47.0,47.0,47.0,47.0];



function sp_dist(a, b, eps) {
    var i;
    var d = 0.0;
    for (i = 0; i < 10 ; i ++){
        d = Math.abs((a[i]-b[i]) / Lrange[i]);//Math.pow((a[i]-b[i]) / Lrange[i],2);
        if( d > eps){
            return 1.0;
        }
    }
    d = Math.sqrt(d);
    return 0.0;
}
 
// retrieve list of neighbors
function retrieve_neighbors(eps, point, cluster) {
    var neighbors = [];     // list of neighbor
    //var dlist = [];
    for (var iter = 0; iter < cluster.length; iter++) {
        var dist = sp_dist(point, cluster[iter],eps);
//        var dist2 = tp_dist(point, cluster[iter]);
        //dlist.push(dist);
        if (dist < 1.0) {
            neighbors.push(iter);
        }
    }
    //console.log(dlist);
    return neighbors;
}
 
// main function
var dbscan = function(X, eps, MinPts) {
    var cluster_label = 0; // label meaning: 0:unmarked; 1,2,3,...:cluster label; "noise":noise
    var labels = new Array(X.length).fill(0); // new an 0 array to store labels
    var clusters = []; // final output
 
    // clustering data points
    for (var i = 0; i < X.length; i++) {
        if (labels[i] != 0){
            continue;
        }

        var neighbors = retrieve_neighbors(eps, X[i], X);
 
        cluster_label += 1;  // construct a new cluster
        var cluster = [];   // construct cluster

        // mark label for all unmarked neighbors
        for (var j1 = 0; j1 < neighbors.length; j1++) {
            // if no other labels
            if (labels[neighbors[j1]] === 0 || labels[neighbors[j1]] === "noise") {
                labels[neighbors[j1]] = cluster_label;
                cluster.push(neighbors[j1]);
            }
        }

        clusters.push(cluster);

        /*
        if (neighbors.length < MinPts) {
            // if it is unmarked, mark it "noise"
            if (labels[i] === 0) {
                labels[i] = "noise";
            }
        } else {
            cluster_label += 1;  // construct a new cluster
            var cluster = [];   // construct cluster
 
            // mark label for all unmarked neighbors
            for (var j1 = 0; j1 < neighbors.length; j1++) {
                // if no other labels
                if (labels[neighbors[j1]] === 0 || labels[neighbors[j1]] === "noise") {
                    labels[neighbors[j1]] = cluster_label;
                    cluster.push(neighbors[j1]);
                }
            }
 
            // check the sub-circle of all objects
            while (neighbors.length !== 0) {
                var j2;
                j2 = neighbors.pop();
                var sub_neighbors = retrieve_neighbors(eps, X[j2], X);
 
                // mark all unmarked neighbors
                if (sub_neighbors.length >= MinPts) {
                    for (var k = 0; k < sub_neighbors.length; k++) {
                        // if no other labels 
                        if (labels[sub_neighbors[k]] === 0 || labels[sub_neighbors[k]] === "noise") {
                            neighbors.push(sub_neighbors[k]);
                            labels[sub_neighbors[k]] = cluster_label;
                            cluster.push(sub_neighbors[k]);
                        }
                    }
                }
            }
 
            // remove cluster of small size
            if (cluster.length < MinPts) {
                for (var j3 = 0; j3 < X.length; j3++) {
                    if (labels[j3] === cluster_label) {
                        labels[j3] = "noise";
                    }
                }
            } else {
                clusters.push(cluster);
            }
        }*/
    }
 
    //console.log(clusters);
    return clusters;
}
