$(document).ready(() => {
	let boxvalue = "fusedframe";
	let boxdesc = "Fused Frame";
	let boxcontent = "The fused frame is a high end part to build the most complex and precise structures."
	let boxid = 1;
	let inputid = 2;
	let options = {"nuclearpasta": "Nuclear Pasta", fusedframe: "Fused Frame"};

	//Itembox example
	let itembox = $(boxtemplate).attr('id', boxid).addClass('item');
	itembox.find('.title1').text(boxdesc);
	itembox.find('.content').append($('<span>').html(boxcontent))
	let select = itembox.find('select').attr('id', inputid)
	for (let [key, value] of Object.entries(options)) {
		select.append($('<option>').attr('value', key).text(value));
	}
	select.find(`option[value="${boxvalue}"]`).attr("selected", "selected");

	$('.content').append(itembox);
});