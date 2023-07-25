$(document).ready(function () {
    console.log('JS is running!!!!')
    try{
        var showpopup = JSON.parse(document.getElementById('showpopup').textContent);
    }
    catch(err){
        console.log('Error!!!!')
    }
    console.log('Value of popup is......!!!!',showpopup);
    if (showpopup=='True'){
        console.log('Value of popup is',$('#myModal'));
        $('#myModal').show();
        $(document).click((e)=>{
            var target = $(e.target);
            if(!target.is('#myModal')){
                console.log('Clicked on modal!!')
            }else{
                console.log('Clicked outside modal!!')
                $('#myModal').hide();
            }
        });
    }

    this.closeRegisterationMoodal = function(){
        $('#myModal').hide();

    }
    
            // var visit = getCookie("fandeed");
            // setTimeout(function(){
            //     if (visit == null) {
            //         var expire = new Date();
            //         expire = new Date(expire.getTime() + 86400);
            //         debugger
            //         document.cookie = "cookie=fandeed; expires=" + expire.toUTCString()+'';
            //         $('#myModal').modal('show');
    
            //     }

            // },8000)
            //python manage.py collectstatic
    
});

function getCookie(c_name) {
    var c_value = document.cookie;
    var c_start = c_value.indexOf(" " + c_name + "=");
    if (c_start == -1) {
        c_start = c_value.indexOf(c_name + "=");
    }
    if (c_start == -1) {
        c_value = null;
    } else {
        c_start = c_value.indexOf("=", c_start) + 1;
        var c_end = c_value.indexOf(";", c_start);
        if (c_end == -1) {
            c_end = c_value.length;
        }
        c_value = unescape(c_value.substring(c_start, c_end));
    }
    return c_value;
}
