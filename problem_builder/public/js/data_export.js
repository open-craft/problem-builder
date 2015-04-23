function DataExportBlock(runtime, element) {
    "use strict";
    var $startExportBtn = $(".new-data-export", element);
    var $deleteExportBtn = $(".delete-data-export", element);
    $startExportBtn.on("click", function() {
        $.ajax({
            type: "POST",
            url: runtime.handlerUrl(element, 'start_export'),
            data: JSON.stringify({}),
            success: function(data) {
                console.log("Success");
                console.log(data);
            },
            dataType: "json",
        });
    });
    $deleteExportBtn.on("click", function() {
        $.ajax({
            type: "POST",
            url: runtime.handlerUrl(element, 'delete_export'),
            data: "{}",
            success: function(data) {
                $deleteExportBtn.prop('disabled', true);
            },
            dataType: "json",
        });
    });
}
