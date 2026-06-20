function toggleEdit(that) {
    $(that).closest('.box')[0].classList.toggle('edit')
}

function toggleCollapse(that, event) {
    let collapsed = $(that).closest('.box').hasClass('collapsed');

    $(that).closest('.box').toggleClass('collapsed', !collapsed);
    if (event.shiftKey) { // if shift is pressed, also toggle child boxes
        $(that).closest('.box').find('.box').toggleClass('collapsed', !collapsed);
    }
}

function toggleAll(that, event) {
    let collapsed = $('.box.tier').hasClass('collapsed');
    let targetselector = '.box.tier';
    if (event.shiftKey) { targetselector += ', .box.tier .box'; }

    $(targetselector).toggleClass('collapsed', !collapsed);
}

function changeStatus(that) {
    let classorder = ['', 'wip', 'done'];
    let classes = that.classList;
    let i = 0;
    if (classes.contains('wip')) { i = 1; }
    if (classes.contains('done')) { i = 2; }

    $(that).removeClass(classorder[i]).addClass(classorder[(i+1)%classorder.length]);
}

function exportPlan() {
    let elmnt = document.createElement('a');
    elmnt.download = 'plan.json';
    elmnt.href = `data:application/json;charset=utf-8,${JSON.stringify(dataobj)}`;
    elmnt.click();
}

function onImport(e) {
    var files = e.target.files;
    if (!files.length) {
        if (DEBUG) {
            console.log('No file selected!');
        }
        return;
    }
    var reader = new FileReader();
    reader.onload = (event) => {
        try {
            imported = JSON.parse(event.target.result);
            if (DEBUG) {
                console.log('Import:');
                console.log(imported);
            }
            send(imported);
        } catch (error) {
            alert(error);
        }
    };
    reader.readAsText(files[0]);
}

function showUpload(that) {
    $('input.import')[0].click();
}

function checkFillKey(fromjson, tojson, key) {
    if (fromjson.hasOwnProperty(key))
        tojson[key] = fromjson[key];
}

