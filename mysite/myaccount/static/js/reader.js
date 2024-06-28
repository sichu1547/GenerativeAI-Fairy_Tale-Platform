$(document).ready(function(){
    $(".coniner, .coniner2, .coniner3").hover(
        function(){
            $(this).animate({ top: "-20px" });
        },
        function(){
            $(this).animate({ top: "0px" });
        }
    );
});

$(document).ready(function(){
    $(".coniner").hover(
        function() {
            $(this).find(".hidden-text").show(); // 마우스를 올렸을 때 텍스트를 표시합니다
        },
        function() {
            $(this).find(".hidden-text").hide(); // 마우스를 내렸을 때 텍스트를 숨깁니다
        }
    );
});
$(document).ready(function(){
    $(".coniner2").hover(
        function() {
            $(this).find(".hidden-text2").show(); // 마우스를 올렸을 때 텍스트를 표시합니다
        },
        function() {
            $(this).find(".hidden-text2").hide(); // 마우스를 내렸을 때 텍스트를 숨깁니다
        }
    );
});

$(document).ready(function(){
    $(".coniner3").hover(
        function() {
            $(this).find(".hidden-text3").show(); // 마우스를 올렸을 때 텍스트를 표시합니다
        },
        function() {
            $(this).find(".hidden-text3").hide(); // 마우스를 내렸을 때 텍스트를 숨깁니다
        }
    );
});
