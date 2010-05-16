$(function(){
    $("form").live("focus",
      function() {
        this.startValue = $(this).find("input[name='hours']").val();
      });
    $("form").submit(
      function() {
        var inst = this;
        $(inst).addClass("submitting");
        var xsrf = $(inst).find("input[name='_xsrf']").val();
        var date = $(inst).find("input[name='date']").val();
        var hours = $(inst).find("input[name='hours']").val();

        $.ajax({
          type: 'POST',
          url: "/",
          data: {'_xsrf': xsrf, 'date':date, 'hours':hours},
          success: function(res) {
            $(inst).find("input[name='hours']").val(res);
            inst.startValue = res;
            inst.className = '';
          }
        });

        return false;
      });
    $("form").live("blur",
      function(){
        var currentValue = $(this).find("input[name='hours']").val();
        if (this.startValue != currentValue) {
          $(this).addClass("changed");
        }
      });
  });
