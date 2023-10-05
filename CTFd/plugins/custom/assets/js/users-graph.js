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


const userGraph = () => {
    var option;

   return $.get(`/api/v2/scoreboard/individuals`,
        function (response) {
            const places = response.data;

            const teams = Object.keys(places);
            if (teams.length === 0) {
            return false;
            }

            const option = {
                title: {
                  left: "center",
                  text: `All time scoreboard (Apprentice - Warrior - Conqueror)`
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


            $("#ctk-tab").on("click", '[role="tab"]', function(event) {
              var $button = $(event.currentTarget);
              if ($button.is("a#users-tab.nav-link")) {
                $('#ctk-scoreboard').css({
                  visibility: "hidden",
                  height: '0px',
                });
                $('#ctk-spinner').css({
                  visibility: "visible",
                  height: '325px'
                });
                setTimeout(function(){
                  $('#ctk-scoreboard').css({
                    visibility: "visible",
                    height: '325px',
                  });
                  $('#ctk-spinner').css({
                    visibility: "hidden",
                    height: '0px'
                  });
                    chart.resize();
                }, 1000);
              }
            });

            //directorate dashboard switch
            $('#ctk-individual').click(function(){
              setTimeout(function(){
                chart.resize();
              }, 1000);
            });
            
        }
    );

};

function CTK_users_graph(){
    userGraph();
}


