function addEntry(e) {
    Typeinputbox = document.createElement("input");
    Typeinputbox.setAttribute("type", "text");
    Typeinputbox.setAttribute("size", "3");
    Typeinputbox.setAttribute("name", "AssetType");
    Typeinputbox.setAttribute("value", "");
    Typeinputbox.setAttribute("class", "input");
    IDinputbox = document.createElement("input");
    IDinputbox.setAttribute("type", "text");
    IDinputbox.setAttribute("size", "10");
    IDinputbox.setAttribute("name", "AssetID");
    IDinputbox.setAttribute("value", "");
    IDinputbox.setAttribute("class", "input");
    Nameinputbox = document.createElement("input");
    Nameinputbox.setAttribute("type", "text");
    Nameinputbox.setAttribute("size", "14");
    Nameinputbox.setAttribute("name", "AssetName");
    Nameinputbox.setAttribute("value", "");
    Nameinputbox.setAttribute("class", "input");
    Bankinputbox = document.createElement("input");
    Bankinputbox.setAttribute("type", "text");
    Bankinputbox.setAttribute("size", "12");
    Bankinputbox.setAttribute("name", "Ticker");
    Bankinputbox.setAttribute("value", "");
    Bankinputbox.setAttribute("class", "input");
    Fnetinputbox = document.createElement("input");
    Fnetinputbox.setAttribute("type", "text");
    Fnetinputbox.setAttribute("size", "12");
    Fnetinputbox.setAttribute("name", "NetRef1");
    Fnetinputbox.setAttribute("value", "");
    Fnetinputbox.setAttribute("class", "input");
    ARDinputbox = document.createElement("input");
    ARDinputbox.setAttribute("type", "text");
    ARDinputbox.setAttribute("size", "12");
    ARDinputbox.setAttribute("name", "NetRef2");
    ARDinputbox.setAttribute("value", "");
    ARDinputbox.setAttribute("class", "input");
    DELbutton = document.createElement("button");
    DELbutton.innerHTML = "Delete";
    DELbutton.setAttribute("type", "button");
    var btn_str1 = "del_line" + e.toString();
    DELbutton.setAttribute("id", btn_str1);
    DELbutton.setAttribute("class", "del_button");
    var btn_str2 = "return delEntry(" + e.toString() + ")";
    DELbutton.setAttribute("onclick", btn_str2);
    var x = document.getElementById("AssetsTable").insertRow(e);
    var type_c = x.insertCell(0);
    var id_c = x.insertCell(1);
    var name_c = x.insertCell(2);
    var bank_c = x.insertCell(3);
    var fnet_c = x.insertCell(4);
    var ard_c = x.insertCell(5);
    var del_c = x.insertCell(6);
    type_c.appendChild(Typeinputbox);
    id_c.appendChild(IDinputbox);
    name_c.appendChild(Nameinputbox);
    bank_c.appendChild(Bankinputbox);
    fnet_c.appendChild(Fnetinputbox);
    ard_c.appendChild(ARDinputbox);
    del_c.appendChild(DELbutton);
}

function delEntry(e) {
    if (confirm("Delete ?")) {
        var x = document.getElementById("AssetsTable").deleteRow(e);
    } else  {
        return false
    }
}

