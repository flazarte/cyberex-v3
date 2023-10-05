// function leatherboard_all() {
//     var chartDom = document.getElementById('ctk-overall-board');
//     var myChart = echarts.init(chartDom);
//     var option;
//     $.get(
//         `/api/v2/leatherboard/overall`,
//         function (data) {
//             run(data);
//         }
//     );

//     function run(data) {
//         option = {
//             tooltip: {
//                 trigger: 'axis',
//                 axisPointer: {
//                     // Use axis to trigger tooltip
//                     type: 'shadow' // 'shadow' as default; can also be 'line' or 'shadow'
//                 }
//             },
//             legend: {},
//             toolbox: {
//                 show: true,
//                 feature: {
//                     mark: {
//                         show: true
//                     },
//                     dataView: {
//                         show: true,
//                         readOnly: false
//                     },
//                     restore: {
//                         show: true
//                     },
//                     saveAsImage: {
//                         show: true,
//                         title: 'Download Overall Graph',
//                         name: 'overall',
//                     }
//                 }
//             },
//             grid: {
//                 left: '3%',
//                 right: '4%',
//                 bottom: '3%',
//                 containLabel: true
//             },
//             xAxis: {
//                 type: 'value'
//             },
//             yAxis: {
//                 type: 'category',
//                 data: data.overall[0]
//             },
//             series: [
//                 {
//                     name: 'Apprentice',
//                     type: 'bar',
//                     stack: 'total',
//                     label: {
//                         show: true
//                     },
//                     emphasis: {
//                         focus: 'series'
//                     },
//                     data: data.overall[1]
//                 },
//                 {
//                     name: 'Warrior',
//                     type: 'bar',
//                     stack: 'total',
//                     label: {
//                         show: true
//                     },
//                     emphasis: {
//                         focus: 'series'
//                     },
//                     data: data.overall[2]
//                 },
//                 {
//                     name: 'Conqueror',
//                     type: 'bar',
//                     stack: 'total',
//                     label: {
//                         show: true
//                     },
//                     emphasis: {
//                         focus: 'series'
//                     },
//                     data: data.overall[3]
//                 },
//                 {
//                     name: 'Chronicles',
//                     type: 'bar',
//                     stack: 'total',
//                     label: {
//                         show: true
//                     },
//                     emphasis: {
//                         focus: 'series'
//                     },
//                     data: data.overall[4]
//                 },
//                 {
//                     name: 'Countermeasure',
//                     type: 'bar',
//                     stack: 'total',
//                     label: {
//                         show: true
//                     },
//                     emphasis: {
//                         focus: 'series'
//                     },
//                     data: data.overall[5]
//                 }
//             ]
//         };
//         option && myChart.setOption(option);
//     }
// }

var colors = [
    "#C0C0C0",
    "#808080",
    "#000000",
    "#FF0000",
    "#800000",
    "#808000",
    "#00FF00",
    "#008000",
    "#00FFFF",
    "#008080",
    "#0000FF",
    "#000080",
    "#FF00FF",
    "#800080"
  ];
  
  function popRandomColor(){
    var rand = Math.random();
    var color = colors[Math.floor(rand*colors.length)];
    colors.splice(Math.floor(rand*colors.length), 1);
    return color;
  }


const overallGraph = () => {
    var option;

   return $.get(`/api/v2/scoreboard/multiplayers`,
        function (response) {
            const places = response.data;

            const teams = Object.keys(places);
            if (teams.length === 0) {
            return false;
            }

            const option = {
                title: {
                  left: "center",
                  text: `All time Scoreboard (Apprentice - Warrior - Conqueror)`
                },
                tooltip: {
                  trigger: "axis",
                  axisPointer: {
                    type: "cross",
                    animation: true,
                  },
                  formatter: function (params) {
                    var colorSpan = color => '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:' + color + '"></span>';
                    let rez = '<p>' + params[0].axisValueLabel + '</p>';
                    params.forEach(item => {
                        var xx = `
                        <p><i class="fas fa-crown d-block mx-auto mb-4" width="10" height="auto" style="color: gold;"> Cyber <small>e</small>x Player</i> </p>
                        <p>${colorSpan(item.color)} ${item.seriesName}: ${item.data[1]}</p>
                        `;
                        rez += xx;
                    });
            
                    return rez;
                  },
                },
                legend: {
                  type: "scroll",
                  orient: "horizontal",
                  align: "left",
                  bottom: 35,
                  data: []
                },
                toolbox: {
                  feature: {
                    dataZoom: {
                      yAxisIndex: "none"
                    },
                    saveAsImage: {}
                  }
                },
                grid: {
                  containLabel: true
                },
                xAxis: [
                  {
                    type: "time",
                    boundaryGap: false,
                    data: []
                  }
                ],
                yAxis: [
                  {
                    type: "value"
                  }
                ],
                dataZoom: [
                  {
                    id: "dataZoomX",
                    type: "slider",
                    xAxisIndex: [0],
                    filterMode: "filter",
                    height: 20,
                    top: 35,
                    fillerColor: "rgba(233, 236, 241, 0.4)"
                  }
                ],
                series: []
              };
          
              for (let i = 0; i < teams.length; i++) {
                const team_score = [];
                const times = [];
                for (let j = 0; j < places[teams[i]]["solves"].length; j++) {
                  team_score.push(places[teams[i]]["solves"][j].value);
                  const date = dayjs(places[teams[i]]["solves"][j].date);
                  times.push(date.toDate());
                }
            
                // const total_scores = cumulativeSum(team_score);
                const accumulate = arr => arr.map((sum => value => sum += value)(0));
                const total_scores = accumulate(team_score);
                var scores = times.map(function(e, i) {
                  return [e, total_scores[i]];
                });
          
                option.legend.data.push(places[teams[i]]["name"]);
          
                const data = {
                  name: places[teams[i]]["name"],
                  type: "line",
                  label: {
                    normal: {
                      position: "top"
                    }
                  },
                  itemStyle: {
                    normal: {
                      color: popRandomColor(places[teams[i]]["name"] + places[teams[i]]["id"])
                    }
                  },
                  data: scores
                };
                option.series.push(data);
              }

              if (option === false) {
                // Replace spinner
                graph.html(
                  '<h3 class="opacity-50 text-center w-100 justify-content-center align-self-center">No solves yet</h3>'
                );
                return;
              }

            let chart = echarts.init(document.querySelector("#ctk-overall-board"));
            chart.setOption(option);
        }
    );

};

//Display Chart
function CTK_multiplayers_graph(){
    overallGraph();
}

