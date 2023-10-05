CTFd._internal.challenge.data = undefined

CTFd._internal.challenge.renderer = CTFd.lib.markdown();


CTFd._internal.challenge.preRender = function () {}

CTFd._internal.challenge.render = function (markdown) {
    return CTFd._internal.challenge.renderer.render(markdown)
}


CTFd._internal.challenge.postRender = function () {
    //set modal c3 category
    var c3_cat_modal_name = $('#c3_cat_name').text();
    $('#c3_modal_cat').text(c3_cat_modal_name);
    //challenge-id
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val());

    //check attempt
    $.getJSON("/api/v2/challenges/"+challenge_id, function (attempt) {
        var attempt_html = ''
        $.each(attempt, function (index, challenger_attempt) {
            if(challenger_attempt.max_attempts > 0){
                attempt_html = '<p> '+challenger_attempt.attempts+"/"+challenger_attempt.max_attempts+' attempts</p>';
                $('div#cyber-ex-attempt.col-md-12').empty();
                $('div#cyber-ex-attempt.col-md-12').append(attempt_html);
            } 
        });     
    });

    //process hints
    var hint_id = $('a#ctk-hints').data('hint-id');
    $(".modal.hints .modal-body").empty();
    $.getJSON("/api/v2/hints/" + hint_id, function (hint_data) {
        var hint_html = '';
        if(hint_data.data){
            hint_html = hint_data.data.html;
            $('.challenge-hints').remove();
            $('#ctk-hints').empty();
            $('#ctk-hints').append('<a class="btn btn-info btn-hint btn-block load-hint" style="color: black;"> <small id="ctk-hint-val"> View Hint </small></a>');
            $(".modal.hints .modal-body").append(hint_html);
        }
    });
    $('.modal#challenge-window').on('click', function (event_hint) {
        var $button_hint = event_hint.target.id;
        if( $button_hint == 'ctk-hint-val'){
            $(".modal.hints").modal("show");
        }
    });
    

    $.getJSON("/api/v2/solves/" + challenge_id, function (solved_data) {
        $('#ctk-solves').empty();
        solved_count = 0;
        if (solved_data) {
            $.each(solved_data, function (index, item_solved) {
                if (item_solved.count) {
                    solved_count = item_solved.count;
                }
            });
            solve_count = solved_count + ' Conquered';
            $('#ctk-solves').append(solve_count);
        }
    });
    $('.modal#challenge-window .solves-participants').on('click', function (event) {
        var $button = $(event.target);
        if ($button) {
            $.getJSON("/api/v2/solves/" + challenge_id, function (solved_name) {
                if (solved_name) {
                    $('tbody#challenge-solves-names').empty();
                    var solve = [];
                    $.each(solved_name, function (index, item_solved_name) {
                        // teams mode
                        if (item_solved_name.mode === 'teams') {
                            solve += '<tr><td><a href="/teams/' + item_solved_name.account_id + '">' + item_solved_name.account_name + '</td><td>' + item_solved_name.date + '</td></tr>';
                        }
                        // users mode
                        if (item_solved_name.mode === 'users') {
                            solve += '<tr><td><a href="/users/' + item_solved_name.user_id + '">' + item_solved_name.account_name + '</td><td>' + item_solved_name.date + '</td></tr>';
                        }
                    });
                    $('tbody#challenge-solves-names').append(solve);
                }
            });
        }
    });

    // solves-participants
    // get challenge api if already solved
    $.getJSON("/api/v2/mysolves/" + challenge_id, function (data_mysolves) {
        if (data_mysolves) {
            if (data_mysolves[0].solved_by_me) {

                var knowledge = `
                    <div id="knowledge-well">
                        <div>
                            <table id="knowledge" class="table table-striped">
                                <thead>
                                    <tr style="color: white">
                                        <td class="text-center" id="del-know"><b>Delete</b></td>
                                        <td style="color: white" class="text-center"><b>File</b></td>
                                        <td style="color: white" class="text-center"><b>Points</b></td>
                                    </tr>
                                </thead>
                                <tbody id="knowledge-well"></tbody>
                            </table>        
                            <div class="btn-cont">
                                <button id="popup-knowledge"> ATTACH KNOWLEDGE WELL (+ POINTS) </button>
                            </div>
                            <p>Download knowledge format <a href="/plugins/custom/chronicles/know.docx"><i class="fas fa-download"></i><small>here..</small></a></p>
                        </div>
                    </div>
                `;

                var upload = `
                    <div id="challenge-files">
                        <div>
                            <table id="filesboard" class="table table-striped">
                                <thead>
                                    <tr style="color: white">
                                        <td class="text-center" id="del-do"><b>Delete</b></td>
                                        <td style="color: white" class="text-center"><b>Documentation</b></td>
                                        <td style="color: white" class="text-center"><b>Points</b></td>
                                    </tr>
                                </thead>
                                <tbody id="write-up"></tbody>
                            </table>
                            <div class="btn-cont">
                                <button id="popup-upload"> ATTACH WRITEUPS FOR DELIBERATION (+ POINTS) </button>
                            </div>
                            <p>Download chronicles format <a href="/plugins/custom/chronicles/do.docx"><i class="fas fa-download"></i><small>here..</small></a></p>
                        </div>
                    </div>
                `;


                var counterMeasure = `
                    <div id="challenge-counterMeasure">
                        <div>
                            <table id="counterMeasure" class="table table-striped">
                                <thead>
                                    <tr style="color: white">
                                        <td class="text-center" id="del-learn"><b>Delete</b></td>
                                        <td style="color: white" class="text-center"><b>File</b></td>
                                        <td style="color: white" class="text-center"><b>Points</b></td>
                                    </tr>
                                </thead>
                                <tbody id="counterMeasure"></tbody>
                            </table>        
                            <div class="btn-cont">
                                <button id="popup-countermeasure"> ATTACH KNOWLEDGE GAIN EXPERIENCE (+ POINTS) </button>
                            </div>
                            <p>Download countermeasure format <a href="/plugins/custom/chronicles/learn.docx"><i class="fas fa-download"></i><small>here..</small></a></p>
                        </div>
                    </div>
                `;

                $("#challenge-input").prop('disabled', true);
                $("#challenge-input").attr('placeholder', 'Throne Conquered!');
                $("button#challenge-submit").prop('disabled', true);

                //show knowledge-well upload
                $("#knowledge-section").append(knowledge);
                $("#popup-knowledge").on('click', function(){
                   $('.upload-knowledge').css({
                       visibility: "visible"
                   });
               });
               
                //show chronicles upload
                $("#upload-section").append(upload);

                $("#popup-upload").on('click', function () {
                    $('.upload-modal').css({
                        visibility: "visible"
                    });
                });
                //show counter measure upload
                $("#upload-counter").append(counterMeasure);

                $("#popup-countermeasure").on('click', function () {
                    $('.upload-countermeasure').css({
                        visibility: "visible"
                    });
                });

                //remove upload Button when published
                if (data_mysolves[0].published){
                    $("#popup-countermeasure").remove();
                    $("#popup-upload").remove();
                    $("#popup-knowledge").remove();
                }
            }
        }

    });
    // check write-ups uploaded files
    $.getJSON("/api/v2/writeups/" + challenge_id, function (data_chronicles) {
        setTimeout(function () {
            if (!$.isEmptyObject(data_chronicles)) {
                $('input#multiFiles').remove();
                $('input#writeup-submit').remove();
                $('#popup-upload').remove();
                if(data_chronicles.published && !data_chronicles.view_ratings){
                    var file_writeup = "<tr><td style=\"color: white\" class=\"text-center\"><i class=\"fas fa-ban\"></i></td><td class=\"text-center\"><a class=\"btn btn-info btn-file mb-1 d-inline-block px-2 w-100 text-truncate\" target=\"_blank\" href=\"" + data_chronicles.location + "\"><i class=\"fas fa-download\"></i><small>" + data_chronicles.name + "</small></a></td><td style=\"color: white\" class=\"text-center\"><p>" + data_chronicles.points + "</p></td></tr>";
                }else if(data_chronicles.published && data_chronicles.view_ratings){
                    $('#del-do').empty();
                    $('#del-do').append("<b>View Ratings</b>");
                    var file_writeup = "<tr><td style=\"color: white\" class=\"text-center\"><button type=\"button\" class=\"btn btn-outline-secondary individualKnowledge-directorate-do-button\" data-toggle=\"tooltip\" data-id=\"" + data_chronicles.id + "\" title=\"View Judge eX Ratings\" data-original-title=\"View Judge eX Ratings\"><i class=\"fas fa-eye do\"></i></button></td><td class=\"text-center\"><a class=\"btn btn-info btn-file mb-1 d-inline-block px-2 w-100 text-truncate\" target=\"_blank\" href=\"" + data_chronicles.location + "\"><i class=\"fas fa-download\"></i><small>" + data_chronicles.name + "</small></a></td><td style=\"color: white\" class=\"text-center\"><p>" + data_chronicles.points + "</p></td></tr>";
                }else{
                    var file_writeup = "<tr><td style=\"color: white\" class=\"text-center\"><i id=\"delete-file\" role=\"button\"class=\"btn-fa fas fa-times delete-file\"></i></td><td class=\"text-center\"><a class=\"btn btn-info btn-file mb-1 d-inline-block px-2 w-100 text-truncate\" target=\"_blank\" href=\"" + data_chronicles.location + "\"><i class=\"fas fa-download\"></i><small>" + data_chronicles.name + "</small></a></td><td style=\"color: white\" class=\"text-center\"><p>" + data_chronicles.points + "</p></td></tr>";
                }  
                $("tbody#write-up").append(file_writeup);
            }
        }, 500);
    });

    //individual knowledge-well graded  points update for direcorate
    $('.modal#challenge-window').on('click', function (event) {
        var $button = $(event.target);
        if ($button.is("button.individualKnowledge-directorate-do-button") || $button.is("i.fa-eye.do")) {
            var id = $(".modal-content .individualKnowledge-directorate-do-button").attr("data-id");
            var directorate_score = ''
            $(".modal.individualChronicles-directorate .modal-body table tbody#chronicle-rater-points").empty();
            $(".modal.individualChronicles-directorate .modal-body table tbody#chronicle-rater-points").empty();
            if (id) {
                $.getJSON(`/api/v2/chronicles/directorate/${id}`, function (directorate_chronicles_data) {
                    if (directorate_chronicles_data.rater) {
                        $.each(directorate_chronicles_data.rater, function (key, rater_item) {
                            directorate_score += `<tr><td>${ rater_item.directorate_name}</td><td>${ rater_item.rater_points}</td><td>${ rater_item.date}</td></tr>`;
                        });
                    }
                    //remove rdated judge eX
                    $(".modal.individualChronicles-directorate .modal-body select#counter-points").css({
                        visibility: "visible"
                    });
                    $(".modal.individualChronicles-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({
                        visibility: "visible",
                        "margin-bottom": "0rem"
                    });
                    if (directorate_chronicles_data.rated == true) {
                        // $(".modal.individualChronicles-directorate .modal-body select#counter-points").css({visibility: "hidden"});
                        // $(".modal.individualChronicles-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({visibility: "hidden", "margin-bottom" : "-10rem"});
                    }
                    $(".modal.individualChronicles-directorate .modal-body form").attr('action', `/api/v2/chronicles/directorate/${id}`);
                    $(".modal.individualChronicles-directorate .modal-body table tbody#chronicle-rater-points").empty();
                    $(".modal.individualChronicles-directorate .modal-body table tbody#chronicle-rater-points").append(directorate_score);
                    $(".modal.individualChronicles-directorate").modal("show");
                });
            }
        }
    });

    var challenge_id_writeups = parseInt(CTFd.lib.$('#challenge-id').val());
    //upload file
    $('.modal#challenge-window').on('click', function (event) {
        var $button = $(event.target);

        $('#challenge-writeup').find('input').eq(0).on('change', function (index, el) {
            $("input#writeup-submit").prop('disabled', false);
        })

        if ($button.is("input#writeup-submit")) {

            // Disabled submit button to avoid multiple submission
            $("input#writeup-submit").prop('disabled', true);


            //upload documenations/write ups
            if ($('#challenge-writeup').length) {



                $('.upload-modal').css({
                    visibility: "hidden"
                })

                var form_data = new FormData();
                var ins = document.getElementById('multiFiles').files.length;
                if (ins == 0) {
                    $('#msg').html('<span style="color:red">Select at least one file</span>');
                    return;
                }
                //get files upload
                form_data.append("files", document.getElementById('multiFiles').files[0]);
                //get challenge data
                form_data.append("challenge", challenge_id_writeups);
                $('input#writeup-submit').prop('disabled', true);


                $('.loading-status').css({
                    visibility: "visible"
                })
                $.ajax({
                    url: '/uploader',
                    dataType: 'json',
                    cache: false,
                    contentType: false,
                    processData: false,
                    data: form_data,
                    type: 'post',
                    success: function (chronicles_response) {

                        $('input#multiFiles').remove();
                        $('input#writeup-submit').remove();
                        $('#popup-upload').remove();
                        $(".modal.upload").modal("show");
                        $.each(chronicles_response, function (key, data_chronicles) {
                            if (key !== 'message') {
                                // $('#msg').append(key + ' -> ' + data + '<br/>');
                            } else {
                                $('#msg').append(data_chronicles + '<br/>');
                                setTimeout(function () {
                                    $('#msg').empty();
                                }, 800);
                            }
                        })

                        $('.loading-status').css({
                            visibility: "hidden"
                        })
                    },
                    error: function (chronicles_response) {
                        // $('#msg').html(chronicles_response.message);
                        alert(chronicles_response.responseJSON.message);
                        $('input#writeup-submit').prop('disabled', false);
                    }
                });


            } else {
                // Enabled submit button to avoid multiple submission
                $("input#writeup-submit").prop('disabled', false);
            }
        }
    });

    //delete file
    $('.modal#challenge-window').on('click', function (event) {
        var $button = $(event.target);
        if ($button.is("i#delete-file")) {
            var r = confirm("Are you sure you want to delete?");
            if (r) {
                $.ajax({
                    url: '/uploader',
                    dataType: 'json',
                    cache: false,
                    contentType: 'application/json; charset=utf-8',
                    processData: false,
                    data: JSON.stringify({
                        challenge: challenge_id_writeups
                    }),
                    type: 'delete',
                    success: function (del_response) {
                        $.each(del_response, function (index, element_delete) {
                            if (element_delete.success) {
                                location.reload();
                            }
                        });
                    },
                    error: function (del_response) {
                        // $('#msg').html(del_response.message);
                        alert(del_response.responseJSON.message);
                    }
                });
            }

        }
    });

    //check counter measure is already uploaded files
    var challenge_id_counter = parseInt(CTFd.lib.$('#challenge-id').val());
    $.getJSON("/api/v2/countermeasure/" + challenge_id_counter, function (counterMeasure) {
        setTimeout(function () {
            if (!$.isEmptyObject(counterMeasure)) {
                $('input#counterfiles').remove();
                $('input#counter-submit').remove();
                $('#popup-countermeasure').remove();
                if(counterMeasure.published && !counterMeasure.view_ratings){
                    var file_counter = "<tr><td style=\"color: white\" class=\"text-center\"><i class=\"fas fa-ban\"></i></td><td class=\"text-center\"><a class=\"btn btn-info btn-file mb-1 d-inline-block px-2 w-100 text-truncate\" target=\"_blank\" href=\"" + counterMeasure.location + "\"><i class=\"fas fa-download\"></i><small>" + counterMeasure.name + "</small></a></td><td style=\"color: white\" class=\"text-center\"><p>" + counterMeasure.points + "</p></td></tr>";
                }else if (counterMeasure.published && counterMeasure.view_ratings) {
                    $('#del-learn').empty();
                    $('#del-learn').append("<b>View Ratings</b>");
                    var file_counter = "<tr><td style=\"color: white\" class=\"text-center\"><button type=\"button\" class=\"btn btn-outline-secondary individualKnowledge-directorate-learn-button\" data-toggle=\"tooltip\" data-id=\"" + counterMeasure.id + "\" title=\"View Judge eX Ratings\" data-original-title=\"View Judge eX Ratings\"><i class=\"fas fa-eye learn\"></i></button></td><td class=\"text-center\"><a class=\"btn btn-info btn-file mb-1 d-inline-block px-2 w-100 text-truncate\" target=\"_blank\" href=\"" + counterMeasure.location + "\"><i class=\"fas fa-download\"></i><small>" + counterMeasure.name + "</small></a></td><td style=\"color: white\" class=\"text-center\"><p>" + counterMeasure.points + "</p></td></tr>";
                }else{
                    var file_counter = "<tr><td style=\"color: white\" class=\"text-center\"><i id=\"delete-counter\" role=\"button\"class=\"btn-fa fas fa-times delete-file\"></i></td><td class=\"text-center\"><a class=\"btn btn-info btn-file mb-1 d-inline-block px-2 w-100 text-truncate\" target=\"_blank\" href=\"" + counterMeasure.location + "\"><i class=\"fas fa-download\"></i><small>" + counterMeasure.name + "</small></a></td><td style=\"color: white\" class=\"text-center\"><p>" + counterMeasure.points + "</p></td></tr>";
                }
                $("tbody#counterMeasure").append(file_counter);
            }
        }, 500);
    });

    //individual countermeasure graded  points update for direcorate
    $('.modal#challenge-window').on('click', function (event) {
        var $button = $(event.target);
        if ($button.is("button.individualKnowledge-directorate-learn-button") || $button.is("i.fa-eye.learn")) {
            var id = $(".modal-content .individualKnowledge-directorate-learn-button").attr("data-id");
            var directorate_score = ''
            $(".modal.individualCountermeasure-directorate .modal-body table tbody#chronicle-rater-points").empty();
            $(".modal.individualCountermeasure-directorate .modal-body table tbody#chronicle-rater-points").empty();
            if (id) {
                $.getJSON(`/api/v2/countermeasures/directorate/${id}`, function (directorate_chronicles_data) {
                    if (directorate_chronicles_data.rater) {
                        $.each(directorate_chronicles_data.rater, function (key, rater_item) {
                            directorate_score += `<tr><td>${ rater_item.directorate_name}</td><td>${ rater_item.rater_points}</td><td>${ rater_item.date}</td></tr>`;
                        });
                    }
                    //remove rdated judge eX
                    $(".modal.individualCountermeasure-directorate .modal-body select#counter-points").css({
                        visibility: "visible"
                    });
                    $(".modal.individualCountermeasure-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({
                        visibility: "visible",
                        "margin-bottom": "0rem"
                    });
                    if (directorate_chronicles_data.rated == true) {
                        // $(".modal.individualCountermeasure-directorate .modal-body select#counter-points").css({visibility: "hidden"});
                        // $(".modal.individualCountermeasure-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({visibility: "hidden", "margin-bottom" : "-10rem"});
                    }
                    $(".modal.individualCountermeasure-directorate .modal-body form").attr('action', `/api/v2/countermeasures/directorate/${id}`);
                    $(".modal.individualCountermeasure-directorate .modal-body table tbody#chronicle-rater-points").empty();
                    $(".modal.individualCountermeasure-directorate .modal-body table tbody#chronicle-rater-points").append(directorate_score);
                    $(".modal.individualCountermeasure-directorate").modal("show");
                });
            }
        }
    });

    //upload countermeasure
    $('.modal#challenge-window').on('click', function (event) {
        var $button = $(event.target);

        $('#challenge-counterMeasure').find('input').eq(0).on('change', function (index, el) {
            $("input#counter-submit").prop('disabled', false);
        })

        if ($button.is("input#counter-submit")) {

            // Disabled submit button to avoid multiple submission
            $("input#counter-submit").prop('disabled', true);

            //upload documenations/write ups
            var form_data = new FormData();
            var ins = document.getElementById('counterfiles').files.length;
            if (ins == 0) {
                $('#countermsg').html('<span style="color:red">Select at least one file</span>');
                // Disabled submit button to avoid multiple submission
                $("input#counter-submit").prop('disabled', false);

                return;
            }

            $('.upload-countermeasure').css({
                visibility: "hidden"
            })

            //get files upload
            form_data.append("files", document.getElementById('counterfiles').files[0]);
            //get challenge data
            form_data.append("challenge", challenge_id_counter);
            $('input#counter-submit').prop('disabled', true);

            $('.loading-status').css({
                visibility: "visible"
            })

            $.ajax({
                url: '/api/v2/countermeasure/' + challenge_id_counter,
                dataType: 'json',
                cache: false,
                contentType: false,
                processData: false,
                data: form_data,
                type: 'POST',
                success: function (counter_response) {
                    $('input#counterfiles').remove();
                    $('input#counter-submit').remove();
                    $('#popup-countermeasure').remove();
                    $(".modal.upload").modal("show");
                    $.each(counter_response, function (key, data_counter) {
                        if (key !== 'message') {
                            // $('#msg').append(key + ' -> ' + data + '<br/>');
                        } else {
                            $('#countermsg').append(data_counter + '<br/>');
                            setTimeout(function () {
                                $('#countermsg').empty();
                            }, 800);
                        }
                    })
                    $('input#counter-submit').prop('disabled', false);

                    $('.loading-status').css({
                        visibility: "hidden"
                    })
                },
                error: function (counter_response) {
                    // $('#countermsg').html(counter_response.message);
                    alert(counter_response.responseJSON.message);
                    $('input#counter-submit').prop('disabled', false);
                }
            });
        }
    });

    //delete counter file
    $('.modal#challenge-window').on('click', function (event) {
        var $button = $(event.target);
        if ($button.is("i#delete-counter")) {
            var r = confirm("Are you sure you want to delete?");
            if (r) {
                $.ajax({
                    url: '/api/v2/countermeasure/' + challenge_id_counter,
                    dataType: 'json',
                    cache: false,
                    contentType: 'application/json; charset=utf-8',
                    processData: false,
                    data: JSON.stringify({
                        challenge: challenge_id_counter
                    }),
                    type: 'delete',
                    success: function (response_counter_delete) {
                        $.each(response_counter_delete, function (index, element_countr_del) {
                            if (element_countr_del.success) {
                                location.reload();
                            }
                        });
                    },
                    error: function (response_counter_delete) {
                        // $('#countermsg').html(response_counter_delete.message);
                        alert(response_counter_delete.responseJSON.message);
                        
                    }
                });
            }

        }
    });

    //multiple choice answer
    $.getJSON("/api/v2/multiplechoice/" + challenge_id, function (data) {
        var choice = "";
        $("#multiplechoice").empty();
        $.each(data, function (index, item) {
            $("#multiplequestion").append(item.q);
            $.each(item.choices, function (index, item) {
                choice += '<input  type="radio" name="answer" value="' + index + '">' + item + '<br>';
            });
            // setTimeout(function () {
                // data.stopPropagation();
                $("#multiplechoice").empty();
                $("#multiplechoice").append(choice);
            // }, 1000);
        });

    });

