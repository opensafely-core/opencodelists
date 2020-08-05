const addForm = (name, event) => {
    const form_idx = $(`#id_${name}-TOTAL_FORMS`).val();
    const new_form = $(`#${name}-forms .template`).html().replace(/__prefix__/g, form_idx);
    $(`#${name}-forms`).append('<hr />').append(new_form);

    // Update the number of total forms
    $(`#id_${name}-TOTAL_FORMS`).val(parseInt(form_idx) + 1);

    event.preventDefault();
};

$(document).ready(() => {
    $('#add-reference').click((event) => addForm('reference', event));
    $('#add-signoff').click((event) => addForm('signoff', event));
});
