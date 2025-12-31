function toggleedit(that) {
    $(that).closest('.box')[0].classList.toggle('edit')
}

function togglecollapse(that) {
    $(that).closest('.box')[0].classList.toggle('collapsed')
}

async function send() {
    console.log('send:', json);
    let response = await fetch('/send', {
        method: 'post',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(json)
    });

    let result = await response.json();
    console.log(result);

    if (result.hasOwnProperty("recipes")) {
        json["recipes"] = result["recipes"]
    }
    if (result.hasOwnProperty("baseresource")) {
        json["baseresource"] = result["baseresource"]
    }
    if (result.hasOwnProperty("html")) {
        // replace content with built html
        $('body .content')[0].innerHTML = result["html"];
        init_select2(); //initialize autocompletes
    }
}

function validateitem(box) {
    // console.log('item:', json);
    json["item"] = box.find('.selector select').val();
}

function validaterecipe(box) {
    console.log('recipe:', json);
    let item = box.attr('data-item');
    let value = box.find('.selector select').val();
    if (value == 'baseresource') {
        if (!json.hasOwnProperty("baseresource")) {
            json["baseresource"] = [];
        }
        json["baseresource"].push(item);
    } else {
        if (!json.hasOwnProperty("recipes")) {
            json["recipes"] = {};
        }
        json["recipes"][item] = value;
    }
}

function validate(that) {
    let box = $(that).closest(".box");
    let classes = box[0].classList;

    if (classes.contains("item")) {
        console.log('validating item')
        validateitem(box);
    } else {
        validaterecipe(box);
        console.log('validating recipe')
    }

    send();
}

function init_select2() {
    $('select').select2({
        dropdownAutoWidth : true,
        width: 'auto'
    });
}

var json = {};

$().ready(() => {
    init_select2();
    // console.log('select2');
})