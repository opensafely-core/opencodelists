/* v8 ignore start */
const addForm = (name, event) => {
  const formIndex = $(`#id_${name}-TOTAL_FORMS`).val();
  const newForm = $(`#${name}-forms .template`)
    .html()
    .replace(/__prefix__/g, formIndex);
  $(`#add-${name}`).before(newForm);

  // Update the number of total forms
  $(`#id_${name}-TOTAL_FORMS`).val(parseInt(formIndex, 10) + 1);

  event.preventDefault();
};

const removeRow = (name, event) => {
  const classes = [...event.target.classList].filter((c) => c.startsWith(name));

  if (classes.length < 1) {
    // biome-ignore lint/suspicious/noConsole: legacy console implementation
    console.log(
      `no classes beginning with ${name} in remove button class list`,
    );
    return;
  }

  const formId = classes[0];
  const form = document.getElementById(formId);

  // flip the <name>-DELETE checkbox to tell the formset we're deleting this
  // form from the formset
  const deleted = document.getElementById(`${formId}-DELETE`);
  deleted.setAttribute("value", "on");

  // hide the deleted form
  form.classList.add("d-none");

  event.preventDefault();
};

$(document).ready(() => {
  $("#add-reference").click((event) => addForm("reference", event));
  $("#add-signoff").click((event) => addForm("signoff", event));

  $(document).on("click", ".remove-reference", (event) =>
    removeRow("reference", event),
  );
  $(document).on("click", ".remove-signoff", (event) =>
    removeRow("signoff", event),
  );
});
/* v8 ignore end */
