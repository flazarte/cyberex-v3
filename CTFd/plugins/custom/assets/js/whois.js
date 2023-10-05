$(document).ready(function () {
    $.getJSON(`/api/v2/who_login`, function (is_login) {
        //directorate user
        if(is_login.data.directorate){
            var dashboard = `
            <span class="d-block" data-toggle="tooltip" data-placement="bottom" title="Dashboard">
                <i class="fas fa-users d-none d-md-block d-lg-none"></i>
            </span>
             <span class="d-sm-block d-md-none d-lg-block">
                <i class="fas fa-users pr-1"></i> Dashboard
            </span>
            `;
            $("#ctk_is_scoreboard").remove();
            $("#ctk_is_team").empty();
            $("#ctk_is_team").attr("href", "/admin/directorate");
            $("#ctk_is_team").append(dashboard);

        }
        //individual user
        if(is_login.data.individual){
            $("#ctk_is_team").remove();

        }
        //multiplayer
        if(is_login.data.multiplayer){

        }
       
    });
});