function formatDate(date, format) {
    const map = {
        mm: date.getMonth() + 1,
        dd: date.getDate(),
        yy: date.getFullYear().toString().slice(-2),
        yyyy: date.getFullYear()
    }

    return format.replace(/mm|dd|yy|yyy/gi, matched => map[matched])
}

function delTableRow(e) {
    if (confirm("Delete ?")) {
        var x = document.getElementById("FFDMTable").deleteRow(e);
    } else {
        return false
    }
}

function validate(form) {
    return confirm('Do you really want to apply?');
}
