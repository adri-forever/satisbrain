function toggleedit(that) {
	$(that).closest('.box')[0].classList.toggle('edit')
}

function togglecollapse(that) {
	$(that).closest('.box')[0].classList.toggle('collapsed')
}

async function send() {
	// console.log('send:', json);
	let response = await fetch('/send', {
		method: 'post',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify(json)
	});

	let result = await response.json();
	console.log(result);

	if ("html" in result) {
		$('body .content')[0].innerHTML = result["html"];
	}
}

function validateitem(box) {
	// console.log('item:', json);
	json["item"] = box.find('.selector select').val();
}

function validaterecipe(box) {
	console.log('recipe:', json);
	let item = box.attr('data-item');
	json["itemtorecipes"][item] = box.find('.selector select').val();
}

function validate(that) {
	let box = $(that).closest(".box");
	let classes = box[0].classList;

	if ("item" in classes) {
		validateitem(box);
	} else {
		validaterecipe(box);
	}

	send();
}

var json = {};

$().ready(() => {
    $('select').select2({
        dropdownAutoWidth : true,
        width: 'auto'
    });
    // console.log('select2');
})