function addVL(e) {
    Planinputbox = document.createElement("input");
    Planinputbox.setAttribute("type", "text");
    Planinputbox.setAttribute("size", "2");
    Planinputbox.setAttribute("name", "PlanID");
    Planinputbox.setAttribute("value", e);
    Planinputbox.setAttribute("class", "input");
    Planinputbox.setAttribute("readonly", true);
    Bankinputbox = document.createElement("input");
    Bankinputbox.setAttribute("type", "text");
    Bankinputbox.setAttribute("size", "8");
    Bankinputbox.setAttribute("name", "Bank");
    Bankinputbox.setAttribute("value", "");
    Bankinputbox.setAttribute("class", "input");
    Accinputbox = document.createElement("input");
    Accinputbox.setAttribute("type", "text");
    Accinputbox.setAttribute("size", "10");
    Accinputbox.setAttribute("name", "AccountNr");
    Accinputbox.setAttribute("value", "");
    Accinputbox.setAttribute("class", "input");
    IDinputbox = document.createElement("input");
    IDinputbox.setAttribute("type", "text");
    IDinputbox.setAttribute("size", "10");
    IDinputbox.setAttribute("name", "AssetID");
    IDinputbox.setAttribute("value", "");
    IDinputbox.setAttribute("class", "input");
    Startinputbox = document.createElement("input");
    Startinputbox.setAttribute("type", "date");
    Startinputbox.setAttribute("size", "4");
    Startinputbox.setAttribute("name", "StartDate");
    Startinputbox.setAttribute("value", "");
    Startinputbox.setAttribute("class", "input");
    Endinputbox = document.createElement("input");
    Endinputbox.setAttribute("type", "date");
    Endinputbox.setAttribute("size", "4");
    Endinputbox.setAttribute("name", "EndDate");
    Endinputbox.setAttribute("value", "");
    Endinputbox.setAttribute("class", "input");
    Amntinputbox = document.createElement("input");
    Amntinputbox.setAttribute("type", "number");
    Amntinputbox.setAttribute("size", "8");
    Amntinputbox.setAttribute("name", "Amount");
    Amntinputbox.setAttribute("value", "");
    Amntinputbox.setAttribute("max", "99999");
    Amntinputbox.setAttribute("min", "0");
    Amntinputbox.setAttribute("step", "0.001");
    Amntinputbox.setAttribute("class", "input");
    Pcsinputbox = document.createElement("input");
    Pcsinputbox.setAttribute("type", "number");
    Pcsinputbox.setAttribute("size", "8");
    Pcsinputbox.setAttribute("name", "Pieces");
    Pcsinputbox.setAttribute("value", "");
    Pcsinputbox.setAttribute("max", "99999");
    Pcsinputbox.setAttribute("min", "0");
    Pcsinputbox.setAttribute("step", "0.001");
    Pcsinputbox.setAttribute("class", "input");
    Currinputbox = document.createElement("input");
    Currinputbox.setAttribute("type", "text");
    Currinputbox.setAttribute("size", "3");
    Currinputbox.setAttribute("name", "Currency");
    Currinputbox.setAttribute("value", "");
    Currinputbox.setAttribute("class", "input");
    DELbutton = document.createElement("button");
    DELbutton.innerHTML = "Delete";
    DELbutton.setAttribute("type", "button");
    var btn_str1 = "del_line" + e.toString();
    DELbutton.setAttribute("id", btn_str1);
    DELbutton.setAttribute("class", "del_button");
    var btn_str2 = "return delVL(" + e.toString() + ")";
    DELbutton.setAttribute("onclick", btn_str2);
    var x = document.getElementById("VLEditTable").insertRow(e);
    var plan_c = x.insertCell(0);
    var bank_c = x.insertCell(1);
    var acc_c = x.insertCell(2);
    var id_c = x.insertCell(3);
    var start_c = x.insertCell(4);
    var end_c = x.insertCell(5);
    var amnt_c = x.insertCell(6);
    var pcs_c = x.insertCell(7);
    var curr_c = x.insertCell(8);
    var del_c = x.insertCell(9);
    plan_c.appendChild(Planinputbox);
    bank_c.appendChild(Bankinputbox);
    acc_c.appendChild(Accinputbox);
    id_c.appendChild(IDinputbox);
    start_c.appendChild(Startinputbox);
    end_c.appendChild(Endinputbox);
    amnt_c.appendChild(Amntinputbox);
    pcs_c.appendChild(Pcsinputbox);
    curr_c.appendChild(Currinputbox);
    del_c.appendChild(DELbutton);
}

function delVL(e) {
    if (confirm("Delete ?")) {
        var x = document.getElementById("VLEditTable").deleteRow(e);
    } else {
        return false
    }
}