//////////////////////
//// Knowledge Well
/////////////////////

 //check knowledge well if  is already uploaded files
 var challenge_id_knowledge = parseInt(CTFd.lib.$('#challenge-id').val());
 $.getJSON("/api/v2/knowledge-well/" + challenge_id_knowledge, function (knowledgeWell) {
     setTimeout(function () {
         if (!$.isEmptyObject(knowledgeWell)) {
             $('input#knowledge-files').remove();
             $('input#knowledge-submit').remove();
             $('#popup-knowledge').remove();
             if(knowledgeWell.published && !knowledgeWell.view_ratings){
                var file_knowledge = "<tr><td style=\"color: white\" class=\"text-center\"><i class=\"fas fa-ban\"></i></td><td class=\"text-center\"><a class=\"btn btn-info btn-file mb-1 d-inline-block px-2 w-100 text-truncate\" target=\"_blank\" href=\"" + knowledgeWell.location + "\"><i class=\"fas fa-download\"></i><small>" + knowledgeWell.name + "</small></a></td><td style=\"color: white\" class=\"text-center\"><p>" + knowledgeWell.points + "</p></td></tr>";
             }else if (knowledgeWell.published && knowledgeWell.view_ratings) {
                $('#del-know').empty();
                $('#del-know').append("<b>View Ratings</b>");
                var file_knowledge = "<tr><td style=\"color: white\" class=\"text-center\"><button type=\"button\" class=\"btn btn-outline-secondary individualKnowledge-directorate-know-button\" data-toggle=\"tooltip\" data-id=\"" + knowledgeWell.id + "\" title=\"View Judge eX Ratings\" data-original-title=\"View Judge eX Ratings\"><i class=\"fas fa-eye know\"></i></button></td><td class=\"text-center\"><a class=\"btn btn-info btn-file mb-1 d-inline-block px-2 w-100 text-truncate\" target=\"_blank\" href=\"" + knowledgeWell.location + "\"><i class=\"fas fa-download\"></i><small>" + knowledgeWell.name + "</small></a></td><td style=\"color: white\" class=\"text-center\"><p>" + knowledgeWell.points + "</p></td></tr>";
             }else{
                var file_knowledge = "<tr><td style=\"color: white\" class=\"text-center\"><i id=\"delete-knowledge\" role=\"button\"class=\"btn-fa fas fa-times delete-file\"></i></td><td class=\"text-center\"><a class=\"btn btn-info btn-file mb-1 d-inline-block px-2 w-100 text-truncate\" target=\"_blank\" href=\"" + knowledgeWell.location + "\"><i class=\"fas fa-download\"></i><small>" + knowledgeWell.name + "</small></a></td><td style=\"color: white\" class=\"text-center\"><p>" + knowledgeWell.points + "</p></td></tr>";
             }
             $("tbody#knowledge-well").append(file_knowledge);
         }
     }, 500);
 });

 //individual knowledge-well graded  points update for direcorate
 $('.modal#challenge-window').on('click', function (event) {
    var $button = $(event.target);
    if ($button.is("button.individualKnowledge-directorate-know-button") || $button.is("i.fa-eye.know")) {
        var id = $(".modal-content .individualKnowledge-directorate-know-button").attr("data-id");
        var directorate_score = ''
        $(".modal.individualKnowledge-directorate .modal-body table tbody#knowledge-rater-points").empty();
        $(".modal.individualKnowledge-directorate .modal-body table tbody#knowledge-rater-points").empty();
        if (id) {
            $.getJSON(`/api/v2/knowledge-well/directorate/${id}`, function (directorate_knowledge_data) {
                if (directorate_knowledge_data.rater) {
                    $.each(directorate_knowledge_data.rater, function (key, rater_item) {
                        directorate_score += `<tr><td>${ rater_item.directorate_name}</td><td>${ rater_item.rater_points}</td><td>${ rater_item.date}</td></tr>`;
                    });
                }
                //remove rdated judge eX
                $(".modal.individualKnowledge-directorate .modal-body select#counter-points").css({
                    visibility: "visible"
                });
                $(".modal.individualKnowledge-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({
                    visibility: "visible",
                    "margin-bottom": "0rem"
                });
                if (directorate_knowledge_data.rated == true) {
                    // $(".modal.individualKnowledge-directorate .modal-body select#counter-points").css({visibility: "hidden"});
                    // $(".modal.individualKnowledge-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({visibility: "hidden", "margin-bottom" : "-10rem"});
                }
                $(".modal.individualKnowledge-directorate .modal-body form").attr('action', `/api/v2/knowledge-well/directorate/${id}`);
                $(".modal.individualKnowledge-directorate .modal-body table tbody#knowledge-rater-points").empty();
                $(".modal.individualKnowledge-directorate .modal-body table tbody#knowledge-rater-points").append(directorate_score);
                $(".modal.individualKnowledge-directorate").modal("show");
            });
        }
    }
});


 $('.modal#challenge-window').on('click', function (event) {
    var $button = $(event.target);

    $('#knowledge-docs').find('input').eq(0).on('change', function(index, el){
        $("input#knowledge-submit").prop('disabled', false);
    })

    if ($button.is("input#knowledge-submit")) {

        // Disabled submit button to avoid multiple submission
        $("input#knowledge-submit").prop('disabled', true);

        //upload documenations/write ups
        var form_data = new FormData();
        var ins = document.getElementById('knowledge-files').files.length;
        if (ins == 0) {
            $('#msg').html('<span style="color:red">Select at least one file</span>');
            // Disabled submit button to avoid multiple submission
            $("input#knowledge-submit").prop('disabled', false);

            return;
        }

        $('.upload-knowledge').css({
            visibility: "hidden"
        })
            
        //get files upload
        form_data.append("files", document.getElementById('knowledge-files').files[0]);
        //get challenge data
        form_data.append("challenge", challenge_id_knowledge);
        $('input#knowledge-submit').prop('disabled', true);

        $('.loading-status').css({
            visibility: "visible"
        })

        $.ajax({
            url: '/api/v2/knowledge-well/' + challenge_id_knowledge,
            dataType: 'json',
            cache: false,
            contentType: false,
            processData: false,
            data: form_data,
            type: 'POST',
            success: function (counter_knowledge) {
                $('input#knowledge-files').remove();
                $('input#knowledge-submit').remove();
                $('#popup-knowledge').remove();
                $(".modal.upload").modal("show");
                $.each(counter_knowledge, function (key, data_knowledge) {
                    if (key !== 'message') {
                        // $('#msg').append(key + ' -> ' + data + '<br/>');
                    } else {
                        $('#msg').append(data_knowledge + '<br/>');
                        setTimeout(function () {
                            $('#msg').empty();
                        }, 800);
                    }
                })
                $('input#knowledge-submit').prop('disabled', false);

                $('.loading-status').css({
                    visibility: "hidden"
                });
            },
            error: function (counter_knowledge) {
                // $('#msg').html();
                alert(counter_knowledge.responseJSON.message);
                $('input#knowledge-submit').prop('disabled', false);
            }
        });
    }
});


