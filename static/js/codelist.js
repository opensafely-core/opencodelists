const addForm = (name, event) => {
    const formIndex = $(`#id_${name}-TOTAL_FORMS`).val();
    const newForm = $(`#${name}-forms .template`).html().replace(/__prefix__/g, formIndex);
    $(`#add-${name}`).before(newForm);

    // Update the number of total forms
    $(`#id_${name}-TOTAL_FORMS`).val(parseInt(formIndex) + 1);

    event.preventDefault();
};

const removeRow = (name, event) => {
    const classes = [...event.target.classList].filter(c => c.startsWith(name));

    if (classes.length < 1) {
        console.log(`no classes beginning with ${name} in remove button class list`);
        return;
    }

    const formId = classes[0];
    const form = document.getElementById(formId);

    // add an <name>-DELETE element to tell the formset we're deleting this
    // form from the formset
    const deleted = document.createElement('input');
    deleted.setAttribute("type", "hidden");
    deleted.setAttribute("name", `${formId}-DELETE`);
    deleted.setAttribute("value", "on");
    form.appendChild(deleted);

    // hide the deleted form
    form.classList.add("d-none");

    event.preventDefault();
}

$(document).ready(() => {
    $('#add-reference').click((event) => addForm('reference', event));
    $('#add-signoff').click((event) => addForm('signoff', event));

    $('.remove-reference').bind('click', (event) => removeRow('reference', event));
    $('.remove-signoff').bind('click', (event) => removeRow('signoff', event));
});
