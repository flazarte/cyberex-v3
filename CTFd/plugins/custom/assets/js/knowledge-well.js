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


const  knowledgeGraph = () => {
    var option;

   return $.get(`/api/v2/directorate/documentation/knowledge/multiplayers`,
        function (response) {
            const option = {
                title: {
                  left: "center",
                  text: "Knowledge Well Breakdown \n (KNOW)"
                },
                tooltip: {
                  trigger: "item"
                },
                toolbox: {
                  show: true,
                  feature: {
                    saveAsImage: {}
                  }
                },
                legend: {
                  type: 'scroll',
                  orient: "horizontal",
                  top: "bottom",
                  right: 0,
                  data: []
                },
                series: [
                  {
                    name: "Knowledge Well Points",
                    type: "pie",
                    radius: ["30%", "50%"],
                    avoidLabelOverlap: false,
                    label: {
                      show: false,
                      position: "center"
                    },
                    itemStyle: {
                      normal: {
                        label: {
                          show: true,
                          formatter: function(data) {
                            return `${data.value}`;
                          }
                        },
                        labelLine: {
                          show: true
                        }
                      },
                      emphasis: {
                        label: {
                          show: true,
                          position: "center",
                          textStyle: {
                            fontSize: "14",
                            fontWeight: "normal"
                          }
                        }
                      }
                    },
                    emphasis: {
                      label: {
                        show: true,
                        fontSize: "30",
                        fontWeight: "bold"
                      }
                    },
                    labelLine: {
                      show: false
                    },
                    data: []
                  }
                ]
              };
          
            const solves = response.data;
            const teams = [];
            const knowledges = [];

            for (let i = 0; i < solves.length; i++) {
                teams.push(solves[i].name);
                knowledges.push(solves[i].value);
            }

            const keys = teams.filter((elem, pos) => {
                return teams.indexOf(elem) == pos;
            });

            const counts = [];
            for (let i = 0; i < keys.length; i++) {
                let count = 0;
                for (let x = 0; x < teams.length; x++) {
                if (teams[x] == keys[i]) {
                    count++;
                }
                }
                counts.push(count);
            }

            keys.forEach((team, index) => {
                option.legend.data.push(team);
                option.series[0].data.push({
                value: knowledges[index],
                name: team,
                itemStyle: { color: popRandomColor(team) }
                });
            });

            let chart = echarts.init(document.querySelector("#ctk-knowledge-well-graph"));
            chart.setOption(option);
        }
    );

};

//Display Chart
function knowledgeWell(){
    knowledgeGraph();
}

//////////////////////
//// Individual
/////////////////////
const  knowledgeUsersGraph = () => {
    var option;

   return $.get(`/api/v2/directorate/documentation/knowledge/individuals`,
        function (response) {
            const option = {
                title: {
                  left: "center",
                  text: "Knowledge Well Breakdown \n (KNOW)"
                },
                tooltip: {
                  trigger: "item"
                },
                toolbox: {
                  show: true,
                  feature: {
                    saveAsImage: {}
                  }
                },
                legend: {
                  type: "scroll",
                  orient: "horizontal",
                  top: "bottom",
                  right: 0,
                  data: []
                },
                series: [
                  {
                    name: "Knowledge Well Points",
                    type: "pie",
                    radius: ["30%", "50%"],
                    avoidLabelOverlap: false,
                    label: {
                      show: false,
                      position: "center"
                    },
                    itemStyle: {
                      normal: {
                        label: {
                          show: true,
                          formatter: function(data) {
                            return `${data.value}`;
                          }
                        },
                        labelLine: {
                          show: true
                        }
                      },
                      emphasis: {
                        label: {
                          show: true,
                          position: "center",
                          textStyle: {
                            fontSize: "14",
                            fontWeight: "normal"
                          }
                        }
                      }
                    },
                    emphasis: {
                      label: {
                        show: true,
                        fontSize: "30",
                        fontWeight: "bold"
                      }
                    },
                    labelLine: {
                      show: false
                    },
                    data: []
                  }
                ]
              };
          
            const solves = response.data;
            const teams = [];
            const knowledges = [];

            for (let i = 0; i < solves.length; i++) {
                teams.push(solves[i].name);
                knowledges.push(solves[i].value);
            }

            const keys = teams.filter((elem, pos) => {
                return teams.indexOf(elem) == pos;
            });

            const counts = [];
            for (let i = 0; i < keys.length; i++) {
                let count = 0;
                for (let x = 0; x < teams.length; x++) {
                if (teams[x] == keys[i]) {
                    count++;
                }
                }
                counts.push(count);
            }

            keys.forEach((team, index) => {
                option.legend.data.push(team);
                option.series[0].data.push({
                value: knowledges[index],
                name: team,
                itemStyle: { color: popRandomColor(team) }
                });
            });

            let chart = echarts.init(document.querySelector("#ctk-knowledge-well-users-graph"));
            chart.setOption(option);

            $("#ctk-tab").on("click", '[role="tab"]', function(event) {
                var $button = $(event.currentTarget);
                if ($button.is("a#users-tab.nav-link")) {
                    $('#ctk-knowledge-well-users-graph').css({
                        visibility: "hidden",
                        height: '0px',
                      });
                  setTimeout(function(){
                    $('#ctk-knowledge-well-users-graph').css({
                        visibility: "visible",
                        height: '325px',
                      });
                      chart.resize();
                  }, 1000);
                }
              });
        }
    );

};

//Display Chart
function knowledgeWellUsers(){
    knowledgeUsersGraph();
}


