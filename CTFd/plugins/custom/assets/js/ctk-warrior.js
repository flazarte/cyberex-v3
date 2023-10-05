function warrior() {
    var chartDom = document.getElementById('ctk-warrior-board');
    var myChart = echarts.init(chartDom);
    var option;
    $.get(
        `/api/v2/leatherboard/warrior`,
        function (data) {
            run(data);
        }
    );

    function run(data) {
        option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    // Use axis to trigger tooltip
                    type: 'shadow' // 'shadow' as default; can also be 'line' or 'shadow'
                }
            },
            legend: {},
            toolbox: {
                show: true,
                feature: {
                    mark: {
                        show: true
                    },
                    dataView: {
                        show: true,
                        readOnly: false
                    },
                    restore: {
                        show: true
                    },
                    saveAsImage: {
                        show: true
                    }
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'value'
            },
            yAxis: {
                type: 'category',
                data: data.warrior[0]
            },
            series: [{
                    name: 'Challenges',
                    type: 'bar',
                    stack: 'total',
                    label: {
                        show: true
                    },
                    emphasis: {
                        focus: 'series'
                    },
                    data: data.warrior[1]
                },
                {
                    name: 'Chronicles',
                    type: 'bar',
                    stack: 'total',
                    label: {
                        show: true
                    },
                    emphasis: {
                        focus: 'series'
                    },
                    data: data.warrior[2]
                }
            ]
        };
        option && myChart.setOption(option);
    }
}