// function ctkgraph(ctk_id) {
//     var chartDom = document.getElementById('ctk-scoreboard');
//     var myChart = echarts.init(chartDom);
//     var option;

//     $.get(`/api/v2/scoreboard/${ctk_id}`,
//         function (data) {
//             run(data);
//         }
//     );

//     function run(data) {
//         var ctk_teams = [];
//         var ctk_series_teams = [];
//         var t_score = [];
//         echarts.util.each(data.top10, function (team, index) {
//             var teams_score = [];
//             var ctk_team_dates = [];
//             ctk_teams.push(team.name);
//             echarts.util.each(data.board, function (team_data) {
//                 var teams_score_date = [];
//                 if (team_data[2] === team.name) {
//                     teams_score.push({
//                         'score': team_data[3],
//                         'date': team_data[1]
//                     });
//                     ctk_team_dates = {
//                         'id': index,
//                         'name': team_data[2],
//                         'type': 'line',
//                         'emphasis': {
//                             'focus': 'series'
//                         },
//                         // 'stack' : '',
//                         'data': '',
//                     };


//                 }
//             });

//             t_score.push(teams_score);
//             ctk_series_teams.push(ctk_team_dates);
//         });

//         echarts.util.each(ctk_series_teams, function (team, index) {
//             if (team.id === index) {
//                 var final_score = [];
//                 echarts.util.each(data.dates, function (team_date) {
//                     var score = [];
//                     echarts.util.each(t_score[team.id], function (team_score) {
//                         if (team_date.date === team_score.date) {
//                             final_score.push(team_score.score);
//                             // score = team_score.score;
//                         } else {
//                             // final_score = ;
//                         }
//                     });
//                     // final_score.push(score);
//                 });

//                 // team.data = t_score[team.id];
//                 team.data = final_score;
//             }
//         });
//         //dates
//         var ctk_dates = [];
//         echarts.util.each(data.dates, function (date) {
//             ctk_dates.push(date.date);
//         });

//         option = {
//             animationDuration: 10000,
//             title: {
//                 text: `${data.cat_name.category} Players`
//             },
//             tooltip: {
//                 order: 'valueDesc',
//                 trigger: 'axis'
//             },
//             legend: {
//                 data: ctk_teams
//             },
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
//                         title: `Download ${data.cat_name.category} ScoreBoard`,
//                         name: `${data.cat_name.category}`,
//                     }
//                 }
//             },
//             xAxis: {
//                 type: 'category',
//                 name: 'Date',
//                 boundaryGap: false,
//                 data: ctk_dates,
//                 axisTick: {
//                     alignWithLabel: true,
//                 }
//             },
//             yAxis: {
//                 type: 'value',
//                 name: 'Scores',
//                 splitArea: {
//                     show: true,
//                 },
//             },
//             series: ctk_series_teams
//         };

//         option && myChart.setOption(option);

//     }

// }

// revision latest
// const graph = $("#ctk-scoreboard");
// const table = $("#scoreboard tbody");

// const buildGraphData = () => {
//     return $.get(`/api/v2/scoreboard/top/10`,
//         function (response) {
//             const places = response.data;
  
//       const teams = Object.keys(places);
//       if (teams.length === 0) {
//         return false;
//       }
  
//       const option = {
//         title: {
//           left: "center",
//           text: "Top 10 " + "Users"
//         },
//         tooltip: {
//           trigger: "axis",
//           axisPointer: {
//             type: "cross"
//           }
//         },
//         legend: {
//           type: "scroll",
//           orient: "horizontal",
//           align: "left",
//           bottom: 35,
//           data: []
//         },
//         toolbox: {
//           feature: {
//             dataZoom: {
//               yAxisIndex: "none"
//             },
//             saveAsImage: {}
//           }
//         },
//         grid: {
//           containLabel: true
//         },
//         xAxis: [
//           {
//             type: "time",
//             boundaryGap: false,
//             data: []
//           }
//         ],
//         yAxis: [
//           {
//             type: "value"
//           }
//         ],
//         dataZoom: [
//           {
//             id: "dataZoomX",
//             type: "slider",
//             xAxisIndex: [0],
//             filterMode: "filter",
//             height: 20,
//             top: 35,
//             fillerColor: "rgba(233, 236, 241, 0.4)"
//           }
//         ],
//         series: []
//       };
  
//       for (let i = 0; i < teams.length; i++) {
//         const team_score = [];
//         const times = [];
//         for (let j = 0; j < places[teams[i]]["solves"].length; j++) {
//           team_score.push(places[teams[i]]["solves"][j].value);
//           const date = places[teams[i]]["solves"][j].date;
//           times.push(date);
//         }
//         console.log(times);
//         const accumulate = arr => arr.map((sum => value => sum += value)(0));
//         // const total_scores = cumulativeSum(team_score);
//         const total_scores = accumulate(team_score);
//         var scores = times.map(function(e, i) {
//           return [e, total_scores[i]];
//         });
  
//         option.legend.data.push(places[teams[i]]["name"]);
  
//         const data = {
//           name: places[teams[i]]["name"],
//           type: "line",
//           label: {
//             normal: {
//               position: "top"
//             }
//           },
//           itemStyle: {
//             // normal: {
//             //   color: colorHash(places[teams[i]]["name"] + places[teams[i]]["id"])
//             // }
//           },
//           data: scores
//         };
//         option.series.push(data);
//       }
  
//       return option;
//         }
//      ); 
      
//   };
  
//   const createGraph = () => {
//     buildGraphData().then(option => {
//       if (option === false) {
//         // Replace spinner
//         graph.html(
//           '<h3 class="opacity-50 text-center w-100 justify-content-center align-self-center">No solves yet</h3>'
//         );
//         return;
//       }
  
//       graph.empty(); // Remove spinners
//       let chart = echarts.init(document.querySelector("#ctk-scoreboard"));
//       chart.setOption(option);
  
//     //   $(window).on("resize", function() {
//         if (chart != null && chart != undefined) {
//           chart.resize();
//         }
//     //   });
//     });
//   };
  
//   const updateGraph = () => {
//     buildGraphData().then(option => {
//       let chart = echarts.init(document.querySelector("#ctk-scoreboard"));
//       chart.setOption(option);
//     });
//   };
  
//   function update() {
//     // updateScores();
//     updateGraph();
//   }
  
//   $(() => {
//     setInterval(update, 300000); // Update scores every 5 minutes
//     createGraph();
//   });
  
//   window.updateScoreboard = update;
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


const ctkgraph = () => {
    var option;

   return $.get(`/api/v2/scoreboard/top/10`,
        function (response) {
            const places = response.data;

            const teams = Object.keys(places);
            if (teams.length === 0) {
            return false;
            }

            const option = {
                title: {
                  left: "center",
                  text: `${response.category}` + " Cyber eX Players | " +`${response.mode}`
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
                  // extraCssText: 'background: #03030352; border-radius: 5;color: #fff;',
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

            let chart = echarts.init(document.querySelector("#ctk-scoreboard"));
            chart.setOption(option);

        }
    );

};

function CTK_graph(){
    ctkgraph();
}
