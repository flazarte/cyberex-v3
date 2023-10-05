
//Teams
function chronicles_statistics() {
    var chartDom = document.getElementById('ctk-chronicles-directorate');
    var myChart = echarts.init(chartDom);
    var option;
    $.get(
        `/api/v2/statistics`,
        function (data) {
            run(data);
        }
    );

    function run(data) {
        option = {
            tooltip: {
                axisPointer: {
                        type: 'cross'
                    },
                    formatter: function(params) {
                        return  "<p>"+params.value+"</p>";
                }
            },
            legend: {
                orient: 'vertical',
                left: 'left'
              },
            series: [
              {
                type: 'pie',
                label: false,
                data: [
                  {
                    value: data.team.chronicles.graded,
                    name: 'Graded',
                    itemStyle: { color: "green"}
                  },
                  {
                    value: data.team.chronicles.not_graded,
                    name: `Not Graded`,
                    itemStyle: { color: "orange" }
                  }
                ],
                radius: '50%'
              }
            ]
          };
        option && myChart.setOption(option);
    }
}

function countermeasures_statistics() {
    var chartDom = document.getElementById('ctk-countermeasures-directorate');
    var myChart = echarts.init(chartDom);
    var option;
    $.get(
        `/api/v2/statistics`,
        function (data) {
            run(data);
        }
    );

    function run(data) {
        option = {
            tooltip: {
                axisPointer: {
                        type: 'cross'
                    },
                    formatter: function(params) {
                        return  "<p>"+params.value+"</p>";
                }
            },
            legend: {
                orient: 'vertical',
                left: 'left'
              },
            series: [
              {
                type: 'pie',
                label: false,
                data: [
                  {
                    value: data.team.countermeasures.graded,
                    name: 'Graded',
                    itemStyle: { color: "green"}
                  },
                  {
                    value: data.team.countermeasures.not_graded,
                    name: `Not Graded`,
                    itemStyle: { color: "orange" }
                  }
                ],
                radius: '50%'
              }
            ]
          };
        option && myChart.setOption(option);
    }
}


function knowledgeWell_statistics() {
  var chartDom = document.getElementById('ctk-knowledge-directorate');
  var myChart = echarts.init(chartDom);
  var option;
  $.get(
      `/api/v2/statistics`,
      function (data) {
          run(data);
      }
  );

  function run(data) {
      option = {
          tooltip: {
              axisPointer: {
                      type: 'cross'
                  },
                  formatter: function(params) {
                      return  "<p>"+params.value+"</p>";
              }
          },
          legend: {
              orient: 'vertical',
              left: 'left'
            },
          series: [
            {
              type: 'pie',
              label: false,
              data: [
                {
                  value: data.team.knowledgeWell.graded,
                  name: 'Graded',
                  itemStyle: { color: "green"}
                },
                {
                  value: data.team.knowledgeWell.not_graded,
                  name: `Not Graded`,
                  itemStyle: { color: "orange" }
                }
              ],
              radius: '50%'
            }
          ]
        };
      option && myChart.setOption(option);
  }
}


////////////////////////////////////////
///          INDIVIDUALS
///////////////////////////////////////
function user_chronicles_statistics() {
    var chartDom = document.getElementById('ctk-chronicles-directorate-user');
    var myChart = echarts.init(chartDom);
    var option;
    $.get(
        `/api/v2/statistics`,
        function (data) {
            run(data);
        }
    );

    function run(data) {
        option = {
            tooltip: {
                axisPointer: {
                        type: 'cross'
                    },
                    formatter: function(params) {
                        return  "<p>"+params.value+"</p>";
                }
            },
            legend: {
                orient: 'vertical',
                left: 'left'
              },
            series: [
              {
                type: 'pie',
                label: false,
                data: [
                  {
                    value: data.user.chronicles.graded,
                    name: 'Graded',
                    itemStyle: { color: "green"}
                  },
                  {
                    value: data.user.chronicles.not_graded,
                    name: `Not Graded`,
                    itemStyle: { color: "orange" }
                  }
                ],
                radius: '50%'
              }
            ]
          };
        option && myChart.setOption(option);
        //directorate dashboard switch
        $('#ctk-individual').click(function(){
          setTimeout(function(){
            myChart.resize();
          }, 1000);
        });

    }
}

function usercountermeasures_statistics() {
    var chartDom = document.getElementById('ctk-countermeasures-directorate-user');
    var myChart = echarts.init(chartDom);
    var option;
    $.get(`/api/v2/statistics`,function (data) {
            run(data);
        }
    );

    function run(data) {
        option = {
            tooltip: {
                axisPointer: {
                        type: 'cross'
                    },
                    formatter: function(params) {
                        return  "<p>"+params.value+"</p>";
                }
            },
            legend: {
                orient: 'vertical',
                left: 'left'
              },
            series: [
              {
                type: 'pie',
                label: false,
                data: [
                  {
                    value: data.user.countermeasures.graded,
                    name: 'Graded',
                    itemStyle: { color: "green"}
                  },
                  {
                    value: data.user.countermeasures.not_graded,
                    name: `Not Graded`,
                    itemStyle: { color: "orange" }
                  }
                ],
                radius: '50%'
              }
            ]
          };
        option && myChart.setOption(option);
        //directorate dashboard switch
        $('#ctk-individual').click(function(){
          setTimeout(function(){
            myChart.resize();
          }, 1000);
        });
    }
}


function user_knowledge_statistics() {
  var chartDom = document.getElementById('ctk-knowledge-directorate-user');
  var myChart = echarts.init(chartDom);
  var option;
  $.get(
      `/api/v2/statistics`,
      function (data) {
          run(data);
      }
  );

  function run(data) {
      option = {
          tooltip: {
              axisPointer: {
                      type: 'cross'
                  },
                  formatter: function(params) {
                      return  "<p>"+params.value+"</p>";
              }
          },
          legend: {
              orient: 'vertical',
              left: 'left'
            },
          series: [
            {
              type: 'pie',
              label: false,
              data: [
                {
                  value: data.user.knowledgeWell.graded,
                  name: 'Graded',
                  itemStyle: { color: "green"}
                },
                {
                  value: data.user.knowledgeWell.not_graded,
                  name: `Not Graded`,
                  itemStyle: { color: "orange" }
                }
              ],
              radius: '50%'
            }
          ]
        };
      option && myChart.setOption(option);
      //directorate dashboard switch
      $('#ctk-individual').click(function(){
        setTimeout(function(){
          myChart.resize();
        }, 1000);
      });

  }
}