function formatDate(date, format) {
    const map = {
        mm: date.getMonth() + 1,
        dd: date.getDate(),
        yy: date.getFullYear().toString().slice(-2),
        yyyy: date.getFullYear()
    }

    return format.replace(/mm|dd|yy|yyy/gi, matched => map[matched])
}

function addInitA(e) {
    Bankinputbox = document.createElement("input");
    Bankinputbox.setAttribute("type", "text");
    Bankinputbox.setAttribute("size", "6");
    Bankinputbox.setAttribute("name", "Bank");
    Bankinputbox.setAttribute("value", "");
    Bankinputbox.setAttribute("class", "input");
    Accinputbox = document.createElement("input");
    Accinputbox.setAttribute("type", "text");
    Accinputbox.setAttribute("size", "20");
    Accinputbox.setAttribute("name", "AccountNr");
    Accinputbox.setAttribute("value", "");
    Accinputbox.setAttribute("class", "input");
    Dateinputbox = document.createElement("input");
    Dateinputbox.setAttribute("type", "date");
    Dateinputbox.setAttribute("size", "4");
    Dateinputbox.setAttribute("name", "EntryDate");
    Dateinputbox.setAttribute("value", "2020-01-01");
    Dateinputbox.setAttribute("class", "input");
    Refinputbox = document.createElement("input");
    Refinputbox.setAttribute("type", "text");
    Refinputbox.setAttribute("size", "15");
    Refinputbox.setAttribute("name", "Reference");
    Refinputbox.setAttribute("value", "");
    Refinputbox.setAttribute("class", "input");
    Amntinputbox = document.createElement("input");
    Amntinputbox.setAttribute("type", "number");
    Amntinputbox.setAttribute("size", "8");
    Amntinputbox.setAttribute("name", "Amount");
    Amntinputbox.setAttribute("value", "");
    Amntinputbox.setAttribute("max", "99999");
    Amntinputbox.setAttribute("min", "0");
    Amntinputbox.setAttribute("default", "0");
    Amntinputbox.setAttribute("step", "0.001");
    Amntinputbox.setAttribute("class", "input");
    Amntinputbox.defaultValue = "0";
    Currinputbox = document.createElement("input");
    Currinputbox.setAttribute("type", "text");
    Currinputbox.setAttribute("size", "3");
    Currinputbox.setAttribute("name", "Currency");
    Currinputbox.setAttribute("value", "EUR");
    Currinputbox.setAttribute("class", "input");
    DELbutton = document.createElement("button");
    DELbutton.innerHTML = "Delete";
    DELbutton.setAttribute("type", "button");
    var btn_str1 = "del_line" + e.toString();
    DELbutton.setAttribute("id", btn_str1);
    DELbutton.setAttribute("class", "del_button");
    var btn_str2 = "return delInitA(" + e.toString() + ")";
    DELbutton.setAttribute("onclick", btn_str2);
    var x = document.getElementById("InitTable").insertRow(e);
    var bank_c = x.insertCell(0);
    var acc_c = x.insertCell(1);
    var date_c = x.insertCell(2);
    var ref_c = x.insertCell(3);
    var amnt_c = x.insertCell(4);
    var curr_c = x.insertCell(5);
    var del_c = x.insertCell(6);
    bank_c.appendChild(Bankinputbox);
    acc_c.appendChild(Accinputbox);
    date_c.appendChild(Dateinputbox);
    ref_c.appendChild(Refinputbox);
    amnt_c.appendChild(Amntinputbox);
    curr_c.appendChild(Currinputbox);
    del_c.appendChild(DELbutton);
}

function delInitA(e) {
    if (confirm("Delete ?")) {
        var x = document.getElementById("InitTable").deleteRow(e);
    } else {
        return false
    }
}

