CTFd.plugin.run((_CTFd) => {
    const $ = _CTFd.lib.$
    const md = _CTFd.lib.markdown()
})
$(document).ready(function () {
    //get C3 category Challenge selector
    var c3_category = $.getJSON("/api/v2/challenge-category", function (data) {
        $.each(data, function (index, item) {
            $('select#c3_category').append($('<option>', { 
                value: item.id,
                text : item.category
            }));
        });
    });
    //get category challenge
    var Category_chals = $.getJSON("/api/v2/category-challenge", function (data) {
        $.each(data, function (index, item) {
            $('select#category').append($('<option>', { 
                value: item.category_name,
                text : item.category_name
            }));
        });
    });

    /**
     * Challenge Forms
     */
    $("#challenge_selector").on("click",function() {
        $("#create-chal-entry-div").show(); 
    });
    $('#challenge_selector').trigger('click');

});