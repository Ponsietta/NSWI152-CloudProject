$(document).ready(function () {

    $('#convertForm').on('submit', function (event) {
        event.preventDefault();

        var form = $('#convertForm')[0];

		// momentarily disable the submit button
        $("#submitBtn").prop("disabled", true);
		
		//clear previous notifications
		toastr.clear();

        $.ajax({
            type: "POST",
            enctype: 'multipart/form-data',
            url: "/convert",
            data: new FormData(form),
            processData: false,
            contentType: false,
            success: function (result) {     
				if (result.status == "success") {
					toastr.success(result.msg, '' , { timeOut: 0 }).css("width","500px");
					form.reset();
                } else {
					toastr.error(result.msg, '' , { timeOut: 0 }).css("width","500px");
                }				
            },
            error: function () {
				toastr.error('An error occurred.', '' , { timeOut: 0 }).css("width","500px");
            },
			complete: function(data) {
				$("#submitBtn").prop("disabled", false);
			}
        });

    });

});