function addInitD(e) {
    Bankinputbox = document.createElement("input");
    Bankinputbox.setAttribute("type", "text");
    Bankinputbox.setAttribute("size", "6");
    Bankinputbox.setAttribute("name", "Bank");
    Bankinputbox.setAttribute("value", "");
    Bankinputbox.setAttribute("class", "input");
    Accinputbox = document.createElement("input");
    Accinputbox.setAttribute("type", "text");
    Accinputbox.setAttribute("size", "15");
    Accinputbox.setAttribute("name", "DepotNr");
    Accinputbox.setAttribute("value", "");
    Accinputbox.setAttribute("class", "input");
    Assetinputbox = document.createElement("input");
    Assetinputbox.setAttribute("type", "text");
    Assetinputbox.setAttribute("size", "10");
    Assetinputbox.setAttribute("name", "AssetID");
    Assetinputbox.setAttribute("value", "");
    Assetinputbox.setAttribute("class", "input");
    Refinputbox = document.createElement("input");
    Refinputbox.setAttribute("type", "text");
    Refinputbox.setAttribute("size", "15");
    Refinputbox.setAttribute("name", "BankRef");
    Refinputbox.setAttribute("value", "");
    Refinputbox.setAttribute("class", "input");
    Amntinputbox = document.createElement("input");
    Amntinputbox.setAttribute("type", "number");
    Amntinputbox.setAttribute("size", "8");
    Amntinputbox.setAttribute("name", "AssetAmount");
    Amntinputbox.setAttribute("value", "");
    Amntinputbox.setAttribute("max", "99999");
    Amntinputbox.setAttribute("min", "0");
    Amntinputbox.setAttribute("default", "0");
    Amntinputbox.setAttribute("step", "any");
    Amntinputbox.setAttribute("class", "input");
    Amntinputbox.defaultValue = "0";
    Priceinputbox = document.createElement("input");
    Priceinputbox.setAttribute("type", "number");
    Priceinputbox.setAttribute("size", "8");
    Priceinputbox.setAttribute("name", "AssetBuyPrice");
    Priceinputbox.setAttribute("value", "");
    Priceinputbox.setAttribute("max", "99999");
    Priceinputbox.setAttribute("min", "0");
    Priceinputbox.setAttribute("default", "0");
    Priceinputbox.setAttribute("step", "0.01");
    Priceinputbox.setAttribute("class", "input");
    Priceinputbox.defaultValue = "0";
    Currinputbox = document.createElement("input");
    Currinputbox.setAttribute("type", "text");
    Currinputbox.setAttribute("size", "3");
    Currinputbox.setAttribute("name", "Currency");
    Currinputbox.setAttribute("value", "EUR");
    Currinputbox.setAttribute("class", "input");
    DELbutton = document.createElement("button");
    DELbutton.innerHTML = "Delete";
    DELbutton.setAttribute("type", "button");
    var btn_str1 = "del_line" + e.toString();
    DELbutton.setAttribute("id", btn_str1);
    DELbutton.setAttribute("class", "del_button");
    var btn_str2 = "return delInitD(" + e.toString() + ")";
    DELbutton.setAttribute("onclick", btn_str2);
    var x = document.getElementById("InitTable").insertRow(e);
    var bank_c = x.insertCell(0);
    var acc_c = x.insertCell(1);
    var date_c = x.insertCell(2);
    var ref_c = x.insertCell(3);
    var amnt_c = x.insertCell(4);
    var prc_c = x.insertCell(5);
    var curr_c = x.insertCell(6);
    var del_c = x.insertCell(7);
    bank_c.appendChild(Bankinputbox);
    acc_c.appendChild(Accinputbox);
    date_c.appendChild(Assetinputbox);
    ref_c.appendChild(Refinputbox);
    amnt_c.appendChild(Amntinputbox);
    prc_c.appendChild(Priceinputbox);
    curr_c.appendChild(Currinputbox);
    del_c.appendChild(DELbutton);
}

function delInitD(e) {
    if (confirm("Delete ?")) {
        var x = document.getElementById("InitTable").deleteRow(e);
    } else {
        return false
    }
}

function validate(form) {

    return confirm('Do you really want to apply?');
}