$('.modal#challenge-window').on('click', function (event) {
    var $button = $(event.target);
    if ($button.is("i#delete-knowledge")) {
        var r = confirm("Are you sure you want to delete?");
        if (r) {
            $.ajax({
                url: '/api/v2/knowledge-well/' +  challenge_id_knowledge,
                dataType: 'json',
                cache: false,
                contentType: 'application/json; charset=utf-8',
                processData: false,
                data: JSON.stringify({
                    challenge:  challenge_id_knowledge
                }),
                type: 'delete',
                success: function (response_knowledge_delete) {
                    $.each(response_knowledge_delete, function (index, element_know_del) {
                        if (element_know_del.success) {
                            location.reload();
                        }
                    });
                },
                error: function (response_knowledge_delete) {
                    // $('#msg').html(response_knowledge_delete.message);
                    alert(response_knowledge_delete.responseJSON.message);
                }
            });
        }

    }
});


}



CTFd._internal.challenge.submit = function (preview) {
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val())
    var submission = CTFd.lib.$('#challenge-input').val()
    // Multiple Choice Submission
    if ($("input[type='radio']").is(':checked')) {
        var submission = $("input[type='radio']:checked").val();
    }
    var body = {
        'challenge_id': challenge_id,
        'submission': submission,
    }
    var params = {}
    if (preview) {
        params['preview'] = true
    }

    //attempts for Hint for team modes
    return $.ajax({
        url: '/api/v2/attempt',
        dataType: 'json',
        cache: false,
        contentType: 'application/json',
        processData: false,
        data: JSON.stringify(body),
        type: 'post',
        success: function (response) {

            if (response.data.status == 'correct') {
                setTimeout(function () {
                    window.location.reload();
                }, 5000);
            }
            if (response.status === 429) {
                // User was ratelimited but process response
                return response
            }

            if (response.status === 403) {
                // User is not logged in or CTF is paused.
                return response
            }
            return response
        },
        error: function (response) {
            //catch error here
        }
    });


    //end of upload 
    // return CTFd.api.post_challenge_attempt(params, body).then(function (response) {
    //     //update progress chart
    //     if (response.data.status == 'correct') {
    //         setTimeout(function(){
    //             window.location.reload();
    //          }, 5000);
    //     }
    //     if (response.status === 429) {
    //         // User was ratelimited but process response
    //         return response
    //     }
    //     if (response.status === 403) {
    //         // User is not logged in or CTF is paused.
    //         return response
    //     }
    //     return response
    // })
};