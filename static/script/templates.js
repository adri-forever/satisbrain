function toggleedit(that) {
	$(that).closest('.box')[0].classList.toggle('edit')
}

function togglecollapse(that) {
	$(that).closest('.box')[0].classList.toggle('collapsed')
}

boxtemplate = `<div class="box">
	<div class="header">
		<div class="left">
			<button class="status"></button><!-- status button -- only appears for item and recipe boxes -->
			<div class="title1"></div> <!-- item, machine, etc -->
			<div class="title2"></div> <!-- recipe -- only appears for recipe boxes -->
			<select class="selector"></select> <!-- item/recipe selection dropdown -->
		</div>
		<div class="right">
			<button class="validate"></button> <!-- only appears in box edit mode -->
			<button class="edit" onclick="toggleedit(this)"></button> <!-- edit/view -- only appears for item and recipe boxes -->
			<button class="collapse" onclick="togglecollapse(this)"></button> <!-- collapse box -->
		</div>
	</div>
	<div class="content">
		<!-- whatever content to be set inside -->
	</div>
	<datalist></datalist> <!-- contains values for input -->
</div>`
