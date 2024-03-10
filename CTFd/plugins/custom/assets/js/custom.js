$(document).ready(function () {

  // Scoreboard filter for Beginner,Intermediate and advanced @ Admin
  $("#game_category").change(function () {
    $.ajax({
      url: '',
      type: $(this).attr('method'),
      data: $(this).serialize(),
      success: function (response) {
        $("tbody#standings").empty();
        $("tbody#user_standings").empty();
        var standings = [];
        var user_standings = [];
        //for team standings
        jQuery.each(response.standings, function (index, item) {
          var rank = index + 1;
          if (item.hidden) {
            var visibility = "<span class=\"badge badge-danger\">hidden</span>";
          } else {
            var visibility = "<span class=\"badge badge-success\">visible</span>";
          }
          standings += "<tr data-href=\"/admin/teams/" + item.account_id + "\"><td class=\"border-right text-center\" data-checkbox=\"\"><div class=\"form-check\"><input type=\"checkbox\" class=\"form-check-input\" value=\"" + item.account_id + "\" data-account-id=\"" + item.account_id + "\">&nbsp;</div></td><td class=\"text-center\" width=\"10%\">" + rank + "</td><td><a href=\"/admin/teams/" + item.account_id + "\">" + item.name + "</a></td><td>" + item.score + "</td><td>" + visibility + "</td></tr>";
        });
        //for users standings
        jQuery.each(response.users_standings, function (index, item) {
          var rank = index + 1;
          if (item.hidden) {
            var visibility = "<span class=\"badge badge-danger\">hidden</span>";
          } else {
            var visibility = "<span class=\"badge badge-success\">visible</span>";
          }
          user_standings += "<tr data-href=\"/admin/users/" + item.user_id + "\"><td class=\"border-right text-center\" data-checkbox=\"\"><div class=\"form-check\"><input type=\"checkbox\" class=\"form-check-input\" value=\"" + item.user_id + "\" data-user-id=\"" + item.user_id + "\">&nbsp;</div></td><td class=\"text-center\" width=\"10%\">" + rank + "</td><td><a href=\"/admin/users/" + item.user_id + "\">" + item.name + "</a></td><td>" + item.score + "</td><td>" + visibility + "</td></tr>";
        });
        $("tbody#standings").append(standings);
        $("tbody#user_standings").append(user_standings);
      }
    });
    return false;
  });

  //challenges list
  $("#game_category_challenges").change(function () {
    $.ajax({
      url: '',
      type: $(this).attr('method'),
      data: $(this).serialize(),
      success: function (response) {
        $("tbody#game_category_challenges").empty();
        var challenges = [];
        jQuery.each(response.challenges, function (index, item) {
          if (item.state == 'visible') {
            var visibility = "<span class=\"badge badge-success\">visible</span>";
          } else {
            var visibility = "<span class=\"badge badge-danger\">hidden</span>";
          }
          challenges += "<tr data-href=\"/admin/challenges/" + item.id + "\">" + item.id + "<td class=\"d-block border-right text-center\" data-checkbox=\"\"><div class=\"form-check\"><input type=\"checkbox\" class=\"form-check-input\" value=\"" + item.id + "\" data-challenge-id=\"" + item.id + "\">&nbsp;</div></td><td class=\"text-center\">" + item.id + "</td><td><a href=\"/admin/challenges/" + item.id + "\">" + item.name + "</a></td><td class=\"d-none d-md-table-cell d-lg-table-cell\">" + item.category + "</td><td class=\"d-none d-md-table-cell d-lg-table-cell text-center\">" + item.value + "</td><td class=\"d-none d-md-table-cell d-lg-table-cell text-center\">" + item.type + "</td><td class=\"d-none d-md-table-cell d-lg-table-cell text-center\">" + visibility + "</td></tr>";
        });
        $("tbody#game_category_challenges").append(challenges);
      }
    });
  });

  //submissions list
  $("#game_category_submissions").change(function () {
    $.date = function (orginaldate) {
      var date = new Date(orginaldate);
      var day = date.getDate();
      var month = date.getMonth() + 1;
      var year = date.getFullYear();
      var second = date.getSeconds();
      var minutes = date.getMinutes();
      if (day < 10) {
        day = "0" + day;
      }
      if (month < 10) {
        month = "0" + month;
      }
      var date = month + "/" + day + "/" + year + " " + minutes + ":" + second;
      return date;
    };

    $.ajax({
      url: '',
      type: $(this).attr('method'),
      data: $(this).serialize(),
      success: function (response) {
        $("tbody#game_category_submissions").empty();
        var submissions = [];
        jQuery.each(response.submissions, function (index, item) {

          submissions += "<tr><td class=\"border-right\" data-checkbox=\"\"><div class=\"form-check text-center\"><input type=\"checkbox\" class=\"form-check-input\" value=\"" + item.id + "\" data-submission-id=\"" + item.id + "\">&nbsp;</div></td><td class=\"text-center\" id=\"" + item.id + "\">" + item.id + "</td><td><a href=\"/admin/users/" + item.user_id + "\">" + item.username + "</a></td><td class=\"team\" id=\"" + item.team_id + "\"><a href=\"/admin/teams/" + item.team_id + "\">" + item.teamname + "</a></td><td class=\"chal\" id=\"" + item.challenge_id + "\"><a href=\"/admin/challenges/" + item.challenge_id + "\">" + item.challengename + "</a></td><td>" + item.type + "</td><td class=\"flag\" id=\"" + item.id + "\"><pre class=\"mb-0\">" + item.provided + "</pre></td><td class=\"text-center solve-time\"><span data-time=\"" + item.date + "\">" + $.date(item.date) + "</span></td></tr>";
        });
        $("tbody#game_category_submissions").append(submissions);

      }
    });
  });

  //c3 category update to select only one
  $('input[name="c3_category"]').on('change', function () {
    $('input[name="c3_category"]').not(this).prop('checked', false);
  });
  //c3 category update
  $("#c3-edit-button").click(function () {
    $('input[name="c3_category"]:checked').each(function () {
      if (this.value) {
        var chal = $.getJSON("/api/v2/challenge-category/" + this.value, function (data) {
          $.each(data, function (index, item) {
            $(".modal.c3_update .modal-body form").attr('action', '/api/v2/challenge-category/' + item.id);
            $(".modal.c3_update .modal-body input#challenge-c3-category-name").val(item.category);
            $(".modal.c3_update .modal-body textarea#challenge-c3-category-description").val(item.description);
            $(".modal.c3_update").modal("show");
          });
        });
      }
    });
  });

  //c3 category lockout update
  $("#lockout-edit-button").click(function () {
    $('input[name="c3_category"]:checked').each(function () {
      if (this.value) {
        var chal = $.getJSON("/api/v2/challenge-category/" + this.value, function (data) {
          $.each(data, function (index, item) {
            $(".modal.c3_lockoutupdate .modal-body form").attr('action', '/api/v2/challenge-category/' + item.id);
            $(".modal.c3_lockoutupdate .modal-body input#challenge-c3-category-name").val(item.category);
            $(".modal.c3_lockoutupdate .modal-body textarea#challenge-c3-category-description").val(item.description);
            $(".modal.c3_lockoutupdate").modal("show");
          });
        });
      }
    });
  });

  //delete c3 category
  $("#c3-delete-button").click(function () {
    $('input[name="c3_category"]:checked').each(function () {
      if (this.value) {
        $(".modal.c3_delete").modal("show");
      }
    });
  });
  //confirm deletion of c3 category
  $('.modal.c3_delete button#c3_delete').on('click', function (event) {
    var $button = $(event.target); // The clicked button
    var c3_id = null;
    if ($button) {
      $('input[name="c3_category"]:checked').each(function () {
        c3_id = this.value;
      });
      if (c3_id) {
        $.ajax({
          url: "/api/v2/challenge-category/" + c3_id,
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: this.value,
          type: 'delete',
          success: function (response) {
            //process response data
            $.each(response, function (key, data) {
              if (data.success) {
                location.reload();
              }
            });
          },
          error: function (response) {
            //error here
          }
        });
      }
    }
  });

  //challenge category update to select only one
  $('input[name="challenge_category"]').on('change', function () {
    $('input[name="challenge_category"]').not(this).prop('checked', false);
  });
  //challenge category update
  $("#category-challenge-edit-button").click(function () {
    $('input[name="challenge_category"]:checked').each(function () {
      if (this.value) {
        var chal = $.getJSON("/api/v2/category-challenge/" + this.value, function (data) {
          $.each(data, function (index, item) {
            $(".modal.cat_update .modal-body form").attr('action', '/api/v2/category-challenge/' + item.id);
            $(".modal.cat_update .modal-body input#c3_category_name").val(item.category_name);
            $(".modal.cat_update .modal-body textarea#category_description").val(item.description);
            $(".modal.cat_update").modal("show");
          });
        });
      }
    });
  });
  //challenge category delete
  $("#category-challenge-delete-button").click(function () {
    $('input[name="challenge_category"]:checked').each(function () {
      if (this.value) {
        $(".modal.cat_delete").modal("show");
      }
    });
  });
  //confirm deletion of category category
  $('.modal.cat_delete button#cat_delete').on('click', function (event) {
    var $button = $(event.target); // The clicked button
    var cat_id = null;
    if ($button) {
      $('input[name="challenge_category"]:checked').each(function () {
        cat_id = this.value;
      });
      if (cat_id) {
        $.ajax({
          url: "/api/v2/category-challenge/" + cat_id,
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: this.value,
          type: 'delete',
          success: function (response) {
            //process response data
            $.each(response, function (key, data) {
              if (data.success) {
                location.reload();
              }
            });
          },
          error: function (response) {
            //error here
          }
        });
      }
    }
  });

  //chronicles update to select only one
  $('input[name="writeups-id"]').on('change', function () {
    $('input[name="writeups-id"]').not(this).prop('checked', false);
  });
  //chronicles update to select only one | Individuals
  $('input[name="individual-writeups-id"]').on('change', function () {
    $('input[name="individual-writeups-id"]').not(this).prop('checked', false);
  });
  //chronicles graded  points update
  $("#writeups-edit-button").click(function () {
    $('input[name="writeups-id"]:checked').each(function () {
      if (this.value) {
        $.getJSON("/api/v2/chronicles/" + this.value, function (multiplayers_data) {
          $.each(multiplayers_data, function (index, multiplayers_item) {
            $(".modal.writeups .modal-body form").attr('action', '/api/v2/chronicles/' + multiplayers_item.id);
            $(".modal.writeups .modal-body select#writeups-points").val(multiplayers_item.points);
            $(".modal.writeups").modal("show");
          });
        });
      }
    });
  });
  //chronicles graded  points update | Individuals
  $("#individual-edit-button").click(function () {
    $('input[name="individual-writeups-id"]:checked').each(function () {
      if (this.value) {
        $.getJSON("/api/v2/chronicles/" + this.value, function (individual_data) {
          $.each(individual_data, function (index, individual_item) {
            $(".modal.individuals-writeups .modal-body form").attr('action', '/api/v2/chronicles/' + individual_item.id);
            $(".modal.individuals-writeups .modal-body select#individuals-writeups-points").val(individual_item.points);
            $(".modal.individuals-writeups").modal("show");
          });
        });
      }
    });
  });

  $(document).scroll(function () {
    if ($(window).scrollTop() === 0) {
      $('#backtop').removeClass("active");
    } else {
      $('#backtop').addClass("active");
    }
  });

  //countermesure update to select only one
  $('input[name="countermeasure-id"]').on('change', function () {
    $('input[name="countermeasure-id"]').not(this).prop('checked', false);
  });
  //countermeasure graded  points update
  $("#countermeasure-edit-button").click(function () {
    $('input[name="countermeasure-id"]:checked').each(function () {
      if (this.value) {
        $.getJSON("/api/v2/countermeasure/update/" + this.value, function (multi_data) {
          $.each(multi_data, function (index, multi_item) {
            $(".modal.countermeasure .modal-body form").attr('action', '/api/v2/countermeasure/update/' + multi_item.id);
            $(".modal.countermeasure .modal-body select#counter-points").val(multi_item.points);
            $(".modal.countermeasure").modal("show");
          });
        });
      }
    });
  });

  //countermeasure individual update to select only one
  $('input[name="individualCountermeasure-id"]').on('change', function () {
    $('input[name="individualCountermeasure-id"]').not(this).prop('checked', false);
  });

  //individual countermeasure graded  points update
  $("#individualCountermeasure-edit-button").click(function () {
    $('input[name="individualCountermeasure-id"]:checked').each(function () {
      if (this.value) {
        $.getJSON("/api/v2/countermeasure/update/" + this.value, function (individual_counterdata) {
          $.each(individual_counterdata, function (index, counterInvidualitem) {
            $(".modal.individualCountermeasure .modal-body form").attr('action', '/api/v2/countermeasure/update/' + counterInvidualitem.id);
            $(".modal.individualCountermeasure .modal-body select#counter-points").val(counterInvidualitem.points);
            $(".modal.individualCountermeasure").modal("show");
          });
        });
      }
    });
  });

  //published | unpublished countermeasure
  $('input[name="publish_id"]').on('change', function () {
    $('input[name="publish_id"]').not(this).prop('checked', false);
  });

  //published | unpublished countermeasure
  $("#countermeasure-publish-button").click(function () {
    $('input[name="publish_id"]:checked').each(function () {
      if (this.value == 'document_publish') {
        $(".modal.countermeasure_publish").modal("show");
        var published = $.getJSON("/api/v2/docs", function (data) {
          $.each(data, function (index, item) {
            counter = 0
            if (item.countermeasure == true) {
              counter = 1
            }
            $(".modal.countermeasure_publish .modal-body form#counter-publish").attr('action', '/api/v2/docs/document_publish');
            $(".modal.countermeasure_publish .modal-body select#counter-publish").val(counter);
          });
        });
      }
      if (this.value == 'view_rating') {
        $(".modal.countermeasure_publish").modal("show");
        var published2 = $.getJSON("/api/v2/docs", function (data_chronicles) {
          $.each(data_chronicles, function (index, item) {
            chronicles = 0
            if (item.chronicles == true) {
              chronicles = 1
            }
            $(".modal.countermeasure_publish .modal-body form#counter-publish").attr('action', '/api/v2/docs/view_rating');
            $(".modal.countermeasure_publish .modal-body select#counter-publish").val(chronicles);
          });
        });
      }
    });
  });


  var chal = $.getJSON("/api/v2/status", function (data) {
    $.each(data, function (index, item) {

      //unlock for warrior
      if (item['apprentice']) {
        $.each(item['apprentice'], function (index, apprentice) {
          if (apprentice.progress >= item['warrior_lockout']) {
            var id = $('div#warrior #unlock').attr('data-value');
            var html = "<span><button class=\"btn btn-sm btn-outline-secondary\" name=\"c3_category\" value=\"" + id + "\">Capture<i class=\"fas fa-chess-rook\"></i></button></span>";
            $('div#warrior #unlock').empty();
            $('div#warrior #unlock').append(html);
          }
        });
      }

      //unlock for conqueror
      if (item['warrior']) {
        $.each(item['warrior'], function (index, warrior) {
          if (warrior.progress >= item['conqueror_lockout']) {
            var id = $('div#conqueror #unlock').attr('data-value');
            var html = "<span><button class=\"btn btn-sm btn-outline-secondary\" name=\"c3_category\" value=\"" + id + "\">Capture<i class=\"fas fa-crown\"></i></button></span>";
            $('div#conqueror #unlock').empty();
            $('div#conqueror #unlock').append(html);
          }
        });
      }

    });
  });

  //User list board | Admin
  selected_user = $("select#game_category_challenges_user").attr('value');
  if (selected_user) {
    $("#game_category_challenges_user").val(selected_user).change();
  }

  //Teams list board | Admin
  selected_team = $("select#game_category_challenges_team").attr('value');
  if (selected_team) {
    $("#game_category_challenges_team").val(selected_team).change();
  }

  //add Blog| Article in Setting
  $("#blog-add-button").click(function () {
    window.location.href = '/article/add';
  });

  //Blog update to select only one
  $('input[name="blog-id"]').on('change', function () {
    $('input[name="blog-id"]').not(this).prop('checked', false);
  });

  //Edit Blog| Article in Setting
  $("#blog-edit-button").click(function () {
    $('input[name="blog-id"]:checked').each(function () {
      if (this.value) {
        window.location.href = '/article/edit/' + this.value;
      }
    });
  });

  //Delete Blog| Article in Setting
  $("#blog-delete-button").click(function () {
    $('input[name="blog-id"]:checked').each(function () {
      if (this.value) {
        $(".modal.blog_delete").modal("show");
      }
    });
  });
  //confirm deletion of c3 category
  $('.modal.blog_delete button#blog_delete').on('click', function (event) {
    var $button = $(event.target); // The clicked button
    var blog_id = null;
    if ($button) {
      $('input[name="blog-id"]:checked').each(function () {
        blog_id = this.value;
      });
      if (blog_id) {
        $.ajax({
          url: "/api/v2/article/delete/" + blog_id,
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: this.value,
          type: 'delete',
          success: function (response) {
            //process response data
            $.each(response, function (key, data) {
              if (data.success) {
                location.reload();
              }
            });
          },
          error: function (response) {
            //error here
          }
        });
      }
    }
  });

  //registration config
  $("#branch-service").change(function () {
    if (this.value) {
      $('#unit-field').val(this.value);
      $.getJSON("/api/v2/maj_unit/" + this.value, function (data) {
        option = '<option value="">Select Major Unit</option>';
        if (data != "") {
          $("#unit-service").empty();
          $.each(data, function (key, item) {
            option += '<option value=' + item.key + '>' + item.name + '</option>';
          });
          $("#unit-service").append(option);
          $('select#unit-service').prop('required', true);
          $("#unit").css("display", "");
        } else {
          $("#unit").css("display", "none");
          $('select#unit-service').prop('required', false);
          $("#sub-unit").css("display", "none");
          $('select#sub-unit-service').prop('required', false);
        }
      });
    } else {
      $("#unit").css("display", "none");
      $('select#unit-service').prop('required', false);
      $("#sub-unit").css("display", "none");
      $('select#sub-unit-service').prop('required', false);
      $('#unit-field').val("");
    }
  });

  //mother unit
  $("#unit-service").change(function () {
    if (this.value) {
      branch = $("#branch-service").val();
      $('#unit-field').val(this.value + ', ' + branch);
      $.getJSON("/api/v2/sub_unit/" + this.value, function (sub_data) {
        sub_option = '<option value="">Select Battalion/Office</option>';
        if (sub_data != "") {
          $("#sub-unit-service").empty();
          $.each(sub_data, function (key, sub_item) {
            sub_option += '<option value=' + sub_item.key + '>' + sub_item.name + '</option>';
          });
          $("#sub-unit-service").append(sub_option);
          $('select#sub-unit-service').prop('required', true);
          $("#sub-unit").css("display", "");
        } else {
          $("#sub-unit").css("display", "none");
          $('select#sub-unit-service').prop('required', false);
        }
      });
    } else {
      $("#sub-unit").css("display", "none");
      $('select#sub-unit-service').prop('required', false);
      branch = $("#branch-service").val();
      $('#unit-field').val(branch);
    }
  });

  //Unit
  $("#sub-unit-service").change(function () {
    if (this.value) {
      branch = $("#branch-service").val();
      major_unit = $("#unit-service").val();
      $('#unit-field').val(this.value + ', ' + major_unit + ', ' + branch);
    } else {
      branch = $("#branch-service").val();
      major_unit = $("#unit-service").val();
      $('#unit-field').val(major_unit + ', ' + branch);
    }

  });

  //register
  $(window).on('load', function () {
    $('.modal.c3_register').modal('show');
  });

  //individual chronicles graded  points update for direcorate
  $("button.individualChronicles-directorate-edit-button").click(function () {
    var id = $(this).data('id');
    // var url = $(this).data('url');
    var directorate_score = ''
    $(".modal.individualChronicles-directorate .modal-body table tbody#chronicle-rater-points").empty();
    if (id) {
      $.getJSON(`/api/v2/directorate/${id}`, function (directorate_chronicles_data) {
        if (directorate_chronicles_data.rater) {
          $.each(directorate_chronicles_data.rater, function (key, rater_item) {
            // directorate_score += `<tr><td>${ rater_item.directorate_name}</td><td>${ rater_item.rater_points}</td><td>${ rater_item.date}</td></tr>`;
            //version3
            if(rater_item.admin){
              directorate_score += `<tr>
                                    <td>${rater_item.directorate_name}</td>
                                    <td>${rater_item.grade}</td>
                                    <td><small><em>Know:${rater_item.rater_know} pts<br>Do:${rater_item.rater_do} pts<br>Learn:${rater_item.rater_learn} pts<em><small></td>
                                    <td>${rater_item.date}</td>
                                    </tr>
                                  `;

            }else{

              directorate_score += `<tr>
              <td>${rater_item.directorate_name}</td>
              <td>${rater_item.grade}</td>
              <td><small><em>Know:${rater_item.rater_know} pts<br>Do:${rater_item.rater_do} pts<br>Learn:${rater_item.rater_learn} pts<em><small></td>
            </tr>
            `;


            }
              // directorate_score += `<tr>
              //                       <td>Knowledge-Well</td>
              //                       <td>${rater_item.rater_know}</td>
              //                       <td>${rater_item.directorate_name}/${rater_item.date}</td>
              //                     </tr>
              //                     <tr>
              //                       <td>Chronicles</td>
              //                       <td>${rater_item.rater_do}</td>
              //                       <td>${rater_item.directorate_name}/${rater_item.date}</td>
              //                     </tr>
              //                     <tr>
              //                       <td>Countermeasures</td>
              //                       <td>${rater_item.rater_learn}</td>
              //                       <td>${rater_item.directorate_name}/${rater_item.date}</td>
              //                     </tr>
              //                     `;
            //}
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
        $(".modal.individualChronicles-directorate .modal-body form").attr('action', `/api/v2/directorate/${id}`);
        $(".modal.individualChronicles-directorate .modal-body table tbody#chronicle-rater-points").append(directorate_score);
        $(".modal.individualChronicles-directorate").modal("show");
      });
    }
  });

  //individual countermeasure graded  points update for direcorate
  // $("button.individualCountermeasure-directorate-edit-button").click(function () {
  //   var id = $(this).data('id');
  //   // var url = $(this).data('url');
  //   var directorate_score = ''
  //   $(".modal.individualCountermeasure-directorate .modal-body table tbody#chronicle-rater-points").empty();
  //   if (id) {
  //     $.getJSON(`/api/v2/countermeasures/directorate/${id}`, function (directorate_chronicles_data) {
  //       if (directorate_chronicles_data.rater) {
  //         $.each(directorate_chronicles_data.rater, function (key, rater_item) {
  //           directorate_score += `<tr><td>${ rater_item.directorate_name}</td><td>${ rater_item.rater_points}</td><td>${ rater_item.date}</td></tr>`;
  //         });
  //       }
  //       //remove rdated judge eX
  //       $(".modal.individualCountermeasure-directorate .modal-body select#counter-points").css({
  //         visibility: "visible"
  //       });
  //       $(".modal.individualCountermeasure-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({
  //         visibility: "visible",
  //         "margin-bottom": "0rem"
  //       });
  //       if (directorate_chronicles_data.rated == true) {
  //         // $(".modal.individualCountermeasure-directorate .modal-body select#counter-points").css({visibility: "hidden"});
  //         // $(".modal.individualCountermeasure-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({visibility: "hidden", "margin-bottom" : "-10rem"});
  //       }
  //       $(".modal.individualCountermeasure-directorate .modal-body form").attr('action', `/api/v2/countermeasures/directorate/${id}`);
  //       $(".modal.individualCountermeasure-directorate .modal-body table tbody#chronicle-rater-points").append(directorate_score);
  //       $(".modal.individualCountermeasure-directorate").modal("show");
  //     });
  //   }
  // });

  //individual knowledge-well graded  points update for direcorate
  // $("button.individualKnowledge-directorate-edit-button").click(function () {
  //   var id = $(this).data('id');
  //   // var url = $(this).data('url');
  //   var directorate_score = ''
  //   $(".modal.individualKnowledge-directorate .modal-body table tbody#knowledge-rater-points").empty();
  //   if (id) {
  //     $.getJSON(`/api/v2/knowledge-well/directorate/${id}`, function (directorate_knowledge_data) {
  //       if (directorate_knowledge_data.rater) {
  //         $.each(directorate_knowledge_data.rater, function (key, rater_item) {
  //           directorate_score += `<tr><td>${ rater_item.directorate_name}</td><td>${ rater_item.rater_points}</td><td>${ rater_item.date}</td></tr>`;
  //         });
  //       }
  //       //remove rdated judge eX
  //       $(".modal.individualKnowledge-directorate .modal-body select#counter-points").css({
  //         visibility: "visible"
  //       });
  //       $(".modal.individualKnowledge-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({
  //         visibility: "visible",
  //         "margin-bottom": "0rem"
  //       });
  //       if (directorate_knowledge_data.rated == true) {
  //         // $(".modal.individualKnowledge-directorate .modal-body select#counter-points").css({visibility: "hidden"});
  //         // $(".modal.individualKnowledge-directorate .modal-body button.btn.btn-md.btn-primary.float-right").css({visibility: "hidden", "margin-bottom" : "-10rem"});
  //       }
  //       $(".modal.individualKnowledge-directorate .modal-body form").attr('action', `/api/v2/knowledge-well/directorate/${id}`);
  //       $(".modal.individualKnowledge-directorate .modal-body table tbody#knowledge-rater-points").append(directorate_score);
  //       $(".modal.individualKnowledge-directorate").modal("show");
  //     });
  //   }
  // });

  //directorate user statisctics
  $('a.multiplayer .fa-chart-pie').click(function () {
    var team_ids = []
    var team_id = $(this).data('team_id');
    team_ids.push(team_id);
    $(".modal.individualCountermeasure-directorate").modal("show");
  });

  //directorate user statisctics | Individuals
  $('a.individual .fa-chart-pie').click(function () {
    var user_ids = []
    var user_id = $(this).data('user_id');
    user_ids.push(user_id);
    $(".modal.individualCountermeasure-directorate-users").modal("show");

  });


  $('#ctk-individual').click(function () {
    //loading
    $(".modal.bd-example-modal-lg").modal("show");
    setTimeout(function () {
      $(".modal.bd-example-modal-lg").modal("hide");
    }, 1000);
  });

  $('#ctk-multiplayer').click(function () {
    //loading
    $(".modal.bd-example-modal-lg").modal("show");
    setTimeout(function () {
      $(".modal.bd-example-modal-lg").modal("hide");
    }, 1000);
  });


  /////////////////////////////////////////////////
  ////// CHRONICLES //////////////////////////////
  ///////////////////////////////////////////////
  //Delete chronicles under admin page
  $("#writeups-delete-button").click(function () {
    $('input[name="writeups-id"]:checked').each(function () {
      if (this.value) {
        $(".modal.writeups_delete").modal("show");
      }
    });
  });

  //confirm deletion of chronicles in multiplayers
  $('.modal.writeups_delete button#writeup_delete').on('click', function (event) {
    var $button = $(event.target); // The clicked button
    var writeup_id = null;
    if ($button) {
      $('input[name="writeups-id"]:checked').each(function () {
        writeup_id = this.value;
      });

      if (writeup_id) {
        $.ajax({
          url: "/api/v2/chronicles/" + writeup_id,
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: writeup_id,
          type: 'delete',
          success: function (response) {
            //process response data
            alert(response.message);
            location.reload();
          },
          error: function (response) {
            //error here
          }
        });
      }
    }
  });

  //Delete chronicles under admin page | individuals
  $("#individual-delete-button").click(function () {
    $('input[name="individual-writeups-id"]:checked').each(function () {
      if (this.value) {
        $(".modal.writeups_delete").modal("show");
      }
    });
  });

  //confirm deletion of chronicles in multiplayers | Individuals
  $('.modal.writeups_delete button#writeup_delete').on('click', function (event) {
    var $button = $(event.target); // The clicked button
    var writeup_id = null;
    if ($button) {
      $('input[name="individual-writeups-id"]:checked').each(function () {
        writeup_id = this.value;
      });

      if (writeup_id) {
        $.ajax({
          url: "/api/v2/chronicles/" + writeup_id,
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: writeup_id,
          type: 'delete',
          success: function (response) {
            //process response data
            alert(response.message);
            location.reload();
          },
          error: function (response) {
            //error here
          }
        });
      }
    }
  });
  /////////////////////////////////////////////////
  ////// COUNTERMEASURE //////////////////////////////
  ///////////////////////////////////////////////
  //Delete countermeasure under admin page | multiplayer
  $("#countermeasure-delete-button").click(function () {
    $('input[name="countermeasure-id"]:checked').each(function () {
      if (this.value) {
        $(".modal.countermeasure_delete").modal("show");
      }
    });
  });


  //confirm deletion of countermeasure in multiplayers | Individuals
  $('.modal.countermeasure_delete button#counter_delete').on('click', function (event) {
    var $button = $(event.target); // The clicked button
    var cntrmsrs_id = null;
    if ($button) {
      $('input[name="countermeasure-id"]:checked').each(function () {
        cntrmsrs_id = this.value;
      });

      if (cntrmsrs_id) {
        $.ajax({
          url: "/api/v2/countermeasure/update/" + cntrmsrs_id,
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: cntrmsrs_id,
          type: 'delete',
          success: function (response) {
            //process response data
            alert(response.message);
            location.reload();
          },
          error: function (response) {
            //error here
          }
        });
      }
    }
  });

  //Delete countermeasure under admin page | Individuals
  $("#individualCountermeasure-delete-button").click(function () {
    $('input[name="individualCountermeasure-id"]:checked').each(function () {
      if (this.value) {
        $(".modal.countermeasure_delete").modal("show");
      }
    });
  });

  //confirm deletion of countermeasure in Individuals
  $('.modal.countermeasure_delete button#counter_delete').on('click', function (event) {
    var $button = $(event.target); // The clicked button
    var cntrmsrs_id = null;
    if ($button) {
      $('input[name="individualCountermeasure-id"]:checked').each(function () {
        cntrmsrs_id = this.value;
      });

      if (cntrmsrs_id) {
        $.ajax({
          url: "/api/v2/countermeasure/update/" + cntrmsrs_id,
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: cntrmsrs_id,
          type: 'delete',
          success: function (response) {
            //process response data
            alert(response.message);
            location.reload();
          },
          error: function (response) {
            //error here
          }
        });
      }
    }
  });

  /////////////////////////////////////////////////
  ////// KNOWLEDGE WELL //////////////////////////////
  ///////////////////////////////////////////////
  //knowledge well update to select only one
  $('input[name="knowledge-id"]').on('change', function () {
    $('input[name="knowledge-id"]').not(this).prop('checked', false);
  });

  //Delete knowledge Well under admin page | Multiplayers
  $("#knowledge-delete-button").click(function () {
    $('input[name="knowledge-id"]:checked').each(function () {
      if (this.value) {
        $(".modal.knowledge_delete").modal("show");
      }
    });
  });

  //confirm deletion of knowledge well
  $('.modal.knowledge_delete button#know_del').on('click', function (event) {
    var $button = $(event.target); // The clicked button
    var know_id = null;
    if ($button) {
      $('input[name="knowledge-id"]:checked').each(function () {
        know_id = this.value;
      });
      if (know_id) {
        $.ajax({
          url: "/api/v2/knowledgeWell/" + know_id,
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: know_id,
          type: 'delete',
          success: function (response) {
            //process response data
            alert(response.message);
            location.reload();
          },
          error: function (response) {
            //error here
          }
        });
      }
    }
  });

  //Delete knowledge Well under admin page | Individual
  $("#know-individual-delete-button").click(function () {
    $('input[name="individual-know-id"]:checked').each(function () {
      if (this.value) {
        $(".modal.knowledge_delete").modal("show");
      }
    });
  });

  //confirm deletion of knowledge well
  $('.modal.knowledge_delete button#know_del').on('click', function (event) {
    var $button = $(event.target); // The clicked button
    var know_id = null;
    if ($button) {
      $('input[name="individual-know-id"]:checked').each(function () {
        know_id = this.value;
      });
      if (know_id) {
        $.ajax({
          url: "/api/v2/knowledgeWell/" + know_id,
          dataType: 'json',
          cache: false,
          contentType: false,
          processData: false,
          data: know_id,
          type: 'delete',
          success: function (response) {
            //process response data
            alert(response.message);
            location.reload();
          },
          error: function (response) {
            //error here
          }
        });
      }
    }
  });

  //Calculate Knowledge Well Grades | Multiplayers
  $("#knowledge-calculate-button").click(function () {
    $(".modal.knowledge_calculate_multi").modal("show");
    setTimeout(function () {
      $.ajax({
        url: "/api/v2/knowledgeWell-Grade/multiplayers",
        dataType: 'json',
        cache: false,
        contentType: false,
        processData: false,
        data: [],
        type: 'post',
        success: function (response) {
          //process response data
          $(".modal.knowledge_calculate_multi").modal("hide");
          alert(response.message);
        },
        error: function (response) {
          //error here
        }
      });
    }, 1000);
  });

  //Calculate Chronicles Grades | Multiplayers
  $("#chronicles-calculate-button").click(function () {
    $(".modal.chronicles_calculate_multi").modal("show");
    setTimeout(function () {
      $.ajax({
        url: "/api/v2/documentation/multiplayers",
        dataType: 'json',
        cache: false,
        contentType: false,
        processData: false,
        data: [],
        type: 'post',
        success: function (response) {
          //process response data
          $(".modal.chronicles_calculate_multi").modal("hide");
          alert(response.message);
        },
        error: function (response) {
          //error here
        }
      });
    }, 1000);
  });

  //Calculate Countermeasures Grades | Multiplayers
  $("#document-individual-calculate-button").click(function () {
    $(".modal.chronicles_calculate_multi").modal("show");
    setTimeout(function () {
      $.ajax({
        url: "/api/v2/documentation/individual",
        dataType: 'json',
        cache: false,
        contentType: false,
        processData: false,
        data: [],
        type: 'post',
        success: function (response) {
          //process response data
          $(".modal.chronicles_calculate_multi").modal("hide");
          alert(response.message);
        },
        error: function (response) {
          //error here
        }
      });
    }, 1000);
  });


  //activate conqueror red teaming
  $("#conqueror-activate-button").click(function () {
    $(".modal.conqueror_activate").modal("show");
    var published2 = $.getJSON("/api/v2/redteaming", function (data_chronicles) {
      console.log(data_chronicles);
      $.each(data_chronicles, function (index, item) {
        chronicles = 0
        if (item.chronicles == true) {
          chronicles = 1
        }
        $(".modal.conqueror_activate .modal-body select#conqueror-activate").val(chronicles);
      });
    });
  });
  //Delete knowledge Well under admin page | Individual
  $("#team-info-edit-modal").click(function () {
    // $('input[name="individual-know-id"]:checked').each(function () {
    //   if (this.value) {
    //     $(".modal.knowledge_delete").modal("show");
    //   }
    // });
  });

  //update team logo
  //challenge category update to select only one
  $('input[name="team_logo_checkbox"]').on('change', function () {
    $('input[name="team_logo_checkbox"]').not(this).prop('checked', false);
  });
  $("#team-logo-edit-button").click(function () {
    $('input[name="team_logo_checkbox"]:checked').each(function () {
      $(".modal.team_logo_update .modal-body form").attr('action', '/api/v2/logo/' + this.value);
      $(".modal.team_logo_update").modal("show");
      if (this.value) {
        // var chal = $.getJSON("/api/v2/category-challenge/" + this.value, function (data) {
        //   $.each(data, function (index, item) {
        //     $(".modal.team_logo_update .modal-body form").attr('action', '/api/v2/logo/' + item.id);
        //     $(".modal.team_logo_update").modal("show");
        //   });
        // });
      }
    });
  });

});