async function send(payload) {
    if (DEBUG) {console.log('send:', payload);}

    let response;
    let result;
    try {
        response = await fetch('/send', {
            method: 'post',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        result = await response.json();
    } catch (e) {
        alert("Error :(\nTry resetting the base resource");
        return;
    }
    
    DEBUG = result.DEBUG === 'true';
    if (DEBUG) {console.log(result);}

    checkFillKey(result, dataobj, "nodes");
    checkFillKey(result, dataobj, "recipes");
    checkFillKey(result, dataobj, "baseresource");
    checkFillKey(result, dataobj, "dictionary");
    if (result.hasOwnProperty("target")) {
        let target = {};
        if (result["target"].hasOwnProperty("ingredients"))
            for (let i=0; i<result["target"]["ingredients"].length; i++) {
                target[result["target"]["ingredients"][i]["item"]] = result["target"]["ingredients"][i]["amount"];
            }
        dataobj["target"] = target
    }
    if (result.hasOwnProperty("html")) {
        // replace content with built html
        $('body .content')[0].innerHTML = result["html"];
        init(); //initialize page modules
    }
}

function validateItemLegacy(box) {
    var obj = {};
    var item = box.find('.selector select').val();
    obj[item] = 1;
    dataobj["target"] = obj;
}

function validateItem(box) {
    var target = {};
    box.find('div.item').each(function(index) {
        var item = $(this).find('select').val();
        var amount = parseFloat($(this).find('input.amount').val());

        if (!target.hasOwnProperty(item)) { target[item] = 0; }
        if (amount) { target[item] += amount; }
    });
    dataobj["target"] = target;
}

function validateRecipe(box) {
    let item = box.attr('data-item');
    let value = box.find('.selector select').val();
    if (value == 'baseresource') {
        if (!dataobj.hasOwnProperty("baseresource")) {
            dataobj["baseresource"] = [];
        }
        dataobj["baseresource"].push(item);
    } else {
        if (!dataobj.hasOwnProperty("recipes")) {
            dataobj["recipes"] = {};
        }
        dataobj["recipes"][item] = value;
    }
}

function removeBaseresource(that) {
    let item = $(that).closest('.resource').attr('data-item');
    let index = -1;

    if (dataobj.hasOwnProperty("baseresource")) {
        index = dataobj["baseresource"].indexOf(item); // find index of requested item to remove from list
        if (index >= 0) {
            dataobj["baseresource"].splice(index, 1); // remove 1 element at index
        }
    }
}

function validate(that) {
    let box = $(that).closest(".box");
    let classes = box[0].classList;

    if (classes.contains("item")) {
        if (DEBUG) {console.log('validating item')}
        validateItemLegacy(box);
    } else if (classes.contains("item_multi")) {
        if (DEBUG) {console.log('validating items')}
        validateItem(box);
    } else if (classes.contains("recipe")) {
        if (DEBUG) {console.log('validating recipe')}
        validateRecipe(box);
    }  else if (classes.contains("baseresource")) {
        if (DEBUG) {console.log('removing base resource')}
        removeBaseresource(that);
    } else {
        console.log('Could not validate box with classes ' + Array.from(classes).join(', '))
    }

    send(dataobj);
}

function getBaseresourceEntry(item) {
    entry = $('<div>').addClass('resource').attr('data-item', item.item).append(
        $('<span>').text(item.name)
    ).append(
        $('<button>').addClass('delete smallbutton').attr('onclick', 'validate(this)')
    )
    return entry;
}

function setFactor(force) {
    var _factor = parseFloat($('#quantity').val());

    if (DEBUG) {console.log('_factor', _factor);}

    var update = !isNaN(_factor) && factor!=_factor;
    if (update) { factor = _factor; }
    if (update || force) {
        if (DEBUG) {console.log('factor', factor);}

        $('.scalable').each(function() {
            this.innerText = (parseFloat(this.getAttribute('data-value')) * factor).toFixed(DIGITS);
        });
        // Generated fixed numbers here too for fixed formatting
        $('.fixed').each(function() {
            this.innerText = (parseFloat(this.getAttribute('data-value'))).toFixed(DIGITS);
        });
    }
}

function initSelect2() {
    $('div.selector > select').select2({
        dropdownAutoWidth : true,
        width: 'auto'
    });
}

function removeItem(that) {
    let box = $(that).closest('.box'); // Take closest box before deleting item (caller will cease to exist)
    $(that).closest('div.item').remove();
    validate(box);
}

function inputValidationKey(event) {
    const reg = /^[0-9]+$/;
    let prevent = false;

    if (DEBUG) { console.log("(keypress) Key: "+event.key+"\nCurrent value: "+event.target.value);}

    if (event.key === '.') {
        prevent = event.target.value.includes('.'); // prevent from setting several dots
    } else {
        prevent = !reg.test(event.key);
    }

    if (prevent) { event.preventDefault(); }
}

function inputValidationWhole(event) {
    const regwhole = /^[0-9]*\.?[0-9]*$/;
    const regmatch = /([0-9]*\.?[0-9]*)/;
    let matches;

    if (DEBUG) { console.log("(keyup) Key: "+event.key+"\nCurrent value: "+event.target.value); }

    if (!regwhole.test(event.target.value)) {
        matches = event.target.value.match(regmatch) ?? [];
        $(event.target).val(matches.length > 0 ? matches[0] : "");
    }

    if (event.key === 'Enter') {
        validate(event.target);
    }
}

function addItem(that, item, amount, init) {
    let boxid = crypto.randomUUID();

    $('<div>').addClass('item').attr('id', boxid).append(
        $('<div>').addClass('selector').append(
            $('.box.item_multi .template select').clone().attr('id', crypto.randomUUID())
        )
    ).append(
        $('<input>').addClass('amount').attr('id', crypto.randomUUID()).attr('pattern', '[0-9]+\\.?[0-9]+')//.attr('type', 'number')
    ).append(
        $('<span>').addClass('small').text('/min')
    ).append(
        $('<button>').addClass('delete smallbutton').attr('onclick', 'removeItem(this)')
    ).insertBefore(
        $('.box.item_multi > .content .buttons')
    );

    if (item) {
        $('#'+boxid+' select option[value='+item+']').attr('selected', 'selected');
    }
    if (amount) {
        $('#'+boxid+' input.amount').val(amount);
    }

    $('#'+boxid+' input.amount').on('keypress', inputValidationKey).on('keyup', inputValidationWhole);

    if (init) { initSelect2(); }
}

function initItemInput() {
    let haskey = Object.keys(dataobj).includes("target");
    let hasitem = false; // will stay false if no key
    if (haskey) {
        hasitem = Object.keys(dataobj["target"]).length > 0;
    }
    if (hasitem) {
        for (const [item, amount] of Object.entries(dataobj["target"])) {
            addItem(this, item, amount, false);
        }
    } else {
        addItem(this, null, null, false);
    }
}   

function resetBaseResource() {
    delete dataobj["baseresource"];
    send(dataobj);
}

function initBaseResource() {
    if (dataobj['baseresource']) {
        let items = []; 
        let itemname;
        let itemdesc;

        // get translation for all items
        for (let i=0; i<dataobj['baseresource'].length; i++) {
            itemname = dataobj['baseresource'][i];
            
            if (Object.keys(dataobj["nodes"]).includes(itemname)) { // only create handler button if item is present in plan
                itemdesc = dataobj["dictionary"]["items"][dataobj['baseresource'][i]];
                if (!itemdesc) { itemdesc = itemname; } // if we do not find translation, show raw item name 
                
                items.push({"item": dataobj['baseresource'][i], "name": itemdesc});
            }
        }

        // sort alphabetically
        let sorted = items.sort(function(a, b) {return a.name.localeCompare(b.name)})

        // create entries
        for (let i=0; i<sorted.length; i++) {
            $('.box.baseresource .content').append(getBaseresourceEntry(sorted[i]));
        }
    }
}

function init() {
    // Item inputs
    initItemInput();

    // Autocompletes
    initSelect2(); 

    // Base resource handler
    initBaseResource();

    setFactor(true); // to delete next ?
}

const DIGITS = 3;
var DEBUG = false;

var imported = {};
var dataobj = {};
var factor = 1;

$().ready(() => {
    init();
})