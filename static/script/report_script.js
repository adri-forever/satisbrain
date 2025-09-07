/* Collapsibles */
var expnd = document.getElementsByClassName("expndall")[0];
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display === "block") {
            content.style.display = "none";
        }
        else {
            content.style.display = "block";
        }
    });
}

expnd.addEventListener("click", function() {
    var state = false;
    var style = "block";
    for (i = 0; i < coll.length; i++) {
            state = state || (coll[i].nextElementSibling.style.display==="block");
    }

    if (state) {
            style = "none";
    }

    for (i = 0; i < coll.length; i++) {
            coll[i].nextElementSibling.style.display=style;
    coll[i].classList.toggle("active", !state)
    }
});

/* LocalStorage checkboxes*/
document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');

    // Initialize the checkboxes based on localStorage
    checkboxes.forEach(function(checkbox) {
        const boxId = checkbox.id;
        const isChecked = localStorage.getItem(boxId) === 'true';

        checkbox.checked = isChecked;
    });

    // Add event listeners to each checkbox
    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const isChecked = checkbox.checked;
            const boxId = checkbox.id;

            localStorage.setItem(boxId, isChecked);
        });
    });
});