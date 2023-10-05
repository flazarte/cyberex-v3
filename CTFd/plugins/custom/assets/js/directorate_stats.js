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
//multiplayers
function category_breakdown(team_id){
    var chartDom = document.getElementById('categories-pie-graph-team');
    var myChart = echarts.init(chartDom);
    var option;
    $.get(
        `/api/v1/teams/${team_id}/solves`,
        function (responses) {
            run(responses);
        }
    );
    function run(responses) {
        let option = {
            title: {
              left: "center",
              text: "Category Breakdown"
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
              orient: "vertical",
              top: "middle",
              right: 0,
              data: []
            },
            series: [
              {
                name: "Category Breakdown",
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
                        return `${data.percent}% (${data.value})`;
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
          const solves = responses.data;
          const categories = [];
    
          for (let i = 0; i < solves.length; i++) {
            categories.push(solves[i].challenge.category);
          }
    
          const keys = categories.filter((elem, pos) => {
            return categories.indexOf(elem) == pos;
          });
    
          const counts = [];
          for (let i = 0; i < keys.length; i++) {
            let count = 0;
            for (let x = 0; x < categories.length; x++) {
              if (categories[x] == keys[i]) {
                count++;
              }
            }
            counts.push(count);
          }
    
          keys.forEach((category, index) => {
            option.legend.data.push(category);
            option.series[0].data.push({
              value: counts[index],
              name: category,
              itemStyle: { color: popRandomColor(category) }
            });
          });

          option && myChart.setOption(option);
    }
}

//individuals
function category_breakdown_users(user_id){
  var chartDom = document.getElementById('categories-pie-graph-users');
  var myChart = echarts.init(chartDom);
  var option;
  $.get(
      `/api/v1/users/${user_id}/solves`,
      function (responses) {
          run(responses);
      }
  );
  function run(responses) {
      let option = {
          title: {
            left: "center",
            text: "Category Breakdown"
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
            orient: "vertical",
            top: "middle",
            right: 0,
            data: []
          },
          series: [
            {
              name: "Category Breakdown",
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
                      return `${data.percent}% (${data.value})`;
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
        const solves = responses.data;
        const categories = [];
  
        for (let i = 0; i < solves.length; i++) {
          categories.push(solves[i].challenge.category);
        }
  
        const keys = categories.filter((elem, pos) => {
          return categories.indexOf(elem) == pos;
        });
  
        const counts = [];
        for (let i = 0; i < keys.length; i++) {
          let count = 0;
          for (let x = 0; x < categories.length; x++) {
            if (categories[x] == keys[i]) {
              count++;
            }
          }
          counts.push(count);
        }
  
        keys.forEach((category, index) => {
          option.legend.data.push(category);
          option.series[0].data.push({
            value: counts[index],
            name: category,
            itemStyle: { color: popRandomColor(category) }
          });
        });

        option && myChart.setOption(option);
  }
}

//multiplayer
function solves_breakdown(team_id){

    var chartDom = document.getElementById('keys-pie-graph-team');
    var myChart = echarts.init(chartDom);
    var option;
    var solves = $.ajax({ 
        dataType: "json",
        url: `/api/v1/teams/${team_id}/solves`,
        async: true,
        success: function(result) {}                     
      });
      
      
      var fails = $.ajax({ 
        dataType: "json",
        url: `/api/v1/teams/${team_id}/fails`,
        async: true,
        success: function(result) {}  
      });
    
      $.when( solves , fails  ).done(function( a1, a2 ) {
        run(a1, a2);
     });

    function run(solves, fails){
        const solves_count = solves[0].data.length;
        const fails_count = fails[0].meta.count;
        let option = {
          title: {
            left: "center",
            text: "Solve Percentages"
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
            orient: "vertical",
            top: "middle",
            right: 0,
            data: ["Fails", "Solves"]
          },
          series: [
            {
              name: "Solve Percentages",
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
                      return `${data.name} - ${data.value} (${data.percent}%)`;
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
              data: [
                {
                  value: fails_count,
                  name: "Fails",
                  itemStyle: { color: "rgb(207, 38, 0)" }
                },
                {
                  value: solves_count,
                  name: "Solves",
                  itemStyle: { color: "rgb(0, 209, 64)" }
                }
              ]
            }
          ]
        };
        option && myChart.setOption(option);
    }
}

//user
function solves_breakdown_users(user_id){

  var chartDom = document.getElementById('keys-pie-graph-users');
  var myChart = echarts.init(chartDom);
  var option;
  var solves = $.ajax({ 
      dataType: "json",
      url: `/api/v1/users/${user_id}/solves`,
      async: true,
      success: function(result) {}                     
    });
    
    
    var fails = $.ajax({ 
      dataType: "json",
      url: `/api/v1/users/${user_id}/fails`,
      async: true,
      success: function(result) {}  
    });
  
    $.when( solves , fails  ).done(function( a1, a2 ) {
      run(a1, a2);
   });

  function run(solves, fails){
      const solves_count = solves[0].data.length;
      const fails_count = fails[0].meta.count;
      let option = {
        title: {
          left: "center",
          text: "Solve Percentages"
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
          orient: "vertical",
          top: "middle",
          right: 0,
          data: ["Fails", "Solves"]
        },
        series: [
          {
            name: "Solve Percentages",
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
                    return `${data.name} - ${data.value} (${data.percent}%)`;
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
            data: [
              {
                value: fails_count,
                name: "Fails",
                itemStyle: { color: "rgb(207, 38, 0)" }
              },
              {
                value: solves_count,
                name: "Solves",
                itemStyle: { color: "rgb(0, 209, 64)" }
              }
            ]
          }
        ]
      };
      option && myChart.setOption(option);
  }
}

//multiplayer directorate
const chroniclesCountermeasuresGraphDirectorateMulti = (team_id) => {

  // var knowledges = $.ajax({ 
  //   dataType: "json",
  //   url: `/api/v2/directorate/knowledge/team/${team_id}`,
  //   async: true,
  //   success: function(result) {}                     
  // });
  
  // var chronicles = $.ajax({ 
  //   dataType: "json",
  //   url: `/api/v2/directorate/chronicles/team/${team_id}`,
  //   async: true,
  //   success: function(result) {}                     
  // });
  
  
  // var countermeasures = $.ajax({ 
  //   dataType: "json",
  //   url: `/api/v2/directorate/countermeasures/team/${team_id}`,
  //   async: true,
  //   success: function(result) {}  
  // });

//   $.when(  chronicles , countermeasures, knowledges ).done(function( a1, a2, a3 ) {
//     run(a1, a2, a3);
//  });
 
//  function run(chronicles, countermeasure, knowledges){
  // const knowledges_average = knowledges[0].data;
  // const chronicles_average = chronicles[0].data;
  // const countermeasures_average = countermeasure[0].data;
  //  //get the knowledges average
  //  var total_knowledges = 0;
  //  $.each( knowledges_average, function( key, value ) {
  //    total_knowledges += value.average;
  //  });
  // //get the chronicles average
  // var total_chronicles = 0;
  // $.each( chronicles_average, function( key, value ) {
  //   total_chronicles += value.average;
  // });
  // //get the countermeasures average
  // var total_countermeasures = 0;
  // $.each( countermeasures_average, function( key, value ) {
  //   total_countermeasures += value.average;
  // });
var documentation = $.ajax({ 
    dataType: "json",
    url: `/api/v2/directorate/documents/average/team/${team_id}`,
    async: true,
    success: function(result) {}                     
  });
  $.when( documentation ).done(function(documents) {
    run(documents);
 });
function run(documentation){
  const knowledges_average = documentation.data[0].know;
  const chronicles_average = documentation.data[0].do;
  const countermeasures_average = documentation.data[0].learn;
  option = {
    tooltip: {
        trigger: "item",
        axisPointer: {
                type: 'cross'
            },
    },
    legend: {
        orient: 'vertical',
        left: 'left'
      },
      toolbox: {
        show: true,
        feature: {
          saveAsImage: {}
        }
      },
    series: [
      {
        type: 'pie',
        label: true,
        label: {
          show: false,
          position: "center"
        },
        itemStyle: {
          normal: {
            label: {
              show: true,
              formatter: function(data) {
                return `${data.name} - ${data.value}`;
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
        data: [
          {
            value: knowledges_average,
            name: 'Knowledges Well\n(KNOW)',
          },
          {
            value: chronicles_average,
            name: 'Chronicles\n(DO)',
          },
          {
            value: countermeasures_average,
            name: `Countermeasures\n(LEARN)`,
          }
        ],
        radius: '50%'
      }
    ]
  };

    let chart = echarts.init(document.querySelector("#chronicles-average-team"));
    chart.setOption(option);
 }

};

//individual
const chroniclesCountermeasuresGraphDirectorateIndividual = (user_id) => {
  var knowledges = $.ajax({ 
    dataType: "json",
    url: `/api/v2/directorate/knowledge/user/${user_id}`,
    async: true,
    success: function(result) {}                     
  });

  var chronicles = $.ajax({ 
    dataType: "json",
    url: `/api/v2/directorate/chronicles/user/${user_id}`,
    async: true,
    success: function(result) {}                     
  });
  
  
  var countermeasures = $.ajax({ 
    dataType: "json",
    url: `/api/v2/directorate/countermeasures/user/${user_id}`,
    async: true,
    success: function(result) {}  
  });

  $.when(  chronicles , countermeasures, knowledges ).done(function( a1, a2, a3 ) {
    run(a1, a2, a3);
 });
 
 function run(chronicles, countermeasure, knowledges){
  const knowledges_average = knowledges[0].data;
  const chronicles_average = chronicles[0].data;
  const countermeasures_average = countermeasure[0].data;
   //get the knowledges average
   var total_knowledges = 0;
   $.each( knowledges_average, function( key, value ) {
     total_knowledges += value.average;
   });
  //get the chronicles average
  var total_chronicles = 0;
  $.each( chronicles_average, function( key, value ) {
    total_chronicles += value.average;
  });
  //get the countermeasures average
  var total_countermeasures = 0;
  $.each( countermeasures_average, function( key, value ) {
    total_countermeasures += value.average;
  });
  option = {
    tooltip: {
        trigger: "item",
        axisPointer: {
                type: 'cross'
            },
    },
    legend: {
        orient: 'vertical',
        left: 'left'
      },
      toolbox: {
        show: true,
        feature: {
          saveAsImage: {}
        }
      },
    series: [
      {
        type: 'pie',
        label: true,
        label: {
          show: false,
          position: "center"
        },
        itemStyle: {
          normal: {
            label: {
              show: true,
              formatter: function(data) {
                return `${data.name} - ${data.value}`;
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
        data: [
          {
            value: total_knowledges,
            name: 'Knowledge Well\n(KNOW)',
          },
          {
            value: total_chronicles,
            name: 'Chronicles\n(DO)',
          },
          {
            value: total_countermeasures,
            name: `Countermeasures\n(LEARN)`,
          }
        ],
        radius: '50%'
      }
    ]
  };

    let chart = echarts.init(document.querySelector("#chronicles-average-users"));
    chart.setOption(option);
 }

};

$('a.multiplayer .fa-chart-pie').click(function(){
    var team_id = $(this).data('team_id');
    setTimeout(function(){
        solves_breakdown(team_id);
        category_breakdown(team_id);
        chroniclesCountermeasuresGraphDirectorateMulti(team_id);
      }, 900);
  });

//individual
$('a.individual .fa-chart-pie').click(function(){
  var user_id = $(this).data('user_id');
  setTimeout(function(){
    solves_breakdown_users(user_id);
    category_breakdown_users(user_id);
    chroniclesCountermeasuresGraphDirectorateIndividual(user_id);
    }, 900);
});