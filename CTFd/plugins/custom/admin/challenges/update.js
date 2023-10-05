CTFd.plugin.run((_CTFd) => {
    const $ = _CTFd.lib.$
    const md = _CTFd.lib.markdown()
    $(document).ready(function () {
        //remove EasyMDEContainer and replace with ckeditor
        setTimeout(function () {
            $('div.EasyMDEContainer').remove();
        }, 100);
        //get category challenge
        var Category_chals = $.getJSON("/api/v2/category-challenge", function (data) {
            $.each(data, function (index, item) {
                $('select#category').append($('<option>', {
                    value: item.category_name,
                    text: item.category_name
                }));
            });
        });
        //get challenge attributes
        var chal = $.getJSON("/api/v1/challenges/" + CHALLENGE_ID, function (data) {
            $.each(data, function (index, item) {
                setTimeout(function () {
                    var selected = $('[name=category]').val(item.category);
                }, 100);
            });
        });

        //new c3 requirements functions
        function c3_requirements(category_id) {
            var submissions = [];
            var selected = [];
            var check = [];
            var Category_requirements = $.getJSON("/api/v2/c3_category/" + category_id, function (data, status, xhr) {
                $('.scrollbox').empty();
                $.each(data, function (index, item) {

                    if (item.id == CHALLENGE_ID) {
                        if (item.requirements) {
                            if(item.requirements['prerequisites']){
                                selected = item.requirements['prerequisites'];
                            }
                        }
                    }
                });
                $.each(data, function (index, item) {
                    if (item.id != CHALLENGE_ID) {
                        if (selected.includes(item.id.toString())) {

                            submissions += "<div  data-v-f3bc9efa=\"\" class=\"form-check\"><label  data-v-f3bc9efa=\"\" class=\"form-check-label cursor-pointer\"><input checked data-v-f3bc9efa=\"\" type=\"checkbox\" class=\"form-check-input\" value=\"" + item.id + "\">" + item.name + "</label></div>";

                        } else {

                            submissions += "<div  data-v-f3bc9efa=\"\" class=\"form-check\"><label  data-v-f3bc9efa=\"\" class=\"form-check-label cursor-pointer\"><input  data-v-f3bc9efa=\"\" type=\"checkbox\" class=\"form-check-input\" value=\"" + item.id + "\">" + item.name + "</label></div>";
                        }
                    }

                });
                $('.scrollbox').append("<span  data-v-f3bc9efa=\"\">" + submissions + "</span>");
                $('#requirements button').prop('disabled', false);
            });
        }


        var category_id = $('#c3_Category').val();
        //prerender requirements
        c3_requirements(category_id);
        //click requirements
        $('#c3_requirements').on('click', function(){
            c3_requirements(category_id);
        });
        //saved requirements
        
        $('#requirements button').on('click', function(){
            var req = [];
            $('#requirements input[type=checkbox]').each(function () {
                if(this.checked){
                    if($(this).val()){
                        req.push($(this).val())
                    }
                }
            });
            var data = '';
            if($('select[name=anonymize]').val() == 'true'){
                data = {"prerequisites": req, "anonymize": true} 
            }else{
                //hidden
                data = {"prerequisites": req }
            }
            $.ajax({
                url: "/api/v2/c3_category/" + category_id,
                dataType: 'json',
                cache: false,
                contentType: 'application/json; charset=utf-8',
                processData: false,
                data: JSON.stringify({'req': data,'challenge_id': CHALLENGE_ID }),
                type: 'post',
                success: function (response) {
                  //process response data
                  if(response == true){
                    location.reload();
                  }
                },
                error: function (response) {
                  //error here
                }
              });
            
        });



    });
})