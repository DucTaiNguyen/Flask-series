// function recipeDetails(recipeId) { 
//     $.ajax({
//         type: 'GET',
//         url: '/recipe/'+recipeId,
//         success: function (data) {
//             window.location = "/recipe/"+recipeId;
//         },
//         fail: function (data) {
//            window.location = "/error";
//         }
//     });
// }

function recipeDetails(recipeId){
    $.ajax({
        type:'GET',
        url:'/recipe/'+recipeId,
        success:function(data){
            window.location="/recipe/"+recipeId;
        },
        fail: function(){
            window.location="/error";
        }
    })
};

function getPdf() {
    window.print()
}