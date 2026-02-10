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
        json["recipes"] = result["recipes"];
    }
    if (result.hasOwnProperty("baseresource")) {
        json["baseresource"] = result["baseresource"];
    }
    if (result.hasOwnProperty("dictionary")) {
        dictionary = result["dictionary"];
    }
    if (result.hasOwnProperty("html")) {
        // replace content with built html
        $('body .content')[0].innerHTML = result["html"];
        init(); //initialize page modules
    }
}

function validateitem(box) {
    // console.log('item:', json);
    json["item"] = box.find('.selector select').val();
}

function validaterecipe(box) {
    // console.log('recipe:', json);
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

function removebaseresource(that) {
    // console.log('baseresource:', json)
    let item = $(that).closest('.resource').attr('data-item');
    let index = -1;

    if (json.hasOwnProperty("baseresource")) {
        index = json["baseresource"].indexOf(item); // find index of requested item to remove from list
        if (index >= 0) {
            json["baseresource"].splice(index, 1); // remove 1 element at index
        }
    }
}

function validate(that) {
    let box = $(that).closest(".box");
    let classes = box[0].classList;

    if (classes.contains("item")) {
        console.log('validating item')
        validateitem(box);
    } else if (classes.contains("recipe")) {
        validaterecipe(box);
        console.log('validating recipe')
    }  else if (classes.contains("baseresource")) {
        removebaseresource(that);
        console.log('removing base resource')
    } else {
        console.log('Could not validate box with classes ' + Array.from(classes).join(', '))
    }

    send();
}

function get_baseresource_entry(item) {
    entry = $('<div>').addClass('resource').attr('data-item', item.item).append(
        $('<span>').text(item.name)
    ).append(
        $('<button>').addClass('delete').attr('onclick', 'validate(this)')
    )
    return entry
}

function setfactor(force) {
    var _factor = parseFloat($('#quantity').val());

    console.log('_factor', _factor);

    var update = !isNaN(_factor) && factor!=_factor;
    if (update) {
        factor = _factor;
    }
    if (update || force) {
        console.log('factor', factor)

        $('.scalable').each(function() {
            this.innerText = (parseFloat(this.getAttribute('data-value')) * factor).toFixed(DIGITS);
        });
    }
}

function init() {
    // Autocompletes
    $('select').select2({
        dropdownAutoWidth : true,
        width: 'auto'
    });

    // Base resource handler
    if (json['baseresource']) {
        let items = [];
        let itemname;

        // get translation for all items
        for (let i=0; i<json['baseresource'].length; i++) {
            itemname = json['baseresource'][i];
            if (dictionary["items"][json['baseresource'][i]]) {
                itemname = dictionary["items"][json['baseresource'][i]];
            }
            items.push({"item": json['baseresource'][i], "name": itemname});
        }

        // sort alphabetically
        let sorted = items.sort(function(a, b) {return a.name.localeCompare(b.name)})

        // create entries
        for (let i=0; i<sorted.length; i++) {
            $('.box.baseresource .content').append(get_baseresource_entry(sorted[i]));
        }
    }

    // Quantity handler
    $('.box.quantity .content').append(
        $('<label>').attr('for', 'quantity').text('Final item production rate (/min) :')
    ).append(
        $('<input>').attr('id', 'quantity').on('input', setfactor).val(factor)
    );

    setfactor(true);
}

const DIGITS = 3;

var json = {};
var dictionary = {};
var factor = 1;

$().ready(() => {
    init();
})